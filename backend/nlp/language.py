"""NLP component [2]: language identification.

Uses langdetect (Google's n-gram language detector port). langdetect doesn't
support Cebuano (ceb) or Ilocano (ilo) directly — it maps them to 'tl' (Tagalog)
or other close languages — so we layer a small keyword heuristic on top to
distinguish the regional Philippine languages our corpus actually contains.

The LLM also returns a language guess; pipeline.py reconciles the two.
"""
from __future__ import annotations

from langdetect import DetectorFactory, detect_langs

# Deterministic output across runs (langdetect is randomized by default).
DetectorFactory.seed = 0

SUPPORTED = {"en", "tl", "ceb", "ilo"}

# Distinctive function words / markers per regional language. These are cheap
# tiebreakers, not a full classifier — the LLM is the authority; this just
# rescues common cases langdetect can't separate (ceb/ilo both look like 'tl').
_CEBUANO_MARKERS = {
    "lami", "kaayo", "kaayu", "nindot", "gyud", "jud", "kaonon", "lami kaayo",
    "maayo", "pagkaon", "gwapa", "samok", "hugaw", "barato", "lami kaayo",
    "nalami", "lami gyud", "nindota", "ganahan", " paborito", "sulit kaayo",
    "ila", "ilang", "naa", "wala", "gamay", "dako", "presyo",
}
# Ilocano markers: ONLY strong, unambiguous multi-character words. Short
# function words ("ti", "adda", "awan") were removed — they substring-match
# inside English/Tagalog/Cebuano text and caused heavy false positives on this
# Mindanao corpus (which contains essentially no real Ilocano).
_ILOCANO_MARKERS = {
    "naimas", "nalaing", "nasayaat", "agsublik", "naimbag",
    "naraniag", "naimas unay", "nangina", "nalaka",
}
_TAGALOG_MARKERS = {
    "masarap", "sobrang", "sarap", "mabilis", "mabagal", "napakasarap",
    "serbisyo", "presyo", "mura", "mahal", "malinis", "marumi", "talaga",
    "ang sarap", "ng beef", "niyo", "kami", "naman", "lang", "sila",
}


def _heuristic_ph_lang(text: str) -> str | None:
    """Return 'ceb'|'ilo'|'tl' if regional markers strongly suggest one."""
    low = f" {text.lower()} "
    ceb = sum(1 for m in _CEBUANO_MARKERS if f" {m} " in low)
    ilo = sum(1 for m in _ILOCANO_MARKERS if f" {m} " in low)
    tl  = sum(1 for m in _TAGALOG_MARKERS if f" {m} " in low)
    best = max(("ceb", ceb), ("ilo", ilo), ("tl", tl), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else None


def _is_latin_script(text: str) -> bool:
    """True if the text is predominantly Latin-alphabet (a-z) — i.e. plausibly
    English/Filipino/Cebuano/Ilocano rather than Japanese/Korean/Arabic/etc."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if "a" <= c.lower() <= "z")
    return latin / len(letters) >= 0.6


def detect_language(text: str) -> str:
    """Best-effort language code in SUPPORTED, falling back to 'en'/'unknown'.

    Strategy:
      1. Regional marker heuristic first (ceb/ilo/tl) — strongest signal for our
         corpus, and robust on short code-mixed text.
      2. langdetect for the base guess.
      3. For ambiguous Latin-script text, default to English (this corpus is
         English-dominant); reserve 'unknown' for genuinely non-Latin scripts.
    """
    text = (text or "").strip()
    if not text:
        return "unknown"

    # 1) Strong regional markers win immediately (handles short Bisaya/Taglish).
    heuristic = _heuristic_ph_lang(text)
    if heuristic:
        return heuristic

    try:
        ranked = detect_langs(text)
    except Exception:
        ranked = []

    base = ranked[0].lang if ranked else None
    base_conf = ranked[0].prob if ranked else 0.0

    # 2) Confident, recognized results.
    if base == "tl":
        return "tl"
    if base == "en" and base_conf >= 0.50:
        return "en"

    # 3) Non-Latin script (Japanese, Korean, Arabic-script Maranao, …) → unknown.
    if not _is_latin_script(text):
        return "unknown"

    # 4) Latin-script but ambiguous (short/code-mixed): default to English,
    #    the dominant language of this corpus.
    return "en"


def reconcile(langdetect_guess: str, llm_guess: str | None) -> str:
    """Combine our detector with the LLM's language field. The LLM is generally
    better at ceb/ilo, so prefer it when it names a supported regional language;
    otherwise keep our detector's answer."""
    llm = (llm_guess or "").lower().strip()
    if llm in {"ceb", "ilo"}:
        return llm
    if llm in SUPPORTED and langdetect_guess in {"unknown", "tl"}:
        return llm
    if langdetect_guess in SUPPORTED:
        return langdetect_guess
    return llm if llm in SUPPORTED else "unknown"
