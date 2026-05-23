"""P4 evaluation harness — Hybrid (LLM) pipeline vs VADER baseline.

Reads the gold-standard test_set.json and compares each pipeline's CACHED
predictions (already in SQLite — no LLM/VADER recomputation, zero Groq tokens)
against the gold labels. Computes, for both pipelines:

  - overall accuracy
  - precision / recall / F1 per class (positive/neutral/negative) + macro-F1
  - 3x3 confusion matrix
  - per-language accuracy breakdown
  - per-aspect accuracy (hybrid uses its ABSA aspect labels; VADER has no ABSA,
    so its document-level label is broadcast to each mentioned aspect — a fair,
    documented baseline that also shows why hybrid wins on aspects)

Outputs:
  - evaluation/results.md   (human-readable tables — the defense slide)
  - evaluation/results.json (machine-readable, in the /api/evaluation shape)

Usage (from backend/):
    .venv\\Scripts\\python.exe evaluation\\evaluate.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
from flask import Flask  # noqa: E402

load_dotenv()

from db.repo import get_db, init_db  # noqa: E402

HERE = Path(__file__).resolve().parent
TEST_SET_PATH = HERE / "test_set.json"
RESULTS_MD = HERE / "results.md"
RESULTS_JSON = HERE / "results.json"

CLASSES = ["positive", "neutral", "negative"]
ASPECTS = ["food", "service", "ambiance", "price", "cleanliness"]
ACCURACY_TARGET = 80.0  # charter success metric


# ---------------------------------------------------------------------------
# Metrics (hand-rolled for transparency at the defense — no sklearn needed)
# ---------------------------------------------------------------------------
def accuracy(pairs: list[tuple[str, str]]) -> float:
    """pairs = list of (gold, pred). Returns % correct."""
    if not pairs:
        return 0.0
    correct = sum(1 for g, p in pairs if g == p)
    return round(100.0 * correct / len(pairs), 1)


def per_class_prf(pairs: list[tuple[str, str]]) -> dict[str, dict[str, float]]:
    """Precision/recall/F1 per class plus macro-F1."""
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    for g, p in pairs:
        if g == p:
            tp[g] += 1
        else:
            fp[p] += 1
            fn[g] += 1
    out: dict[str, dict[str, float]] = {}
    f1s = []
    for c in CLASSES:
        prec = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) else 0.0
        rec = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out[c] = {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
            "support": tp[c] + fn[c],
        }
        f1s.append(f1)
    out["macro"] = {"f1": round(sum(f1s) / len(f1s), 3)} if f1s else {"f1": 0.0}
    return out


def confusion(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    """matrix[gold][pred] = count."""
    m = {g: {p: 0 for p in CLASSES} for g in CLASSES}
    for g, p in pairs:
        if g in m and p in m[g]:
            m[g][p] += 1
    return m


# ---------------------------------------------------------------------------
# Load predictions from the cached DB
# ---------------------------------------------------------------------------
def load_predictions(review_ids: list[int]) -> dict[int, dict]:
    """For each review_id, the cached hybrid + VADER overall labels and the
    hybrid per-aspect labels."""
    init_db()
    app = Flask(__name__)
    preds: dict[int, dict] = {}
    with app.app_context():
        db = get_db()
        placeholders = ",".join("?" * len(review_ids))
        for r in db.execute(
            f"""SELECT review_id, overall_sentiment, vader_sentiment, detected_language
                FROM reviews WHERE review_id IN ({placeholders})""",
            review_ids,
        ).fetchall():
            preds[r["review_id"]] = {
                "hybrid": r["overall_sentiment"],
                "vader": r["vader_sentiment"],
                "lang": r["detected_language"],
                "aspects": {},
            }
        for a in db.execute(
            f"""SELECT review_id, aspect, sentiment FROM aspect_sentiments
                WHERE review_id IN ({placeholders})""",
            review_ids,
        ).fetchall():
            if a["review_id"] in preds:
                preds[a["review_id"]]["aspects"][a["aspect"]] = a["sentiment"]
    return preds


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate() -> dict:
    test_set = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
    samples = test_set["samples"]
    review_ids = [s["review_id"] for s in samples]
    preds = load_predictions(review_ids)

    hybrid_pairs: list[tuple[str, str]] = []
    vader_pairs: list[tuple[str, str]] = []
    lang_pairs: dict[str, dict[str, list]] = defaultdict(
        lambda: {"hybrid": [], "vader": []}
    )
    # per-aspect (gold_aspect_sentiment, pred)
    aspect_pairs: dict[str, dict[str, list]] = {
        a: {"hybrid": [], "vader": []} for a in ASPECTS
    }

    missing = 0
    for s in samples:
        rid = s["review_id"]
        pred = preds.get(rid)
        if not pred:
            missing += 1
            continue
        gold = s["gold_overall"]
        lang = s.get("lang") or pred["lang"] or "unknown"

        hybrid_pairs.append((gold, pred["hybrid"]))
        vader_pairs.append((gold, pred["vader"]))
        lang_pairs[lang]["hybrid"].append((gold, pred["hybrid"]))
        lang_pairs[lang]["vader"].append((gold, pred["vader"]))

        # Per-aspect: gold aspect sentiment vs hybrid aspect label, and vs VADER's
        # document-level label broadcast to that aspect.
        for aspect, gold_sent in (s.get("gold_aspects") or {}).items():
            if aspect not in aspect_pairs:
                continue
            hyb = pred["aspects"].get(aspect)
            if hyb is not None:
                aspect_pairs[aspect]["hybrid"].append((gold_sent, hyb))
            aspect_pairs[aspect]["vader"].append((gold_sent, pred["vader"]))

    # --- overall metrics ---
    hybrid = {
        "overall_accuracy": accuracy(hybrid_pairs),
        "prf": per_class_prf(hybrid_pairs),
        "confusion": confusion(hybrid_pairs),
    }
    vader = {
        "overall_accuracy": accuracy(vader_pairs),
        "prf": per_class_prf(vader_pairs),
        "confusion": confusion(vader_pairs),
    }

    # --- per-language ---
    per_language = {}
    for lang, d in sorted(lang_pairs.items()):
        per_language[lang] = {
            "n": len(d["hybrid"]),
            "hybrid": accuracy(d["hybrid"]),
            "vader": accuracy(d["vader"]),
        }

    # --- per-aspect ---
    per_aspect = {}
    for aspect in ASPECTS:
        h = aspect_pairs[aspect]["hybrid"]
        v = aspect_pairs[aspect]["vader"]
        per_aspect[aspect] = {
            "n": len(v),  # number of gold-labeled aspect mentions
            "hybrid": accuracy(h),
            "vader": accuracy(v),
        }

    return {
        "meta": {
            "evaluated": date.today().isoformat(),
            "n": len(samples),
            "n_scored": len(hybrid_pairs),
            "missing_predictions": missing,
            "test_set_verified": test_set.get("meta", {}).get("verified", False),
            "accuracy_target": ACCURACY_TARGET,
            "target_met": hybrid["overall_accuracy"] >= ACCURACY_TARGET,
            "label_method": test_set.get("meta", {}).get("label_method", ""),
        },
        "hybrid": hybrid,
        "vader": vader,
        "per_language": per_language,
        "per_aspect": per_aspect,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------
def write_results_json(ev: dict) -> None:
    """Machine-readable, in the exact /api/evaluation shape: per-metric accuracy
    percentages with an `overall` key, for both pipelines.

    We expose `overall` + the per-LANGUAGE breakdown (not per-aspect): every value
    here is scored against the rating-anchored gold label, which is independent of
    both systems. Per-aspect hybrid accuracy is intentionally NOT published to the
    chart because, while the aspect gold is seeded from the LLM (pending human
    verification), it would be circular. The full per-aspect table lives in
    results.md, clearly flagged."""
    hybrid_api = {"overall": ev["hybrid"]["overall_accuracy"]}
    vader_api = {"overall": ev["vader"]["overall_accuracy"]}
    for lang, d in ev["per_language"].items():
        hybrid_api[lang] = d["hybrid"]
        vader_api[lang] = d["vader"]

    RESULTS_JSON.write_text(
        json.dumps(
            {
                "vader": vader_api,
                "hybrid": hybrid_api,
                "_pending": False,
                "_meta": ev["meta"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _conf_table(m: dict[str, dict[str, int]]) -> list[str]:
    lines = ["| gold ↓ \\ pred → | positive | neutral | negative |",
             "|---|---|---|---|"]
    for g in CLASSES:
        row = m[g]
        lines.append(f"| **{g}** | {row['positive']} | {row['neutral']} | {row['negative']} |")
    return lines


def write_results_md(ev: dict) -> None:
    h, v = ev["hybrid"], ev["vader"]
    m = ev["meta"]
    delta = round(h["overall_accuracy"] - v["overall_accuracy"], 1)
    lines: list[str] = []
    a = lines.append

    a("# RestoPulse — Pipeline Evaluation Results")
    a("")
    a(f"_Generated {m['evaluated']} · {m['n_scored']} reviews scored "
      f"(of {m['n']} in the test set)._")
    a("")
    a("## Methodology")
    a("")
    a(f"- **Test set:** {m['n']} reviews, stratified by language (Cebuano/Tagalog "
      "oversampled vs their corpus share) and spread across star ratings to avoid "
      "majority-class (positive) inflation.")
    a(f"- **Gold labels:** {m['label_method']}")
    a(f"- **Human-verified:** {'yes' if m['test_set_verified'] else 'NO — candidate labels, pending team verification'}.")
    a("- **Predictions:** read from the cached SQLite DB (no recomputation, zero API "
      "tokens) — fully reproducible and offline.")
    a("- **VADER baseline:** English-only, lexicon-based. It has no aspect-based "
      "output, so for the per-aspect comparison its single document-level label is "
      "broadcast to each mentioned aspect.")
    a("")
    a("## Headline: Overall Accuracy")
    a("")
    a("| Pipeline | Overall accuracy | Macro-F1 |")
    a("|---|---|---|")
    a(f"| VADER baseline | {v['overall_accuracy']}% | {v['prf']['macro']['f1']} |")
    a(f"| **Hybrid (LLM)** | **{h['overall_accuracy']}%** | **{h['prf']['macro']['f1']}** |")
    a(f"| Δ (hybrid − baseline) | **{delta:+}%** | — |")
    a("")
    target = "✅ **met**" if m["target_met"] else "❌ **not met**"
    a(f"Charter target (≥{m['accuracy_target']}% overall accuracy): {target} by the hybrid pipeline.")
    a("")
    a("## Per-class Precision / Recall / F1")
    a("")
    for name, data in (("Hybrid (LLM)", h), ("VADER baseline", v)):
        a(f"### {name}")
        a("")
        a("| Class | Precision | Recall | F1 | Support |")
        a("|---|---|---|---|---|")
        for c in CLASSES:
            p = data["prf"][c]
            a(f"| {c} | {p['precision']} | {p['recall']} | {p['f1']} | {p['support']} |")
        a(f"| **macro-F1** | | | **{data['prf']['macro']['f1']}** | |")
        a("")
    a("## Per-language Accuracy (where the baseline breaks)")
    a("")
    a("| Language | n | VADER | Hybrid | Δ |")
    a("|---|---|---|---|---|")
    for lang, d in ev["per_language"].items():
        a(f"| {lang} | {d['n']} | {d['vader']}% | {d['hybrid']}% | {round(d['hybrid'] - d['vader'], 1):+}% |")
    a("")
    a("## Per-aspect Accuracy (ABSA — VADER cannot do this)")
    a("")
    a("> ⚠️ **Provisional.** The aspect gold labels are currently seeded from the LLM's "
      "own output, so the hybrid column is circular (it scores against itself) and reads "
      "~100%. Treat it as an upper bound only; it becomes meaningful once the team "
      "independently verifies `gold_aspects` in `test_set.json`. The VADER column "
      "(document label broadcast to each aspect) is already meaningful and shows the "
      "baseline cannot do aspect-level analysis. This table is excluded from the headline "
      "chart for that reason.")
    a("")
    a("| Aspect | n | VADER (broadcast) | Hybrid | Δ |")
    a("|---|---|---|---|---|")
    for aspect in ASPECTS:
        d = ev["per_aspect"][aspect]
        a(f"| {aspect} | {d['n']} | {d['vader']}% | {d['hybrid']}% | {round(d['hybrid'] - d['vader'], 1):+}% |")
    a("")
    a("## Confusion Matrices")
    a("")
    a("### Hybrid (LLM)")
    a("")
    lines.extend(_conf_table(h["confusion"]))
    a("")
    a("### VADER baseline")
    a("")
    lines.extend(_conf_table(v["confusion"]))
    a("")
    a("## Notes")
    a("")
    a("- The hybrid pipeline's advantage concentrates on Tagalog/Cebuano reviews, "
      "where VADER's English lexicon has no coverage — the empirical justification "
      "for the hybrid architecture (starter.MD §2–3).")
    if not m["test_set_verified"]:
        a("- ⚠️ These numbers use **candidate** (rating-anchored) gold labels. Have the "
          "team verify `test_set.json`, set `meta.verified=true`, and re-run for the "
          "final figures.")
    a("")
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not TEST_SET_PATH.is_file():
        raise SystemExit(
            f"[evaluate] {TEST_SET_PATH} not found — run build_test_set.py first."
        )
    ev = evaluate()
    write_results_json(ev)
    write_results_md(ev)

    h, v, m = ev["hybrid"], ev["vader"], ev["meta"]
    print(f"[evaluate] scored {m['n_scored']}/{m['n']} reviews "
          f"({m['missing_predictions']} missing predictions)")
    print(f"[evaluate] VADER  overall accuracy: {v['overall_accuracy']}%  "
          f"(macro-F1 {v['prf']['macro']['f1']})")
    print(f"[evaluate] Hybrid overall accuracy: {h['overall_accuracy']}%  "
          f"(macro-F1 {h['prf']['macro']['f1']})")
    print(f"[evaluate] delta = {round(h['overall_accuracy'] - v['overall_accuracy'], 1):+}%")
    print(f"[evaluate] charter >={m['accuracy_target']}% target: "
          f"{'MET' if m['target_met'] else 'NOT met'}")
    if not m["test_set_verified"]:
        print("[evaluate] NOTE: candidate labels — verify test_set.json then re-run.")
    print(f"[evaluate] wrote {RESULTS_MD.name} + {RESULTS_JSON.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
