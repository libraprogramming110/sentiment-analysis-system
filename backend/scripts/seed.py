"""Seed the SQLite DB with a fake restaurant and ~8 sample reviews so the
dashboard isn't empty before the real ingest pipeline (P3a) runs.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\seed.py
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# Make `db` importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask                                # noqa: E402
from db.repo import init_db, get_db, upsert_restaurant, insert_review  # noqa: E402


SEED_REVIEWS = [
    {
        "author": "Maria L.", "rating": 5, "detected_language": "tl",
        "original_text": "Sobrang masarap ang adobo at sinigang! Ang serbisyo naman ay friendly pero medyo mabagal kasi puno.",
        "translated_text": "The adobo and sinigang are really delicious! The service is friendly but a bit slow because it's full.",
        "overall_sentiment": "positive", "overall_score": 0.86,
        "vader_sentiment": "positive", "vader_score": 0.62,
        "aspects": [
            {"aspect": "food",    "sentiment": "positive", "evidence": "Sobrang masarap ang adobo at sinigang"},
            {"aspect": "service", "sentiment": "negative", "evidence": "medyo mabagal kasi puno"},
        ],
        "keywords": ["masarap", "adobo", "sinigang", "mabagal", "friendly"],
    },
    {
        "author": "John R.", "rating": 4, "detected_language": "en",
        "original_text": "Great ambiance and the staff are accommodating. Prices are a bit on the higher side though.",
        "translated_text": None,
        "overall_sentiment": "positive", "overall_score": 0.78,
        "vader_sentiment": "positive", "vader_score": 0.71,
        "aspects": [
            {"aspect": "ambiance", "sentiment": "positive", "evidence": "Great ambiance"},
            {"aspect": "service",  "sentiment": "positive", "evidence": "staff are accommodating"},
            {"aspect": "price",    "sentiment": "negative", "evidence": "Prices are a bit on the higher side"},
        ],
        "keywords": ["ambiance", "staff", "accommodating", "prices", "higher"],
    },
    {
        "author": "Cristina P.", "rating": 2, "detected_language": "ceb",
        "original_text": "Lami ang pagkaon pero hugaw ang lamesa ug dugay kaayo ang waiter mu-attend.",
        "translated_text": "The food is tasty but the table was dirty and the waiter took very long to attend.",
        "overall_sentiment": "negative", "overall_score": 0.81,
        "vader_sentiment": "neutral", "vader_score": 0.05,
        "aspects": [
            {"aspect": "food",        "sentiment": "positive", "evidence": "Lami ang pagkaon"},
            {"aspect": "cleanliness", "sentiment": "negative", "evidence": "hugaw ang lamesa"},
            {"aspect": "service",     "sentiment": "negative", "evidence": "dugay kaayo ang waiter mu-attend"},
        ],
        "keywords": ["lami", "pagkaon", "hugaw", "lamesa", "dugay", "waiter"],
    },
    {
        "author": "Joseph M.", "rating": 5, "detected_language": "ilo",
        "original_text": "Naimas unay ti pinakbet ken nagsayaat ti serbisyo. Awan duduana, agsubliak.",
        "translated_text": "The pinakbet was very delicious and the service was excellent. No doubt, I'll return.",
        "overall_sentiment": "positive", "overall_score": 0.91,
        "vader_sentiment": "neutral", "vader_score": 0.0,
        "aspects": [
            {"aspect": "food",    "sentiment": "positive", "evidence": "Naimas unay ti pinakbet"},
            {"aspect": "service", "sentiment": "positive", "evidence": "nagsayaat ti serbisyo"},
        ],
        "keywords": ["naimas", "pinakbet", "nagsayaat", "serbisyo"],
    },
    {
        "author": "Aliyah S.", "rating": 3, "detected_language": "tl",
        "original_text": "Okay lang ang food, walang kakaiba. Maingay sa loob, mahirap mag-usap.",
        "translated_text": "The food is just okay, nothing special. It's noisy inside, hard to talk.",
        "overall_sentiment": "neutral", "overall_score": 0.72,
        "vader_sentiment": "neutral", "vader_score": 0.0,
        "aspects": [
            {"aspect": "food",     "sentiment": "neutral",  "evidence": "Okay lang ang food"},
            {"aspect": "ambiance", "sentiment": "negative", "evidence": "Maingay sa loob"},
        ],
        "keywords": ["okay", "food", "kakaiba", "maingay", "loob"],
    },
    {
        "author": "Mark D.", "rating": 5, "detected_language": "en",
        "original_text": "Best lechon kawali I've ever had. Worth every peso. Will definitely come back!",
        "translated_text": None,
        "overall_sentiment": "positive", "overall_score": 0.95,
        "vader_sentiment": "positive", "vader_score": 0.84,
        "aspects": [
            {"aspect": "food",  "sentiment": "positive", "evidence": "Best lechon kawali I've ever had"},
            {"aspect": "price", "sentiment": "positive", "evidence": "Worth every peso"},
        ],
        "keywords": ["best", "lechon", "kawali", "worth", "peso"],
    },
    {
        "author": "Reyna F.", "rating": 1, "detected_language": "tl",
        "original_text": "Ang baho ng banyo at madumi ang sahig. Hindi na ako babalik dito.",
        "translated_text": "The bathroom smells bad and the floor is dirty. I won't come back here.",
        "overall_sentiment": "negative", "overall_score": 0.93,
        "vader_sentiment": "negative", "vader_score": -0.55,
        "aspects": [
            {"aspect": "cleanliness", "sentiment": "negative", "evidence": "Ang baho ng banyo at madumi ang sahig"},
        ],
        "keywords": ["baho", "banyo", "madumi", "sahig"],
    },
    {
        "author": "Carlos U.", "rating": 4, "detected_language": "en",
        "original_text": "Solid Filipino food at fair prices. Ambiance is cozy. Service could be a bit faster.",
        "translated_text": None,
        "overall_sentiment": "positive", "overall_score": 0.74,
        "vader_sentiment": "positive", "vader_score": 0.51,
        "aspects": [
            {"aspect": "food",     "sentiment": "positive", "evidence": "Solid Filipino food"},
            {"aspect": "price",    "sentiment": "positive", "evidence": "fair prices"},
            {"aspect": "ambiance", "sentiment": "positive", "evidence": "Ambiance is cozy"},
            {"aspect": "service",  "sentiment": "negative", "evidence": "Service could be a bit faster"},
        ],
        "keywords": ["solid", "filipino", "food", "fair", "prices", "cozy"],
    },
]


def main() -> None:
    init_db()

    app = Flask(__name__)
    with app.app_context():
        db = get_db()
        existing = db.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        if existing > 0:
            print(f"[seed] DB already has {existing} reviews — clearing first.")
            db.executescript(
                "DELETE FROM keywords; DELETE FROM aspect_sentiments; DELETE FROM reviews; DELETE FROM restaurants;"
            )
            db.commit()

        rest_id = upsert_restaurant("Casa Adobo", "https://maps.google.com/?q=casa+adobo")

        today = date.today()
        for i, rev in enumerate(SEED_REVIEWS):
            rev["restaurant_id"] = rest_id
            rev["date_added"] = (today - timedelta(days=i)).isoformat()
            rev["source"] = "seed"
            insert_review(rev)

        n = db.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        print(f"[seed] inserted {n} reviews for restaurant_id={rest_id}")


if __name__ == "__main__":
    main()
