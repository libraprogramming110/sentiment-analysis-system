"""NLP component [6]: VADER baseline (evaluation comparison only).

VADER is English-only and lexicon-based. For non-English reviews we score the
English text when available (the LLM/translation provides `translated_text`),
otherwise we score the original and accept the degraded result — that *is* the
point of the baseline: to show, empirically, where a traditional English
lexicon approach falls short on Filipino/Cebuano/Ilocano vs the hybrid pipeline.

Never shown in the dashboard; used by evaluation/evaluate.py.
"""
from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_ANALYZER: SentimentIntensityAnalyzer | None = None


def _analyzer() -> SentimentIntensityAnalyzer:
    global _ANALYZER
    if _ANALYZER is None:
        _ANALYZER = SentimentIntensityAnalyzer()
    return _ANALYZER


def vader_sentiment(text: str) -> dict[str, float | str]:
    """Return {'sentiment': label, 'score': compound} using VADER thresholds.

    Standard VADER cutoffs: compound >= 0.05 positive, <= -0.05 negative.
    """
    scores = _analyzer().polarity_scores(text or "")
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {"sentiment": label, "score": compound}
