"""Vendor → RestoPulse canonical CSV schema adapter.

This is the *only* file that knows the vendor scraper's output shape. If the
vendor changes their CSV columns, only this file changes. If we swap the
scraper entirely (e.g. for the Instant Data Scraper Chrome extension), only
this file changes. The NLP pipeline never sees vendor-specific quirks.

Vendor (georgekhananaev/google-reviews-scraper-pro v1.2.3) review record:
    review_id, place_id, author, rating, description (JSON dict {lang: text}),
    review_date (ISO 8601 + TZ), company, source, ...

Our canonical CSV columns (consumed by scripts/ingest.py):
    external_id, restaurant_name, restaurant_external_id, author, rating,
    original_text, translated_text, date_added, source
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

CANONICAL_HEADERS = [
    "external_id",
    "restaurant_name",
    "restaurant_external_id",
    "author",
    "rating",
    "original_text",
    "translated_text",
    "date_added",
    "source",
]

# Languages we explicitly prefer as "original" when present in description dict.
# Order matters: first match wins.
PREFERRED_ORIGINAL_LANGS = ["tl", "fil", "ceb", "ilo", "war", "hil"]


def _parse_description(raw: str) -> tuple[str, str | None]:
    """Decode the vendor's `description` field into (original, translated).

    The vendor stores description as a JSON dict keyed by language code, e.g.:
        {"en": "Great food", "tl": "Masarap"}

    Strategy:
      1. If a preferred non-English language key is present, use it as original
         and use 'en' (if present) as translated.
      2. Else if only 'en' is present, treat it as original with no translation
         (we can't tell whether the source was English or auto-translated).
      3. Else pick the first key alphabetically as original.
    """
    if raw is None or raw == "":
        return "", None

    # Vendor may emit either JSON or already a plain string — try JSON first.
    try:
        desc = json.loads(raw) if raw.lstrip().startswith("{") else None
    except (json.JSONDecodeError, ValueError):
        desc = None

    if desc is None or not isinstance(desc, dict):
        # Treat as plain string
        return str(raw).strip(), None

    if not desc:
        return "", None

    # 1) Preferred original language
    for lang in PREFERRED_ORIGINAL_LANGS:
        if lang in desc and desc[lang]:
            translated = desc.get("en") if lang != "en" else None
            return str(desc[lang]).strip(), (str(translated).strip() if translated else None)

    # 2) Only English
    if "en" in desc and desc["en"]:
        return str(desc["en"]).strip(), None

    # 3) Fall back to first available key
    first_key = sorted(desc.keys())[0]
    return str(desc[first_key]).strip(), None


def _coerce_rating(raw: Any) -> int | None:
    """Vendor rating is float 1-5; we store int 1-5."""
    if raw is None or raw == "":
        return None
    try:
        return int(round(float(raw)))
    except (TypeError, ValueError):
        return None


def _coerce_date(raw: Any) -> str | None:
    """Vendor date is ISO 8601 with TZ; we keep just YYYY-MM-DD."""
    if not raw:
        return None
    s = str(raw)
    # ISO 8601 dates always start with YYYY-MM-DD — slice first 10 chars
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return None


def normalize_csv(input_csv: Path, output_csv: Path) -> int:
    """Read vendor CSV, write canonical CSV. Returns number of rows written.

    Deduplicates on external_id (vendor's review_id). Skips rows with empty
    text or missing rating.
    """
    input_csv  = Path(input_csv)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not input_csv.is_file():
        raise FileNotFoundError(f"vendor CSV not found: {input_csv}")

    by_id: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    skipped = 0

    with input_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            external_id = (row.get("review_id") or "").strip()
            if not external_id:
                skipped += 1
                continue

            original_text, translated_text = _parse_description(row.get("description", ""))
            if not original_text:
                skipped += 1
                continue

            rating = _coerce_rating(row.get("rating"))
            if rating is None:
                skipped += 1
                continue

            date_added = _coerce_date(row.get("review_date"))
            if not date_added:
                skipped += 1
                continue

            by_id[external_id] = {
                "external_id":            external_id,
                "restaurant_name":        (row.get("company") or "").strip() or "Unknown",
                "restaurant_external_id": (row.get("place_id") or "").strip(),
                "author":                 (row.get("author") or "").strip(),
                "rating":                 rating,
                "original_text":          original_text,
                "translated_text":        translated_text or "",
                "date_added":             date_added,
                "source":                 (row.get("source") or "Google Maps").strip(),
            }

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_HEADERS)
        writer.writeheader()
        writer.writerows(by_id.values())

    n = len(by_id)
    print(f"[adapter] normalized {n} rows ({skipped} skipped) → {output_csv}")
    return n


def normalize_sqlite(db_path: Path, output_csv: Path) -> int:
    """Read the vendor's scrape.db directly, write canonical CSV.

    Preferred over normalize_csv(): the vendor's CSV export breaks on Windows
    because place_ids contain a colon (e.g. "0x3255...:0"), which NTFS treats as
    an alternate-data-stream separator. Reading SQLite sidesteps that entirely.

    Joins `reviews` with `places` for the restaurant name. Deduplicates on
    review_id; skips rows with empty text or missing rating.
    """
    db_path    = Path(db_path)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.is_file():
        raise FileNotFoundError(f"vendor scrape.db not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT r.review_id, r.place_id, r.author, r.rating,
                   r.review_text, r.review_date,
                   p.place_name
            FROM reviews r
            LEFT JOIN places p ON p.place_id = r.place_id
            WHERE r.is_deleted = 0
            ORDER BY r.review_date DESC
            """
        ).fetchall()
    finally:
        conn.close()

    by_id: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    skipped = 0

    for row in rows:
        external_id = (row["review_id"] or "").strip()
        if not external_id:
            skipped += 1
            continue

        # review_text is a JSON dict {lang: text}; reuse the description parser.
        original_text, translated_text = _parse_description(row["review_text"] or "")
        if not original_text:
            skipped += 1
            continue

        rating = _coerce_rating(row["rating"])
        if rating is None:
            skipped += 1
            continue

        date_added = _coerce_date(row["review_date"])

        by_id[external_id] = {
            "external_id":            external_id,
            "restaurant_name":        (row["place_name"] or "").strip() or "Unknown",
            "restaurant_external_id": (row["place_id"] or "").strip(),
            "author":                 (row["author"] or "").strip(),
            "rating":                 rating,
            "original_text":          original_text,
            "translated_text":        translated_text or "",
            "date_added":             date_added or "",
            "source":                 "Google Maps",
        }

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_HEADERS)
        writer.writeheader()
        writer.writerows(by_id.values())

    n = len(by_id)
    print(f"[adapter] normalized {n} rows from sqlite ({skipped} skipped) → {output_csv}")
    return n


# ---------------------------------------------------------------------------
# CLI for testing the adapter in isolation
# ---------------------------------------------------------------------------
def _main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Test the vendor→canonical CSV adapter")
    p.add_argument("--in",  dest="inp", required=True, type=Path, help="vendor CSV input")
    p.add_argument("--out", required=True, type=Path, help="canonical CSV output")
    args = p.parse_args()
    normalize_csv(args.inp, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
