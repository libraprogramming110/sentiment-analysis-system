"""Build the gold-standard test set for the P4 evaluation harness.

Strategy (see starter.MD §3 and the plan):
  - Sample 50 reviews from the ingested DB, STRATIFIED BY LANGUAGE so the minority
    Philippine languages (Cebuano, Tagalog) are over-represented relative to their
    corpus share — that's where the VADER baseline is expected to fail and where the
    comparison is most informative.
  - Within each language, spread the picks across star-rating buckets so the set is
    not dominated by 5-star positives (the corpus is ~80% positive).
  - Prefill candidate gold labels:
      * `gold_overall` is anchored to the STAR RATING, which is independent of both
        systems under evaluation (VADER and the LLM) — so the gold standard is not
        circular. 5/4★ -> positive, 3★ -> neutral, 2/1★ -> negative.
      * `gold_aspects` is seeded from the cached LLM aspect output as a *suggestion*
        for the human annotator to confirm (verified:false).
  - Flag `needs_review:true` whenever the rating-anchored gold disagrees with the
    cached pipeline label — those are the hard cases human verification should focus on.

The output `test_set.json` is a CANDIDATE set: a human should verify it and flip
`meta.verified` to true. Deterministic (fixed seed) so re-running is reproducible.

Usage (from backend/):
    .venv\\Scripts\\python.exe evaluation\\build_test_set.py
    .venv\\Scripts\\python.exe evaluation\\build_test_set.py --n 50 --seed 0
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
from flask import Flask  # noqa: E402

load_dotenv()

from db.repo import get_db, init_db  # noqa: E402

OUT_PATH = Path(__file__).resolve().parent / "test_set.json"

# Language quotas for a 50-sample set: oversample minority PH languages so the
# comparison has signal where it matters. ilo intentionally 0 (none in corpus).
LANG_QUOTA = {"ceb": 14, "tl": 20, "en": 14, "unknown": 2}


def rating_to_sentiment(rating: int | None) -> str:
    """Independent gold anchor from the Google star rating."""
    if rating is None:
        return "neutral"
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


def _spread_by_rating(rows: list[dict], quota: int, rng: random.Random) -> list[dict]:
    """Pick `quota` rows from `rows`, spreading across rating buckets (1..5) so the
    sample isn't all 5-star. Round-robins across buckets, shuffled within each."""
    buckets: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        buckets[r["rating"] or 0].append(r)
    for b in buckets.values():
        rng.shuffle(b)
    # Order buckets to favor diversity: visit each rating in turn, take one at a time.
    order = sorted(buckets.keys())
    picked: list[dict] = []
    while len(picked) < quota and any(buckets[k] for k in order):
        for k in order:
            if buckets[k]:
                picked.append(buckets[k].pop())
                if len(picked) >= quota:
                    break
    return picked


def build(n: int, seed: int) -> dict:
    rng = random.Random(seed)
    init_db()
    app = Flask(__name__)
    with app.app_context():
        db = get_db()
        rows = [
            dict(r)
            for r in db.execute(
                """
                SELECT review_id, original_text, detected_language, rating,
                       overall_sentiment, vader_sentiment
                FROM reviews
                WHERE original_text IS NOT NULL AND TRIM(original_text) <> ''
                """
            ).fetchall()
        ]

        by_lang: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            by_lang[r["detected_language"] or "unknown"].append(r)

        # Fetch LLM aspects for all candidates up front (one query).
        aspects_by_review: dict[int, dict[str, str]] = defaultdict(dict)
        for a in db.execute(
            "SELECT review_id, aspect, sentiment FROM aspect_sentiments"
        ).fetchall():
            aspects_by_review[a["review_id"]][a["aspect"]] = a["sentiment"]

        selected: list[dict] = []
        for lang, quota in LANG_QUOTA.items():
            available = by_lang.get(lang, [])
            quota = min(quota, len(available))
            selected.extend(_spread_by_rating(available, quota, rng))

        # Top up to n if any language under-delivered, drawing from the largest pool.
        if len(selected) < n:
            chosen_ids = {s["review_id"] for s in selected}
            remainder = [r for r in rows if r["review_id"] not in chosen_ids]
            rng.shuffle(remainder)
            selected.extend(remainder[: n - len(selected)])
        selected = selected[:n]
        selected.sort(key=lambda r: r["review_id"])

    samples = []
    needs_review = 0
    for r in selected:
        gold_overall = rating_to_sentiment(r["rating"])
        flag = gold_overall != r["overall_sentiment"]
        needs_review += int(flag)
        samples.append(
            {
                "review_id": r["review_id"],
                "text": r["original_text"],
                "lang": r["detected_language"] or "unknown",
                "rating": r["rating"],
                "gold_overall": gold_overall,
                "gold_aspects": dict(aspects_by_review.get(r["review_id"], {})),
                "verified": False,
                "needs_review": flag,
                "_hint_pipeline": r["overall_sentiment"],
                "_hint_vader": r["vader_sentiment"],
            }
        )

    lang_dist = Counter(s["lang"] for s in samples)
    sent_dist = Counter(s["gold_overall"] for s in samples)

    return {
        "meta": {
            "created": date.today().isoformat(),
            "n": len(samples),
            "seed": seed,
            "verified": False,
            "label_method": (
                "Candidate gold labels: overall sentiment anchored to the Google star "
                "rating (5/4*->positive, 3*->neutral, 2/1*->negative), which is "
                "independent of both evaluated systems (VADER and the LLM). Aspect "
                "labels seeded from cached LLM output as suggestions. To be human-verified."
            ),
            "stratification": "by detected_language (PH languages oversampled); "
            "rating-spread within language",
            "language_distribution": dict(lang_dist),
            "gold_sentiment_distribution": dict(sent_dist),
            "needs_review_count": needs_review,
        },
        "samples": samples,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Build the gold-standard evaluation test set")
    p.add_argument("--n", type=int, default=50, help="number of reviews to sample")
    p.add_argument("--seed", type=int, default=0, help="RNG seed for reproducibility")
    p.add_argument("--out", type=Path, default=OUT_PATH)
    args = p.parse_args()

    data = build(args.n, args.seed)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    m = data["meta"]
    print(f"[build_test_set] wrote {m['n']} samples -> {args.out}")
    print(f"[build_test_set] language distribution : {m['language_distribution']}")
    print(f"[build_test_set] gold sentiment dist    : {m['gold_sentiment_distribution']}")
    print(f"[build_test_set] needs_review (rating != pipeline): {m['needs_review_count']}")
    print("[build_test_set] NOTE: candidate labels — verify, then set meta.verified=true.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
