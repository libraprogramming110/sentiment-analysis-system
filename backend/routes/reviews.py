"""Reviews list endpoint with filtering."""
from flask import Blueprint, jsonify, request

from db.repo import fetch_reviews

bp = Blueprint("reviews", __name__)


@bp.get("/reviews")
def list_reviews():
    sentiment = request.args.get("sentiment") or None
    aspect    = request.args.get("aspect")    or None
    lang      = request.args.get("lang")      or None
    q         = request.args.get("q")         or None
    limit_raw = request.args.get("limit", "100")
    try:
        limit = max(1, min(int(limit_raw), 500))
    except ValueError:
        limit = 100

    reviews = fetch_reviews(sentiment=sentiment, aspect=aspect, lang=lang, q=q, limit=limit)
    return jsonify({
        "reviews": reviews,
        "filters": {"sentiment": sentiment, "aspect": aspect, "lang": lang, "q": q},
        "total":   len(reviews),
    })
