"""NLP component [1]: text preprocessing with NLTK.

Traditional NLP: lowercasing, URL/emoji stripping, whitespace normalization,
tokenization, and stopword removal. The *cleaned* text feeds the VADER baseline
and TF-IDF; the *raw* text is what we send to the LLM (which prefers natural
text). This module deliberately exposes both.
"""
from __future__ import annotations

import re
import unicodedata

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# ---------------------------------------------------------------------------
# Lazy NLTK resource bootstrap — downloads once, then cached in user home.
# ---------------------------------------------------------------------------
_NLTK_READY = False


def ensure_nltk() -> None:
    global _NLTK_READY
    if _NLTK_READY:
        return
    for pkg, path in [
        ("punkt", "tokenizers/punkt"),
        ("punkt_tab", "tokenizers/punkt_tab"),
        ("stopwords", "corpora/stopwords"),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)
    _NLTK_READY = True


_URL_RE   = re.compile(r"https?://\S+|www\.\S+")
_EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "]+",
    flags=re.UNICODE,
)
_MULTISPACE_RE = re.compile(r"\s+")

# We keep English stopwords only; Filipino/Cebuano/Ilocano have no NLTK list,
# and stripping their function words risks losing sentiment-bearing particles.
_EN_STOPWORDS: set[str] | None = None


def _stopword_set() -> set[str]:
    global _EN_STOPWORDS
    if _EN_STOPWORDS is None:
        ensure_nltk()
        _EN_STOPWORDS = set(stopwords.words("english"))
    return _EN_STOPWORDS


def clean_text(text: str) -> str:
    """Light cleaning that preserves sentiment cues (kept for VADER/TF-IDF).

    Lowercase, strip URLs + emojis, collapse whitespace, normalize unicode.
    Punctuation is intentionally kept — VADER uses '!' and caps for intensity,
    so callers that want VADER should pass the *raw* text, not this.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = _URL_RE.sub(" ", text)
    text = _EMOJI_RE.sub(" ", text)
    text = _MULTISPACE_RE.sub(" ", text)
    return text.strip()


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Tokenize to lowercase word tokens, optionally dropping English stopwords
    and non-alphanumeric tokens. Used by TF-IDF keyword extraction."""
    ensure_nltk()
    cleaned = clean_text(text).lower()
    tokens = word_tokenize(cleaned)
    tokens = [t for t in tokens if t.isalnum() and len(t) > 2]
    if remove_stopwords:
        sw = _stopword_set()
        tokens = [t for t in tokens if t not in sw]
    return tokens
