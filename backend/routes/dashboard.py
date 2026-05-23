"""Dashboard endpoints reading from SQLite."""
from flask import Blueprint, jsonify, request

from db.repo import (
    fetch_summary,
    fetch_trend,
    fetch_top_issues,
    fetch_languages,
    fetch_restaurants,
)

bp = Blueprint("dashboard", __name__)


@bp.get("/restaurants")
def restaurants():
    return jsonify({"restaurants": fetch_restaurants()})


@bp.get("/summary")
def summary():
    rid = request.args.get("restaurant_id", type=int)
    city = request.args.get("city") or None
    return jsonify(fetch_summary(restaurant_id=rid, city=city))


@bp.get("/trend")
def trend():
    return jsonify({"trend": fetch_trend()})


@bp.get("/issues")
def issues():
    return jsonify({"issues": fetch_top_issues(limit=3)})


@bp.get("/languages")
def languages():
    return jsonify({"languages": fetch_languages()})
