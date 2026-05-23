"""RestoPulse Google Maps reviews scraper wrapper.

Drives the vendored CLI tool (`georgekhananaev/google-reviews-scraper-pro`,
pinned to v1.2.3) inside its own isolated venv via subprocess, then hands the
exported CSV to `adapter.normalize_csv()` for schema mapping. Output is the
canonical `data/reviews_raw.csv` that downstream NLP ingest reads.

Usage:
    cd backend
    .venv\\Scripts\\activate
    python -m scraper.google_scraper --config scraper/config.yaml \\
                                     --out data/reviews_raw.csv
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from scraper import adapter

# ---------------------------------------------------------------------------
# Paths (resolved relative to this file so the wrapper works from any cwd)
# ---------------------------------------------------------------------------
SCRAPER_DIR = Path(__file__).resolve().parent
VENDOR_DIR  = SCRAPER_DIR / "vendor" / "google-reviews-scraper-pro"
VENV_PY     = SCRAPER_DIR / ".venv-scraper" / "Scripts" / "python.exe"
# The scraper writes its SQLite into the vendor folder; we then export from there.
VENDOR_DB   = VENDOR_DIR / "scrape.db"

# Candidate Chromium-family browser binaries, in preference order. The vendored
# scraper passes `binary_location=$CHROME_BIN` to SeleniumBase when CHROME_BIN
# is set, so any Chromium build (Brave, Chrome, Edge) works without code edits.
BROWSER_CANDIDATES = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def _find_browser() -> str | None:
    """Return the first available Chromium-family browser binary, or None.

    Honors an explicit override via the RP_BROWSER_BIN env var.
    """
    override = os.environ.get("RP_BROWSER_BIN")
    if override and Path(override).is_file():
        return override
    for cand in BROWSER_CANDIDATES:
        if cand and Path(cand).is_file():
            return cand
    return None


def _build_url_city_map(config_path: Path) -> dict[str, str]:
    """Parse config.yaml's businesses → {url: city} so the adapter can tag
    each scraped place with the city we assigned it."""
    import yaml  # local import; only needed here

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        print(f"[scraper] warning: could not parse {config_path} for city map: {e}")
        return {}

    mapping: dict[str, str] = {}
    for biz in data.get("businesses", []):
        url = (biz.get("url") or "").strip()
        city = (biz.get("custom_params", {}) or {}).get("city", "")
        if url and city:
            mapping[url] = city
    return mapping


def _check_prereqs() -> None:
    """Fail fast with a clear message if vendor folder or venv is missing."""
    missing = []
    if not VENDOR_DIR.is_dir():
        missing.append(f"vendor folder: {VENDOR_DIR}")
    if not VENV_PY.is_file():
        missing.append(f"isolated venv python: {VENV_PY}")
    if missing:
        msg = "Scraper prerequisites missing:\n  - " + "\n  - ".join(missing)
        msg += "\nRun the S2/S3 setup steps in scraper/VENDOR.md."
        raise SystemExit(msg)


def _run_subprocess(args: list[str], step: str, env: dict[str, str] | None = None) -> None:
    """Run a vendor CLI invocation, streaming output, raising on non-zero exit."""
    print(f"\n[scraper] {step}: {' '.join(str(a) for a in args)}")
    result = subprocess.run(args, cwd=VENDOR_DIR, env=env)
    if result.returncode != 0:
        raise SystemExit(f"[scraper] {step} failed with exit code {result.returncode}")


def scrape(config_path: Path, output_csv: Path) -> int:
    """Run a full scrape + export + normalize cycle.

    Args:
        config_path: path to our scraper/config.yaml (absolute or cwd-relative)
        output_csv:  where to write the canonical CSV

    Returns:
        number of rows written to ``output_csv``
    """
    _check_prereqs()

    config_path = Path(config_path).resolve()
    output_csv  = Path(output_csv).resolve()
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.is_file():
        raise SystemExit(f"[scraper] config file not found: {config_path}")

    # Locate a Chromium-family browser and hand it to the vendor via CHROME_BIN.
    browser = _find_browser()
    if not browser:
        raise SystemExit(
            "[scraper] No Chromium-family browser found.\n"
            "Install Brave, Chrome, or Edge — or set RP_BROWSER_BIN to the .exe path.\n"
            f"Looked in:\n  - " + "\n  - ".join(BROWSER_CANDIDATES)
        )
    print(f"[scraper] using browser binary: {browser}")
    # PYTHONIOENCODING=utf-8 stops the vendor's braille progress spinner from
    # crashing on Windows' default cp1252 console (UnicodeEncodeError on ⠏).
    child_env = {**os.environ, "CHROME_BIN": browser, "PYTHONIOENCODING": "utf-8"}

    # ---- Step A: scrape into the vendor's SQLite -----------------------------
    _run_subprocess(
        [
            str(VENV_PY),
            "start.py",
            "--config", str(config_path),
            "-q",                        # headless
        ],
        step="scrape",
        env=child_env,
    )

    # ---- Step B: normalize directly from the vendor's SQLite -----------------
    # We deliberately skip the vendor's CSV export CLI: it names files
    # `reviews_{place_id}.csv`, and place_ids contain a colon (e.g. "0x..:0")
    # which NTFS treats as an alternate-data-stream separator, producing a
    # 0-byte file. Reading scrape.db directly avoids the whole class of bug.
    if not VENDOR_DB.is_file():
        raise SystemExit(
            f"[scraper] vendor DB not found at {VENDOR_DB} — "
            "the scrape likely failed (check the log above)."
        )
    url_city_map = _build_url_city_map(config_path)
    rows = adapter.normalize_sqlite(VENDOR_DB, output_csv, url_city_map=url_city_map)
    print(f"\n[scraper] wrote {rows} rows to {output_csv}")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RestoPulse Google Reviews scraper")
    parser.add_argument(
        "--config",
        type=Path,
        default=SCRAPER_DIR / "config.yaml",
        help="path to scraper/config.yaml (default: scraper/config.yaml)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=SCRAPER_DIR.parent / "data" / "reviews_raw.csv",
        help="path to write canonical CSV (default: data/reviews_raw.csv)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="delete vendor SQLite before scraping (fresh run)",
    )
    args = parser.parse_args(argv)

    if args.clean and VENDOR_DB.exists():
        print(f"[scraper] --clean: removing {VENDOR_DB}")
        VENDOR_DB.unlink()

    try:
        scrape(args.config, args.out)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
