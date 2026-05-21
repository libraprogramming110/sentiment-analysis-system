"""RestoPulse Flask backend — JSON API for the React frontend."""
from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from db.repo import init_app as init_db_app
from routes.dashboard import bp as dashboard_bp
from routes.reviews import bp as reviews_bp
from routes.analytics import bp as analytics_bp
from routes.analyze import bp as analyze_bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]}})

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

    init_db_app(app)
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
