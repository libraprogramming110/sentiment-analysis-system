"""Analytics endpoints: aspect breakdown, keyword frequencies, pipeline
evaluation comparison."""
import json
from pathlib import Path

from flask import Blueprint, jsonify, request

from db.repo import fetch_aspects, fetch_top_keywords

bp = Blueprint("analytics", __name__)

# Written by evaluation/evaluate.py. Present once the harness has been run.
_RESULTS_JSON = Path(__file__).resolve().parent.parent / "evaluation" / "results.json"


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
    """Hybrid (LLM) vs VADER baseline comparison.

    Serves the real numbers from evaluation/results.json once the harness has run
    (overall + per-language accuracy, both pipelines). Falls back to a `_pending`
    stub if the file is missing or unreadable so the UI still renders."""
    if _RESULTS_JSON.is_file():
        try:
            data = json.loads(_RESULTS_JSON.read_text(encoding="utf-8"))
            if data.get("vader") and data.get("hybrid"):
                return jsonify({
                    "vader":   data["vader"],
                    "hybrid":  data["hybrid"],
                    "_pending": bool(data.get("_pending", False)),
                    "_meta":   data.get("_meta"),
                })
        except (json.JSONDecodeError, OSError):
            pass

    return jsonify({
        "vader":  {"overall": 0, "food": 0, "service": 0, "ambiance": 0, "price": 0, "cleanliness": 0},
        "hybrid": {"overall": 0, "food": 0, "service": 0, "ambiance": 0, "price": 0, "cleanliness": 0},
        "_pending": True,
    })
