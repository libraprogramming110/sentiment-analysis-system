"""Authentication endpoints (charter Login page + Users table).

Simple session-based auth: a correct login stores the user in Flask's signed
session cookie; the global gate in app.py rejects unauthenticated /api/* calls.
Passwords are verified against the Werkzeug hash stored in the users table.
"""
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash

from db.repo import get_user

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    user = get_user(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password."}), 401

    session["user"] = {"username": user["username"], "role": user["role"]}
    session.permanent = True
    return jsonify(session["user"])


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
def me():
    user = session.get("user")
    if not user:
        return jsonify({"error": "not authenticated"}), 401
    return jsonify(user)
