# RestoPulse — Presentation Slides (content)

Slide-by-slide content. Each `---` is a new slide. Copy the bullets into
PowerPoint / Google Slides / Canva. Speaker notes are in _italics_.

---

## Slide 1 — Title

# RestoPulse
### Multilingual Restaurant Review Sentiment Analysis

Aspect-Based Sentiment Analysis for English / Tagalog / Cebuano reviews

[Team names] · [Course / Section] · 2026

_Opening line: "RestoPulse reads restaurant reviews the way customers actually
write them — in a mix of English, Tagalog, and Cebuano — and tells owners not just
the rating, but what people loved and complained about."_

---

## Slide 2 — The Problem

- Restaurants get hundreds of reviews; reading them all is impractical.
- A star rating doesn't say **why** — was it the food? the service? the price?
- Filipino reviews are **multilingual & code-mixed** ("Lami ang food pero mabagal ang service").
- Standard English sentiment tools **can't read** Tagalog/Cebuano.

_Problem in one sentence: how do you measure sentiment, per aspect, across languages?_

---

## Slide 3 — Our Solution

**A dashboard powered by a hybrid NLP pipeline.**

- Scrapes real Google reviews → analyzes each one → visualizes the results.
- **Aspect-Based Sentiment Analysis (ABSA):** food, service, ambiance, price, cleanliness.
- Handles English, Tagalog, and Cebuano natively — no translation.
- Runs **offline** for the demo (all results cached).

---

## Slide 4 — The Dataset

| | |
|---|---|
| Reviews | **390** |
| Restaurants | 10 |
| Cities | Cagayan de Oro, Iligan, Marawi |
| Languages | English 346 · Tagalog 28 · Cebuano 14 |
| Sentiment | 313 positive · 22 neutral · 55 negative |

_Real data, scraped once with a free self-hosted scraper — no paid API._

---

## Slide 5 — System Architecture

**3-layer web application:**

- **Frontend** — React + TypeScript dashboard (5 pages)
- **Backend** — Flask JSON API
- **Data** — SQLite

> Key rule: the LLM runs at **ingest time**, not on every request. The dashboard
> reads cached results, so it's fast and works without internet.

_(Show the architecture diagram from REPORT.md §5.)_

---

## Slide 6 — The Hybrid NLP Pipeline (the core)

**6 components — 5 classical NLP + 1 LLM:**

1. NLTK preprocessing
2. Language detection (langdetect + regional heuristic)
3. **LLM ABSA engine** (Llama 3.1 8B via Groq) ← sentiment authority
4. Rule-based aspect validator (multilingual keyword dictionary)
5. TF-IDF keyword extraction (scikit-learn)
6. VADER baseline (for evaluation only)

_(Show the pipeline diagram from REPORT.md §6.)_

_Emphasize: "The LLM is one component. We built the pipeline, the multilingual
aspect taxonomy, the prompt design, and the evaluation."_

---

## Slide 7 — Why Hybrid?

| Approach | Verdict |
|---|---|
| English-only VADER | ❌ Can't read Tagalog/Cebuano |
| Translate-then-analyze | ❌ Loses nuance |
| Pure LLM | ⚠️ Accurate but no baseline to justify it |
| **Hybrid (LLM + classical)** | ✅ Accurate, multilingual, **and** measurable |

---

## Slide 8 — The Dashboard (demo lead-in)

- **Dashboard** — sentiment overview, aspects, trends, top issues
- **Reviews** — filter by sentiment / aspect / language, with evidence
- **Analytics** — aspect performance + pipeline evaluation
- **Compare** — restaurants ranked fairly (Bayesian-adjusted)
- **Live Analyze** — paste a review, get instant ABSA

_→ Switch to the live demo here. See DEMO.md._

---

## Slide 9 — Evaluation: Hybrid vs Baseline

**Tested on 50 human-verified reviews:**

| Pipeline | Overall accuracy |
|---|---|
| VADER baseline | 58.0% |
| **Hybrid (LLM)** | **78.0%** |
| **Improvement** | **+20 points** |

Hybrid wins on **every language** — biggest gap on Tagalog (85% vs 65%).

_This is the empirical proof the hybrid approach was the right call._

---

## Slide 10 — Honest Limitations

- Test set is small (50) → ~80% is best read as "clearly above the 58% baseline."
- Aspect-level accuracy not yet independently validated.
- Dashboard filters scope the summary, not yet every chart.
- No Ilocano in the corpus (all restaurants are in Mindanao).

_Showing limitations honestly is a strength, not a weakness._

---

## Slide 11 — Conclusion

- Built an **end-to-end** system: scraping → hybrid NLP → dashboard → evaluation.
- A hybrid pipeline reads multilingual Filipino reviews **far better** than a
  traditional baseline (**78% vs 58%**).
- Reproducible and offline-capable.

**Future work:** larger test set, validated ABSA, multi-tenant deployment.

---

## Slide 12 — Thank You / Questions

**RestoPulse** — Review Intelligence

[Team names] · [contact / repo link]

_(Have DEMO.md and QA.md open in case of follow-ups.)_
