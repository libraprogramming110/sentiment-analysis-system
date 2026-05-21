"""SQLite repository for RestoPulse.

One connection per request (Flask `g`), schema initialized on first launch,
and small helpers for the read paths the dashboard needs.
"""
from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from flask import g

DB_PATH = Path(__file__).resolve().parent.parent / "restopulse.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------
def get_db() -> sqlite3.Connection:
    """Get or create the request-scoped DB connection."""
    if "db" not in g:
        # No PARSE_DECLTYPES: keep dates as plain ISO strings so JSON output is
        # stable ("2026-05-16") instead of being auto-cast to Python date and
        # then RFC-formatted by Flask's jsonify.
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Apply schema. Idempotent."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def init_app(app) -> None:
    """Register teardown + ensure schema exists before first request."""
    init_db()
    app.teardown_appcontext(close_db)


# ---------------------------------------------------------------------------
# Read helpers (dashboard / analytics)
# ---------------------------------------------------------------------------
def fetch_summary() -> dict[str, Any]:
    db = get_db()
    row = db.execute(
        """
        SELECT
          COUNT(*)                                                       AS total,
          SUM(CASE WHEN overall_sentiment='positive' THEN 1 ELSE 0 END)  AS positive,
          SUM(CASE WHEN overall_sentiment='neutral'  THEN 1 ELSE 0 END)  AS neutral,
          SUM(CASE WHEN overall_sentiment='negative' THEN 1 ELSE 0 END)  AS negative,
          COALESCE(ROUND(AVG(rating), 2), 0)                             AS avg_rating
        FROM reviews
        """
    ).fetchone()
    total = row["total"] or 0
    return {
        "total":          total,
        "positive":       row["positive"] or 0,
        "neutral":        row["neutral"]  or 0,
        "negative":       row["negative"] or 0,
        "avgRating":      row["avg_rating"],
        # Deltas need a previous period to compare against — placeholder for now.
        "positiveDelta":  0.0,
        "negativeDelta":  0.0,
    }


def fetch_trend(days: int = 30) -> list[dict[str, Any]]:
    """Sentiment volume per day for the last `days` days."""
    db = get_db()
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    rows = db.execute(
        """
        SELECT date_added                                                  AS day,
               SUM(CASE WHEN overall_sentiment='positive' THEN 1 ELSE 0 END) AS positive,
               SUM(CASE WHEN overall_sentiment='neutral'  THEN 1 ELSE 0 END) AS neutral,
               SUM(CASE WHEN overall_sentiment='negative' THEN 1 ELSE 0 END) AS negative
        FROM reviews
        WHERE date_added >= ?
        GROUP BY date_added
        ORDER BY date_added
        """,
        (cutoff,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_aspects() -> list[dict[str, Any]]:
    """Aspect-level sentiment breakdown."""
    db = get_db()
    rows = db.execute(
        """
        SELECT aspect,
               SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END) AS positive,
               SUM(CASE WHEN sentiment='neutral'  THEN 1 ELSE 0 END) AS neutral,
               SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) AS negative
        FROM aspect_sentiments
        GROUP BY aspect
        ORDER BY aspect
        """
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_top_issues(limit: int = 3) -> list[dict[str, Any]]:
    """Aspects with the most negative mentions — feeds 'Top 3 Issues Detected'."""
    db = get_db()
    rows = db.execute(
        """
        SELECT aspect, COUNT(*) AS mentions
        FROM aspect_sentiments
        WHERE sentiment='negative'
        GROUP BY aspect
        ORDER BY mentions DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    pretty = {
        "service":     "Slow service / staff issues",
        "price":       "Pricing perceived as too high",
        "cleanliness": "Cleanliness complaints",
        "food":        "Food quality complaints",
        "ambiance":    "Ambiance / atmosphere issues",
    }
    return [
        {"issue": pretty.get(r["aspect"], r["aspect"]),
         "mentions": r["mentions"],
         "aspect": r["aspect"]}
        for r in rows
    ]


def fetch_languages() -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT detected_language AS lang, COUNT(*) AS count
        FROM reviews
        WHERE detected_language IS NOT NULL
        GROUP BY detected_language
        ORDER BY count DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_top_keywords(limit: int = 20) -> list[dict[str, Any]]:
    """Aggregate keyword frequencies across the corpus and tag dominant sentiment."""
    db = get_db()
    rows = db.execute(
        """
        SELECT k.keyword, SUM(k.frequency) AS count, r.overall_sentiment AS sentiment
        FROM keywords k
        JOIN reviews r ON r.review_id = k.review_id
        GROUP BY k.keyword
        ORDER BY count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    # Pick the dominant sentiment per keyword (simple majority)
    by_word: dict[str, dict[str, Any]] = {}
    sentiment_votes: defaultdict[str, Counter] = defaultdict(Counter)
    for r in rows:
        w = r["keyword"]
        if r["sentiment"]:
            sentiment_votes[w][r["sentiment"]] += r["count"]
        by_word.setdefault(w, {"word": w, "count": 0})
        by_word[w]["count"] += r["count"]
    for w, data in by_word.items():
        votes = sentiment_votes[w]
        data["sentiment"] = votes.most_common(1)[0][0] if votes else "neutral"
    return sorted(by_word.values(), key=lambda x: x["count"], reverse=True)[:limit]


def fetch_reviews(
    sentiment: str | None = None,
    aspect: str | None = None,
    lang: str | None = None,
    q: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    db = get_db()
    sql = [
        """
        SELECT r.review_id, r.author, r.original_text, r.translated_text,
               r.detected_language, r.rating, r.overall_sentiment, r.overall_score,
               r.date_added, r.source
        FROM reviews r
        """
    ]
    params: list[Any] = []
    where: list[str] = []
    if sentiment:
        where.append("r.overall_sentiment = ?"); params.append(sentiment)
    if lang:
        where.append("r.detected_language = ?"); params.append(lang)
    if q:
        where.append("(r.original_text LIKE ? OR COALESCE(r.translated_text,'') LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if aspect:
        sql.append("WHERE r.review_id IN (SELECT review_id FROM aspect_sentiments WHERE aspect = ?)")
        params.append(aspect)
        if where:
            sql[-1] += " AND " + " AND ".join(where)
    elif where:
        sql.append("WHERE " + " AND ".join(where))
    sql.append("ORDER BY r.date_added DESC LIMIT ?")
    params.append(limit)

    rows = db.execute(" ".join(sql), params).fetchall()
    review_ids = [r["review_id"] for r in rows]

    # Fetch all aspects for these reviews in one query
    aspects_by_review: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    if review_ids:
        placeholders = ",".join("?" * len(review_ids))
        aspect_rows = db.execute(
            f"SELECT review_id, aspect, sentiment, evidence FROM aspect_sentiments WHERE review_id IN ({placeholders})",
            review_ids,
        ).fetchall()
        for a in aspect_rows:
            aspects_by_review[a["review_id"]].append(
                {"aspect": a["aspect"], "sentiment": a["sentiment"], "evidence": a["evidence"]}
            )

    return [
        {
            "id":             r["review_id"],
            "author":         r["author"],
            "originalText":   r["original_text"],
            "translatedText": r["translated_text"],
            "language":       r["detected_language"],
            "rating":         r["rating"],
            "overall":        r["overall_sentiment"],
            "date":           r["date_added"],
            "aspects":        aspects_by_review[r["review_id"]],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Write helpers (used by ingest pipeline in P3a)
# ---------------------------------------------------------------------------
def upsert_restaurant(name: str, source_url: str | None = None) -> int:
    db = get_db()
    cur = db.execute("SELECT restaurant_id FROM restaurants WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row["restaurant_id"]
    cur = db.execute(
        "INSERT INTO restaurants(name, source_url) VALUES (?, ?)",
        (name, source_url),
    )
    db.commit()
    return cur.lastrowid


def insert_review(review: dict[str, Any]) -> int:
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO reviews(
            restaurant_id, author, original_text, translated_text, detected_language,
            rating, overall_sentiment, overall_score, vader_sentiment, vader_score,
            llm_raw_response, date_added, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review.get("restaurant_id"),
            review.get("author"),
            review["original_text"],
            review.get("translated_text"),
            review.get("detected_language"),
            review.get("rating"),
            review.get("overall_sentiment"),
            review.get("overall_score"),
            review.get("vader_sentiment"),
            review.get("vader_score"),
            review.get("llm_raw_response"),
            review.get("date_added"),
            review.get("source"),
        ),
    )
    rid = cur.lastrowid
    for asp in review.get("aspects", []):
        db.execute(
            "INSERT INTO aspect_sentiments(review_id, aspect, sentiment, evidence, source_method) VALUES (?, ?, ?, ?, ?)",
            (rid, asp["aspect"], asp["sentiment"], asp.get("evidence"), asp.get("source_method", "llm")),
        )
    for kw in review.get("keywords", []):
        if isinstance(kw, str):
            db.execute(
                "INSERT INTO keywords(review_id, keyword, frequency) VALUES (?, ?, 1)",
                (rid, kw),
            )
        else:
            db.execute(
                "INSERT INTO keywords(review_id, keyword, frequency, tf_idf_score) VALUES (?, ?, ?, ?)",
                (rid, kw["keyword"], kw.get("frequency", 1), kw.get("tf_idf_score")),
            )
    db.commit()
    return rid
