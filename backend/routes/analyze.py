"""Live single-review analysis endpoint — runs the hybrid NLP pipeline
(Groq + Llama 3.3 + rule aspects) on demand. Requires internet + GROQ_API_KEY.
Powers the frontend Live Analyze page."""
from flask import Blueprint, jsonify, request

from nlp.pipeline import process_review

bp = Blueprint("analyze", __name__)


@bp.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    if len(text) > 2000:
        return jsonify({"error": "text too long (max 2000 chars)"}), 400

    try:
        # VADER baseline isn't needed for the live demo — skip for speed.
        result = process_review(text, run_vader=False)
    except RuntimeError as e:
        # e.g. GROQ_API_KEY missing or LLM returned unparseable JSON twice
        return jsonify({"error": str(e)}), 502

    return jsonify({
        "language":           result["detected_language"],
        "overall_sentiment":  result["overall_sentiment"],
        "overall_confidence": result["overall_score"],
        "aspects":            [
            {"aspect": a["aspect"], "sentiment": a["sentiment"], "evidence": a["evidence"]}
            for a in result["aspects"]
        ],
        "keywords":           result["keywords"],
    })
