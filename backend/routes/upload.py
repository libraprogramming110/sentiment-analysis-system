"""CSV upload endpoint — lets a user add reviews on top of the existing dataset.

Mirrors the per-row flow of scripts/ingest.py but runs inside a web request:
each row goes through the hybrid pipeline (LLM ABSA + VADER + rule aspects),
corpus-level TF-IDF runs over the uploaded batch, and everything is written via
the same repo helpers the scraper ingest uses. Uploaded reviews become first-class
data — the new restaurant shows up across the whole dashboard.

Constraints:
  - Max MAX_UPLOAD_ROWS rows per upload (each row is a real LLM call; this protects
    demo latency and the Groq free-tier rate limit).
  - Requires GROQ_API_KEY (process_review raises RuntimeError without it → 502).
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime

from flask import Blueprint, jsonify, request

from db.repo import insert_review, review_text_exists, upsert_restaurant
from nlp import keywords as kw_mod
from nlp.pipeline import process_review

bp = Blueprint("upload", __name__)

MAX_UPLOAD_ROWS = 30

# Accepted aliases for each logical field (lower-cased CSV header → value).
_TEXT_KEYS = ("review_text", "original_text", "text", "review")
_RESTAURANT_KEYS = ("restaurant_name", "restaurant")
_DATE_KEYS = ("date", "date_added")


def _pick(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for k in keys:
        v = row.get(k)
        if v and v.strip():
            return v.strip()
    return ""


def _int(v: str) -> int | None:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


# Date formats we accept in uploads → all normalized to ISO YYYY-MM-DD so SQLite's
# date functions (used by the trend chart) can parse them. Excel commonly rewrites
# ISO dates into M/D/YYYY, so we accept those too.
_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y")


def _normalize_date(s: str) -> str | None:
    """Parse a date string in a few common formats → ISO 'YYYY-MM-DD'.
    Returns None if it can't be parsed (caller falls back to today)."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


@bp.post("/upload")
def upload():
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "No file uploaded (expected form field 'file')."}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "File must be a .csv"}), 400

    dataset_name = (request.form.get("dataset_name") or "").strip() or "Uploaded Reviews"

    # Parse CSV (utf-8, tolerate a BOM). Normalize headers to lower-case.
    try:
        raw = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({"error": "Could not read file as UTF-8 text."}), 400

    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        return jsonify({"error": "CSV is empty or has no header row."}), 400

    rows = [{(k or "").strip().lower(): v for k, v in r.items()} for r in reader]
    if not rows:
        return jsonify({"error": "CSV has a header but no data rows."}), 400
    if len(rows) > MAX_UPLOAD_ROWS:
        return jsonify({
            "error": f"Too many rows ({len(rows)}). Max {MAX_UPLOAD_ROWS} reviews per upload — "
                     "each review is analyzed by the LLM, so larger files time out."
        }), 400

    today = date.today().isoformat()
    processed: list[dict] = []
    texts: list[str] = []
    seen: set[tuple[int, str]] = set()  # (restaurant_id, text) already handled this batch
    skipped = 0
    failed = 0
    errors: list[str] = []
    any_text_rows = False  # did any row have usable review text at all?

    # ---- Pass 1: pipeline per row, collect texts for TF-IDF ----
    for i, row in enumerate(rows, 1):
        text = _pick(row, _TEXT_KEYS)
        if not text:
            skipped += 1
            continue
        any_text_rows = True

        # Resolve the restaurant first (cheap) so we can dedup BEFORE the costly LLM call.
        rest_name = _pick(row, _RESTAURANT_KEYS) or dataset_name
        rest_city = _pick(row, ("city",)) or None
        rest_id = upsert_restaurant(name=rest_name, external_id=None, city=rest_city, source_url=None)

        # Idempotency: skip exact re-adds (same restaurant + same review text), whether
        # the duplicate is already in the DB or earlier in this same file.
        key = (rest_id, text)
        if key in seen or review_text_exists(rest_id, text):
            skipped += 1
            continue
        seen.add(key)

        try:
            result = process_review(text)
        except RuntimeError as e:
            # Missing key / LLM unparseable — abort the whole upload with a clear status.
            return jsonify({"error": str(e)}), 502
        except Exception as e:  # one bad row shouldn't kill the batch
            failed += 1
            if len(errors) < 5:
                errors.append(f"Row {i}: {e}")
            continue

        processed.append({
            "row": row,
            "result": result,
            "restaurant_id": rest_id,
            "text_index": len(texts),
        })
        texts.append(text)

    if not processed:
        # No genuine review text anywhere → real user error (400).
        if not any_text_rows:
            return jsonify({
                "error": "No valid reviews found. Ensure a 'review_text' column with non-empty text.",
                "skipped": skipped,
                "failed": failed,
                "errors": errors,
            }), 400
        # There WERE text rows, but all were duplicates (or failed) → success, nothing new.
        from db.repo import get_db
        new_total = get_db().execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        return jsonify({
            "inserted": 0,
            "skipped": skipped,
            "failed": failed,
            "restaurants_created": 0,
            "new_total": new_total,
            "errors": errors,
        })

    # ---- Pass 2: corpus TF-IDF over the uploaded batch, then write ----
    tfidf = kw_mod.extract_corpus_keywords(texts, top_n_per_doc=6) if texts else []
    restaurants_seen: set[int] = set()
    inserted = 0

    for item in processed:
        row, result = item["row"], item["result"]
        ti = item["text_index"]
        tfidf_kw = tfidf[ti] if ti < len(tfidf) else []
        merged_kw: list[dict] = [{"keyword": k, "frequency": 1} for k in result["keywords"]]
        merged_kw.extend(tfidf_kw)

        insert_review({
            "restaurant_id":     item["restaurant_id"],
            "external_id":       None,
            "author":            _pick(row, ("author",)) or None,
            "original_text":     result["original_text"],
            "translated_text":   result.get("translated_text"),
            "detected_language": result["detected_language"],
            "rating":            _int(_pick(row, ("rating",))),
            "overall_sentiment": result["overall_sentiment"],
            "overall_score":     result["overall_score"],
            "vader_sentiment":   result.get("vader_sentiment"),
            "vader_score":       result.get("vader_score"),
            "llm_raw_response":  result["llm_raw_response"],
            "date_added":        _normalize_date(_pick(row, _DATE_KEYS)) or today,
            "source":            _pick(row, ("source",)) or "Manual Upload",
            "aspects":           result["aspects"],
            "keywords":          merged_kw,
        })
        inserted += 1
        restaurants_seen.add(item["restaurant_id"])

    from db.repo import get_db
    new_total = get_db().execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]

    return jsonify({
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
        "restaurants_created": len(restaurants_seen),
        "new_total": new_total,
        "errors": errors,
    })
