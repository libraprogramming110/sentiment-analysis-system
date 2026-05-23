"""RestoPulse Flask backend — JSON API for the React frontend."""
from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS

from db.repo import init_app as init_db_app
from routes.dashboard import bp as dashboard_bp
from routes.reviews import bp as reviews_bp
from routes.analytics import bp as analytics_bp
from routes.analyze import bp as analyze_bp
from routes.upload import bp as upload_bp
from routes.auth import bp as auth_bp

load_dotenv()


def create_app() -> Flask:
    # Serve the built React SPA (frontend/ → backend/webdist) as static files at the root,
    # so the API and UI share one origin in production.
    app = Flask(__name__, static_folder="webdist", static_url_path="")

    # Signs the session cookie that keeps users logged in. Set SECRET_KEY in prod.
    app.secret_key = os.getenv("SECRET_KEY", "dev-insecure-key-change-me")

    # CORS only matters cross-origin (e.g. local dev frontend on :5173). Same-origin
    # production needs none. Configurable via ALLOWED_ORIGINS (comma-separated).
    # supports_credentials lets the session cookie ride along in cross-origin dev.
    origins = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    CORS(
        app,
        resources={r"/api/*": {"origins": [o.strip() for o in origins if o.strip()]}},
        supports_credentials=True,
    )

    # Endpoints reachable without a session. Everything else under /api/ is gated.
    _OPEN_API_PATHS = {"/api/login", "/api/logout", "/api/me", "/api/health"}

    @app.before_request
    def require_login():
        path = request.path
        if not path.startswith("/api/"):
            return None  # SPA + static assets always served (login screen must load)
        if request.method == "OPTIONS" or path in _OPEN_API_PATHS:
            return None
        if not session.get("user"):
            return jsonify({"error": "auth required"}), 401
        return None

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "restopulse",
            "time": datetime.utcnow().isoformat() + "Z",
            "groq_key_loaded": bool(os.getenv("GROQ_API_KEY")),
        })

    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(reviews_bp,   url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(analyze_bp,   url_prefix="/api")
    app.register_blueprint(upload_bp,    url_prefix="/api")
    app.register_blueprint(auth_bp,      url_prefix="/api")

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(404)
    def spa_fallback(_err):
        # Real API misses stay JSON; everything else serves the SPA so client-side
        # routes (/reviews, /analytics, …) work on direct load / refresh.
        if request.path.startswith("/api/"):
            return jsonify({"error": "not found"}), 404
        return send_from_directory(app.static_folder, "index.html")

    init_db_app(app)
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
