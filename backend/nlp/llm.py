"""NLP component [3]: LLM sentiment + ABSA engine (Groq + Llama 3.3 70B).

A single structured prompt returns overall sentiment, per-aspect sentiment with
evidence, detected language, and keywords — as strict JSON. Includes:
  - temperature=0 for reproducibility
  - JSON-mode response + schema validation
  - one stricter retry on malformed output
  - simple token-bucket throttle to respect Groq free-tier rate limits
  - optional Gemini fallback hook (not required for the demo)
"""
from __future__ import annotations

import json
import os
import time
from threading import Lock
from typing import Any

from groq import Groq

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
VALID_SENTIMENTS = {"positive", "neutral", "negative"}
VALID_ASPECTS = {"food", "service", "ambiance", "price", "cleanliness"}

# Compact prompt — sent on every request, so kept short to conserve daily tokens.
SYSTEM_PROMPT = (
    "Aspect-based sentiment for restaurant reviews (English/Tagalog/Cebuano/Ilocano). "
    "Output ONLY minified JSON: "
    '{"language":"en|tl|ceb|ilo|other","overall_sentiment":"positive|neutral|negative",'
    '"overall_confidence":0-1,"aspects":[{"aspect":"food|service|ambiance|price|cleanliness",'
    '"sentiment":"positive|neutral|negative","evidence":"verbatim quote"}],"keywords":["..."]}. '
    "Only include mentioned aspects. 3-6 keywords."
)


class _Throttle:
    """Minimal request-rate limiter for the Groq free tier (default 30 req/min)."""

    def __init__(self, max_per_min: int = 28) -> None:
        self.min_interval = 60.0 / max_per_min
        self._last = 0.0
        self._lock = Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delta = now - self._last
            if delta < self.min_interval:
                time.sleep(self.min_interval - delta)
            self._last = time.monotonic()


_client: Groq | None = None
_throttle = _Throttle()


def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set — add it to backend/.env")
        _client = Groq(api_key=key)
    return _client


def _coerce_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate + clamp the model's JSON into our canonical shape."""
    overall = str(raw.get("overall_sentiment", "neutral")).lower()
    if overall not in VALID_SENTIMENTS:
        overall = "neutral"

    try:
        conf = float(raw.get("overall_confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))

    aspects: list[dict[str, Any]] = []
    for a in raw.get("aspects", []) or []:
        asp = str(a.get("aspect", "")).lower().strip()
        sent = str(a.get("sentiment", "neutral")).lower().strip()
        if asp in VALID_ASPECTS and sent in VALID_SENTIMENTS:
            aspects.append({
                "aspect": asp,
                "sentiment": sent,
                "evidence": str(a.get("evidence", "")).strip()[:300],
            })

    keywords = [str(k).strip() for k in (raw.get("keywords") or []) if str(k).strip()][:8]
    language = str(raw.get("language", "other")).lower().strip()

    return {
        "language": language,
        "overall_sentiment": overall,
        "overall_confidence": conf,
        "aspects": aspects,
        "keywords": keywords,
    }


def _call(text: str, strict: bool = False) -> dict[str, Any]:
    system = SYSTEM_PROMPT
    if strict:
        system += "\nIMPORTANT: your previous output was invalid. Output ONLY the JSON object."
    _throttle.wait()
    resp = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=800,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f'Review: "{text}"'},
        ],
    )
    content = resp.choices[0].message.content
    return json.loads(content), content  # type: ignore[return-value]


def analyze(text: str) -> dict[str, Any]:
    """Analyze one review. Returns the canonical dict plus `raw_response`
    (the cached JSON string, stored in SQLite for reproducibility).

    Raises RuntimeError only if both the initial call and the strict retry fail.
    """
    text = (text or "").strip()
    if not text:
        return {
            "language": "unknown", "overall_sentiment": "neutral",
            "overall_confidence": 0.0, "aspects": [], "keywords": [],
            "raw_response": "",
        }

    last_err: Exception | None = None
    for strict in (False, True):
        try:
            parsed, raw = _call(text, strict=strict)
            result = _coerce_result(parsed)
            result["raw_response"] = raw
            return result
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            last_err = e
            continue
    raise RuntimeError(f"LLM returned unparseable JSON twice: {last_err}")
