# RestoPulse — Pipeline Evaluation Results

_Generated 2026-05-23 · 50 reviews scored (of 50 in the test set)._

## Methodology

- **Test set:** 50 reviews, stratified by language (Cebuano/Tagalog oversampled vs their corpus share) and spread across star ratings to avoid majority-class (positive) inflation.
- **Gold labels:** Gold labels human-verified by reading each review TEXT. When review text and star rating conflicted, the TEXT was treated as ground truth (the test set evaluates how systems read text, not how users click stars). Aspect labels left as previously seeded.
- **Human-verified:** yes.
- **Predictions:** read from the cached SQLite DB (no recomputation, zero API tokens) — fully reproducible and offline.
- **VADER baseline:** English-only, lexicon-based. It has no aspect-based output, so for the per-aspect comparison its single document-level label is broadcast to each mentioned aspect.

## Headline: Overall Accuracy

| Pipeline | Overall accuracy | Macro-F1 |
|---|---|---|
| VADER baseline | 58.0% | 0.579 |
| **Hybrid (LLM)** | **78.0%** | **0.687** |
| Δ (hybrid − baseline) | **+20.0%** | — |

Charter target (≥80.0% overall accuracy): ❌ **not met** by the hybrid pipeline.

## Per-class Precision / Recall / F1

### Hybrid (LLM)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| positive | 0.96 | 0.857 | 0.906 | 28 |
| neutral | 0.75 | 0.3 | 0.429 | 10 |
| negative | 0.571 | 1.0 | 0.727 | 12 |
| **macro-F1** | | | **0.687** | |

### VADER baseline

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| positive | 0.714 | 0.536 | 0.612 | 28 |
| neutral | 0.333 | 0.6 | 0.429 | 10 |
| negative | 0.727 | 0.667 | 0.696 | 12 |
| **macro-F1** | | | **0.579** | |

## Per-language Accuracy (where the baseline breaks)

| Language | n | VADER | Hybrid | Δ |
|---|---|---|---|---|
| ceb | 14 | 57.1% | 71.4% | +14.3% |
| en | 14 | 57.1% | 71.4% | +14.3% |
| tl | 20 | 65.0% | 85.0% | +20.0% |
| unknown | 2 | 0.0% | 100.0% | +100.0% |

## Per-aspect Accuracy (ABSA — VADER cannot do this)

> ⚠️ **Provisional.** The aspect gold labels are currently seeded from the LLM's own output, so the hybrid column is circular (it scores against itself) and reads ~100%. Treat it as an upper bound only; it becomes meaningful once the team independently verifies `gold_aspects` in `test_set.json`. The VADER column (document label broadcast to each aspect) is already meaningful and shows the baseline cannot do aspect-level analysis. This table is excluded from the headline chart for that reason.

| Aspect | n | VADER (broadcast) | Hybrid | Δ |
|---|---|---|---|---|
| food | 44 | 54.5% | 100.0% | +45.5% |
| service | 26 | 53.8% | 100.0% | +46.2% |
| ambiance | 22 | 45.5% | 100.0% | +54.5% |
| price | 17 | 29.4% | 100.0% | +70.6% |
| cleanliness | 10 | 20.0% | 100.0% | +80.0% |

## Confusion Matrices

### Hybrid (LLM)

| gold ↓ \ pred → | positive | neutral | negative |
|---|---|---|---|
| **positive** | 24 | 1 | 3 |
| **neutral** | 1 | 3 | 6 |
| **negative** | 0 | 0 | 12 |

### VADER baseline

| gold ↓ \ pred → | positive | neutral | negative |
|---|---|---|---|
| **positive** | 15 | 10 | 3 |
| **neutral** | 4 | 6 | 0 |
| **negative** | 2 | 2 | 8 |

## Notes

- The hybrid pipeline's advantage concentrates on Tagalog/Cebuano reviews, where VADER's English lexicon has no coverage — the empirical justification for the hybrid architecture (starter.MD §2–3).
