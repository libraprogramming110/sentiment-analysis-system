"""Live single-review analysis endpoint. Will call Groq + Llama 3.3 once
nlp/pipeline.py is built. Currently echoes a structured stub."""
from flask import Blueprint, jsonify, request

bp = Blueprint("analyze", __name__)


@bp.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    # Stub response — same shape as the eventual LLM pipeline output.
    return jsonify({
        "language": "unknown",
        "overall_sentiment": "neutral",
        "overall_confidence": 0.0,
        "aspects": [],
        "keywords": [],
        "_stub": True,
        "_received_chars": len(text),
    })
