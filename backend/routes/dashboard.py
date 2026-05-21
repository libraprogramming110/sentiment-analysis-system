"""Dashboard endpoints reading from SQLite."""
from flask import Blueprint, jsonify

from db.repo import (
    fetch_summary,
    fetch_trend,
    fetch_top_issues,
    fetch_languages,
)

bp = Blueprint("dashboard", __name__)


@bp.get("/summary")
def summary():
    return jsonify(fetch_summary())


@bp.get("/trend")
def trend():
    return jsonify({"trend": fetch_trend(days=30)})


@bp.get("/issues")
def issues():
    return jsonify({"issues": fetch_top_issues(limit=3)})


@bp.get("/languages")
def languages():
    return jsonify({"languages": fetch_languages()})
