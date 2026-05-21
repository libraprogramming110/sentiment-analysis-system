"""Analytics endpoints: aspect breakdown, keyword frequencies, pipeline
evaluation comparison."""
from flask import Blueprint, jsonify, request

from db.repo import fetch_aspects, fetch_top_keywords

bp = Blueprint("analytics", __name__)


@bp.get("/aspects")
def aspects():
    return jsonify({"aspects": fetch_aspects()})


@bp.get("/keywords")
def keywords():
    limit_raw = request.args.get("limit", "20")
    try:
        limit = max(1, min(int(limit_raw), 100))
    except ValueError:
        limit = 20
    return jsonify({"keywords": fetch_top_keywords(limit=limit)})


@bp.get("/evaluation")
def evaluation():
    """Hybrid (LLM) vs VADER baseline comparison. Will be populated by
    evaluation/evaluate.py once the test set is hand-labeled. Returns
    placeholder zeros for now so the UI renders."""
    return jsonify({
        "vader":  {"overall": 0, "food": 0, "service": 0, "ambiance": 0, "price": 0, "cleanliness": 0},
        "hybrid": {"overall": 0, "food": 0, "service": 0, "ambiance": 0, "price": 0, "cleanliness": 0},
        "_pending": True,
    })
