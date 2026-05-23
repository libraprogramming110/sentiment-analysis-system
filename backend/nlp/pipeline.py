"""Hybrid NLP pipeline orchestrator.

Ties together the 6 components from starter.MD §1:
  [1] NLTK preprocessing      (preprocess.py)
  [2] langdetect              (language.py)
  [3] LLM ABSA engine         (llm.py)          ← sentiment authority
  [4] rule-based aspect check (aspects.py)
  [5] TF-IDF keywords         (keywords.py)     ← corpus-level, applied in ingest
  [6] VADER baseline          (baseline_vader.py) ← evaluation only

`process_review()` handles a single review (used by the /api/analyze endpoint).
The corpus-level TF-IDF step runs in ingest where the full corpus is available.
"""
from __future__ import annotations

from typing import Any

from nlp import aspects, baseline_vader, language, llm, preprocess


def process_review(text: str, *, run_vader: bool = True) -> dict[str, Any]:
    """Run the hybrid pipeline on one review.

    Returns a dict ready for DB insertion / API response:
        {
          original_text, detected_language,
          overall_sentiment, overall_score,         # from LLM
          aspects: [{aspect, sentiment, evidence, source_method}],
          keywords: [str],                            # LLM keywords (TF-IDF added later)
          vader_sentiment, vader_score,               # baseline (optional)
          llm_raw_response,
        }
    """
    text = (text or "").strip()
    if not text:
        return _empty_result()

    # [1] preprocessing (also bootstraps NLTK)
    cleaned = preprocess.clean_text(text)

    # [2] language detection (our detector)
    ld_guess = language.detect_language(text)

    # [3] LLM ABSA (sentiment authority)
    llm_out = llm.analyze(text)

    # reconcile language: LLM is better at ceb/ilo
    detected = language.reconcile(ld_guess, llm_out.get("language"))

    # [4] validate/augment aspects against the keyword dictionary
    validated_aspects = aspects.validate_llm_aspects(llm_out["aspects"], text)

    result: dict[str, Any] = {
        "original_text":     text,
        "cleaned_text":      cleaned,
        "detected_language": detected,
        "overall_sentiment": llm_out["overall_sentiment"],
        "overall_score":     llm_out["overall_confidence"],
        "aspects":           validated_aspects,
        "keywords":          llm_out["keywords"],
        "llm_raw_response":  llm_out.get("raw_response", ""),
    }

    # [6] VADER baseline for comparison (English-only; degraded on PH languages
    # by design — that's the empirical point of the baseline)
    if run_vader:
        vres = baseline_vader.vader_sentiment(cleaned)
        result["vader_sentiment"] = vres["sentiment"]
        result["vader_score"]     = vres["score"]

    return result


def _empty_result() -> dict[str, Any]:
    return {
        "original_text": "", "cleaned_text": "", "detected_language": "unknown",
        "overall_sentiment": "neutral", "overall_score": 0.0,
        "aspects": [], "keywords": [], "llm_raw_response": "",
        "vader_sentiment": "neutral", "vader_score": 0.0,
    }
