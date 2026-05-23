"""SQLite repository for RestoPulse.

One connection per request (Flask `g`), schema initialized on first launch,
and small helpers for the read paths the dashboard needs.
"""
from __future__ import annotations

import os
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from flask import g
from werkzeug.security import generate_password_hash

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
    _seed_default_user()
    app.teardown_appcontext(close_db)


def _seed_default_user() -> None:
    """Create the demo account on first run if no users exist (charter login).

    Runs at startup outside any request context, so it opens its own connection
    rather than using get_db(). Credentials overridable via env; defaults shown
    on the login page for the demo.
    """
    username = os.getenv("ADMIN_USER", "admin")
    password = os.getenv("ADMIN_PASS", "restopulse123")
    conn = sqlite3.connect(DB_PATH)
    try:
        n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if n == 0:
            conn.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'owner')",
                (username, generate_password_hash(password)),
            )
            conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read helpers (dashboard / analytics)
# ---------------------------------------------------------------------------
def fetch_restaurants() -> list[dict[str, Any]]:
    """List restaurants with per-restaurant review counts + avg rating, for the
    restaurant/city filter and the comparison view."""
    db = get_db()
    rows = db.execute(
        """
        SELECT r.restaurant_id, r.name, r.city,
               COUNT(rv.review_id)               AS reviews,
               COALESCE(ROUND(AVG(rv.rating),2),0) AS avg_rating,
               SUM(CASE WHEN rv.overall_sentiment='positive' THEN 1 ELSE 0 END) AS positive,
               SUM(CASE WHEN rv.overall_sentiment='neutral'  THEN 1 ELSE 0 END) AS neutral,
               SUM(CASE WHEN rv.overall_sentiment='negative' THEN 1 ELSE 0 END) AS negative
        FROM restaurants r
        LEFT JOIN reviews rv ON rv.restaurant_id = r.restaurant_id
        GROUP BY r.restaurant_id
        ORDER BY r.city, r.name
        """
    ).fetchall()
    return [dict(r) for r in rows]


def _scope_clause(restaurant_id: int | None, city: str | None) -> tuple[str, list[Any]]:
    """Build an optional WHERE fragment to scope dashboard queries by restaurant
    or city. Returns (clause, params) where clause starts with ' AND ...' or ''."""
    clauses: list[str] = []
    params: list[Any] = []
    if restaurant_id:
        clauses.append("restaurant_id = ?"); params.append(restaurant_id)
    if city:
        clauses.append("restaurant_id IN (SELECT restaurant_id FROM restaurants WHERE city = ?)")
        params.append(city)
    return ((" AND " + " AND ".join(clauses)) if clauses else ""), params


def fetch_summary(restaurant_id: int | None = None, city: str | None = None) -> dict[str, Any]:
    db = get_db()
    scope, params = _scope_clause(restaurant_id, city)
    row = db.execute(
        f"""
        SELECT
          COUNT(*)                                                       AS total,
          SUM(CASE WHEN overall_sentiment='positive' THEN 1 ELSE 0 END)  AS positive,
          SUM(CASE WHEN overall_sentiment='neutral'  THEN 1 ELSE 0 END)  AS neutral,
          SUM(CASE WHEN overall_sentiment='negative' THEN 1 ELSE 0 END)  AS negative,
          COALESCE(ROUND(AVG(rating), 2), 0)                             AS avg_rating
        FROM reviews
        WHERE 1=1 {scope}
        """,
        params,
    ).fetchone()
    total = row["total"] or 0
    return {
        "total":          total,
        "positive":       row["positive"] or 0,
        "neutral":        row["neutral"]  or 0,
        "negative":       row["negative"] or 0,
        "avgRating":      row["avg_rating"],
    }


def fetch_trend() -> list[dict[str, Any]]:
    """Sentiment volume per month across all reviews.

    Review dates come from Google as relative labels ("a year ago") that the scraper
    converts to approximate absolute dates, so we aggregate by month (YYYY-MM) rather
    than by day — it covers the whole corpus and smooths the date approximation.
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT strftime('%Y-%m', date_added)                              AS day,
               SUM(CASE WHEN overall_sentiment='positive' THEN 1 ELSE 0 END) AS positive,
               SUM(CASE WHEN overall_sentiment='neutral'  THEN 1 ELSE 0 END) AS neutral,
               SUM(CASE WHEN overall_sentiment='negative' THEN 1 ELSE 0 END) AS negative
        FROM reviews
        WHERE date_added IS NOT NULL AND date_added <> ''
        GROUP BY day
        ORDER BY day
        """
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


# Low-insight keywords filtered from the "Trending Keywords" widget: the aspect names
# (already shown in the aspect breakdown) plus generic filler words. Excluding them
# lets distinctive terms (delicious, sarap, friendly, accommodating, …) surface.
_GENERIC_KEYWORDS = {
    "food", "service", "ambiance", "price", "cleanliness",
    "good", "great", "nice", "place", "restaurant", "experience",
    "really", "very", "also", "one",
}


def fetch_top_keywords(limit: int = 20) -> list[dict[str, Any]]:
    """Aggregate keyword frequencies across the corpus and tag dominant sentiment."""
    db = get_db()
    blocklist = sorted(_GENERIC_KEYWORDS)
    placeholders = ",".join("?" * len(blocklist))
    rows = db.execute(
        f"""
        SELECT k.keyword, SUM(k.frequency) AS count, r.overall_sentiment AS sentiment
        FROM keywords k
        JOIN reviews r ON r.review_id = k.review_id
        WHERE lower(k.keyword) NOT IN ({placeholders})
        GROUP BY k.keyword
        ORDER BY count DESC
        LIMIT ?
        """,
        (*blocklist, limit),
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
    restaurant_id: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    db = get_db()
    sql = [
        """
        SELECT r.review_id, r.restaurant_id, r.author, r.original_text, r.translated_text,
               r.detected_language, r.rating, r.overall_sentiment, r.overall_score,
               r.date_added, r.source,
               rt.name AS restaurant_name, rt.city AS city
        FROM reviews r
        LEFT JOIN restaurants rt ON rt.restaurant_id = r.restaurant_id
        """
    ]
    params: list[Any] = []
    where: list[str] = []
    if sentiment:
        where.append("r.overall_sentiment = ?"); params.append(sentiment)
    if lang:
        where.append("r.detected_language = ?"); params.append(lang)
    if restaurant_id:
        where.append("r.restaurant_id = ?"); params.append(restaurant_id)
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
            "restaurantId":   r["restaurant_id"],
            "restaurantName": r["restaurant_name"] or "Unknown",
            "city":           r["city"],
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
def upsert_restaurant(
    name: str,
    external_id: str | None = None,
    city: str | None = None,
    source_url: str | None = None,
) -> int:
    db = get_db()
    # Prefer external_id (place_id) as the stable key; fall back to name.
    if external_id:
        row = db.execute(
            "SELECT restaurant_id FROM restaurants WHERE external_id = ?", (external_id,)
        ).fetchone()
    else:
        row = db.execute(
            "SELECT restaurant_id FROM restaurants WHERE name = ?", (name,)
        ).fetchone()
    if row:
        # keep city/name fresh on re-ingest
        db.execute(
            "UPDATE restaurants SET name = ?, city = COALESCE(?, city), source_url = COALESCE(?, source_url) WHERE restaurant_id = ?",
            (name, city, source_url, row["restaurant_id"]),
        )
        db.commit()
        return row["restaurant_id"]
    cur = db.execute(
        "INSERT INTO restaurants(name, external_id, city, source_url) VALUES (?, ?, ?, ?)",
        (name, external_id, city, source_url),
    )
    db.commit()
    return cur.lastrowid


# ---------------------------------------------------------------------------
# Users / auth
# ---------------------------------------------------------------------------
def get_user(username: str) -> dict[str, Any] | None:
    row = get_db().execute(
        "SELECT user_id, username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    return dict(row) if row else None


def create_user(username: str, password_hash: str, role: str = "owner") -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, role),
    )
    db.commit()
    return cur.lastrowid


def count_users() -> int:
    return get_db().execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]


def review_exists(external_id: str) -> bool:
    if not external_id:
        return False
    row = get_db().execute(
        "SELECT 1 FROM reviews WHERE external_id = ? LIMIT 1", (external_id,)
    ).fetchone()
    return row is not None


def insert_review(review: dict[str, Any]) -> int:
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO reviews(
            restaurant_id, external_id, author, original_text, translated_text,
            detected_language, rating, overall_sentiment, overall_score,
            vader_sentiment, vader_score, llm_raw_response, date_added, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review.get("restaurant_id"),
            review.get("external_id"),
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
