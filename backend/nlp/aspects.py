"""NLP component [4]: rule-based aspect validator.

Loads the curated multilingual aspect keyword dictionary and detects which
aspects (food/service/ambiance/price/cleanliness) a review mentions, by simple
substring matching across all four languages.

Role in the hybrid pipeline:
  - Cross-checks the LLM's aspect output (catches aspects the LLM missed).
  - Provides a fallback aspect list when the LLM returns nothing.
  - Demonstrates a visible, classical NLP technique for the defense.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ASPECTS = ["food", "service", "ambiance", "price", "cleanliness"]

_KEYWORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "aspect_keywords.json"
_FLAT: dict[str, list[str]] | None = None


def _load() -> dict[str, list[str]]:
    """Flatten the per-language dict into {aspect: [all keywords]} once."""
    global _FLAT
    if _FLAT is None:
        raw = json.loads(_KEYWORDS_PATH.read_text(encoding="utf-8"))
        flat: dict[str, list[str]] = {}
        for aspect, by_lang in raw.items():
            words: list[str] = []
            for kws in by_lang.values():
                words.extend(w.lower() for w in kws)
            flat[aspect] = sorted(set(words), key=len, reverse=True)  # longest first
        _FLAT = flat
    return _FLAT


def detect_aspects(text: str) -> dict[str, list[str]]:
    """Return {aspect: [matched keywords]} for aspects present in `text`."""
    low = f" {(text or '').lower()} "
    hits: dict[str, list[str]] = {}
    for aspect, words in _load().items():
        matched = [w for w in words if f" {w} " in low or w in low]
        if matched:
            hits[aspect] = matched
    return hits


def validate_llm_aspects(
    llm_aspects: list[dict[str, Any]],
    text: str,
) -> list[dict[str, Any]]:
    """Reconcile the LLM's aspect list with rule-based detection.

    - Tags each aspect with `source_method`: 'both' if rules agree, 'llm' if
      only the LLM found it, 'rule' if only the keyword dictionary did.
    - Adds rule-only aspects with neutral sentiment (the LLM is the sentiment
      authority, but a keyword hit means the aspect was at least mentioned).

    Returns a clean aspect list ready for DB insertion.
    """
    rule_hits = detect_aspects(text)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for a in llm_aspects or []:
        aspect = str(a.get("aspect", "")).lower().strip()
        if aspect not in ASPECTS:
            continue
        seen.add(aspect)
        out.append({
            "aspect":        aspect,
            "sentiment":     a.get("sentiment", "neutral"),
            "evidence":      a.get("evidence", ""),
            "source_method": "both" if aspect in rule_hits else "llm",
        })

    # Rule-only aspects the LLM missed — record as mentioned, neutral sentiment.
    for aspect in rule_hits:
        if aspect not in seen:
            out.append({
                "aspect":        aspect,
                "sentiment":     "neutral",
                "evidence":      f"(keyword match: {', '.join(rule_hits[aspect][:3])})",
                "source_method": "rule",
            })

    return out
