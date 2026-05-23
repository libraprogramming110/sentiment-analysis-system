"""Ingest: canonical CSV → hybrid NLP pipeline → SQLite.

Reads data/reviews_raw.csv (produced by the scraper), runs each review through
the hybrid pipeline (LLM ABSA + VADER baseline + rule aspects), merges in
corpus-level TF-IDF keywords, and writes everything into the app DB.

Features:
  - Resumable: skips reviews whose external_id is already in the DB.
  - Throttled: nlp/llm.py paces requests for the Groq free tier.
  - Progress: prints a running counter so long batches are observable.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\ingest.py
    .venv\\Scripts\\python.exe scripts\\ingest.py --limit 20   # test on first 20
    .venv\\Scripts\\python.exe scripts\\ingest.py --reset      # wipe DB first
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from db.repo import (  # noqa: E402
    get_db, init_db, insert_review, review_exists, upsert_restaurant,
)
from nlp import keywords as kw_mod  # noqa: E402
from nlp.pipeline import process_review  # noqa: E402

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "reviews_raw.csv"


def _reset_db() -> None:
    db = get_db()
    db.executescript(
        "DELETE FROM keywords; DELETE FROM aspect_sentiments; "
        "DELETE FROM reviews; DELETE FROM restaurants;"
    )
    db.commit()
    print("[ingest] DB wiped.")


def run(csv_path: Path, limit: int | None, reset: bool) -> None:
    init_db()
    app = Flask(__name__)
    with app.app_context():
        if reset:
            _reset_db()

        if not csv_path.is_file():
            raise SystemExit(f"[ingest] CSV not found: {csv_path}\nRun the scraper first.")

        with csv_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if limit:
            rows = rows[:limit]

        print(f"[ingest] {len(rows)} reviews in CSV. Analyzing with hybrid pipeline…")

        # First pass: LLM ABSA + VADER per review, collect texts for TF-IDF.
        processed: list[dict] = []
        texts: list[str] = []
        skipped = done = 0

        for i, row in enumerate(rows, 1):
            ext_id = (row.get("external_id") or "").strip()
            if ext_id and review_exists(ext_id):
                skipped += 1
                continue

            text = (row.get("original_text") or "").strip()
            if not text:
                skipped += 1
                continue

            try:
                result = process_review(text)
            except Exception as e:  # one bad review shouldn't kill the batch
                print(f"[ingest]   ! review {i} failed: {e}")
                skipped += 1
                continue

            rest_id = upsert_restaurant(
                name=(row.get("restaurant_name") or "Unknown").strip(),
                external_id=(row.get("restaurant_external_id") or "").strip() or None,
                city=(row.get("city") or "").strip() or None,
                source_url=None,
            )

            processed.append({
                "row": row, "result": result, "restaurant_id": rest_id, "ext_id": ext_id,
                "text_index": len(texts),
            })
            texts.append(text)
            done += 1
            if done % 10 == 0:
                print(f"[ingest]   analyzed {done} reviews…")

        # Second pass: corpus-level TF-IDF keywords (component [5]).
        print(f"[ingest] computing TF-IDF keywords over {len(texts)} reviews…")
        tfidf = kw_mod.extract_corpus_keywords(texts, top_n_per_doc=6) if texts else []

        # Write to DB.
        for item in processed:
            row, result = item["row"], item["result"]
            ti = item["text_index"]
            tfidf_kw = tfidf[ti] if ti < len(tfidf) else []
            # Merge LLM keywords (frequency-style) + TF-IDF keywords (scored).
            merged_kw: list[dict] = [{"keyword": k, "frequency": 1} for k in result["keywords"]]
            merged_kw.extend(tfidf_kw)

            insert_review({
                "restaurant_id":     item["restaurant_id"],
                "external_id":       item["ext_id"] or None,
                "author":            (row.get("author") or "").strip(),
                "original_text":     result["original_text"],
                "translated_text":   (row.get("translated_text") or "").strip() or None,
                "detected_language": result["detected_language"],
                "rating":            _int(row.get("rating")),
                "overall_sentiment": result["overall_sentiment"],
                "overall_score":     result["overall_score"],
                "vader_sentiment":   result.get("vader_sentiment"),
                "vader_score":       result.get("vader_score"),
                "llm_raw_response":  result["llm_raw_response"],
                "date_added":        (row.get("date_added") or "").strip() or None,
                "source":            (row.get("source") or "Google Maps").strip(),
                "aspects":           result["aspects"],
                "keywords":          merged_kw,
            })

        total = get_db().execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        print(f"\n[ingest] done. inserted {done}, skipped {skipped}. DB now has {total} reviews.")


def _int(v) -> int | None:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def main() -> int:
    p = argparse.ArgumentParser(description="Ingest reviews CSV through the hybrid NLP pipeline")
    p.add_argument("--csv", type=Path, default=CSV_PATH)
    p.add_argument("--limit", type=int, default=None, help="only process first N reviews")
    p.add_argument("--reset", action="store_true", help="wipe DB before ingesting")
    args = p.parse_args()
    run(args.csv, args.limit, args.reset)
    return 0


if __name__ == "__main__":
    sys.exit(main())
