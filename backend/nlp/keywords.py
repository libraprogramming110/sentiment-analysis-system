"""NLP component [5]: TF-IDF keyword extraction (corpus-level, statistical NLP).

The LLM extracts per-review keywords, but those are model-chosen and not ranked
by corpus importance. This module runs a classic TF-IDF over the whole review
corpus to surface statistically distinctive terms — a visible, defensible
traditional-NLP technique independent of the LLM.
"""
from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer

from nlp.preprocess import tokenize


def _identity(tokens: list[str]) -> list[str]:
    return tokens


def extract_corpus_keywords(
    texts: list[str],
    top_n_per_doc: int = 6,
) -> list[list[dict[str, Any]]]:
    """Compute TF-IDF over the corpus; return per-document top keywords.

    Returns a list parallel to `texts`; each entry is a list of
    {keyword, tf_idf_score} dicts (highest score first).
    """
    if not texts:
        return []

    token_lists = [tokenize(t, remove_stopwords=True) for t in texts]

    # Guard: documents with no usable tokens still need a slot in the output.
    nonempty_idx = [i for i, toks in enumerate(token_lists) if toks]
    if not nonempty_idx:
        return [[] for _ in texts]

    vectorizer = TfidfVectorizer(
        tokenizer=_identity,
        preprocessor=_identity,
        token_pattern=None,
        lowercase=False,
        min_df=1,
        ngram_range=(1, 2),
    )
    matrix = vectorizer.fit_transform([token_lists[i] for i in nonempty_idx])
    vocab = vectorizer.get_feature_names_out()

    results: list[list[dict[str, Any]]] = [[] for _ in texts]
    for row_pos, doc_idx in enumerate(nonempty_idx):
        row = matrix.getrow(row_pos)
        if row.nnz == 0:
            continue
        pairs = sorted(
            zip(row.indices, row.data), key=lambda kv: kv[1], reverse=True
        )[:top_n_per_doc]
        results[doc_idx] = [
            {"keyword": str(vocab[idx]), "tf_idf_score": round(float(score), 4)}
            for idx, score in pairs
        ]
    return results
