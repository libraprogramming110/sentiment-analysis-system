# RestoPulse System Design Plan

## Context

RestoPulse is a 26-day student capstone (Apr 23 – May 19, 2026) that turns scraped restaurant reviews into a sentiment + aspect-mining dashboard. The project directory is currently empty (only the charter PDF and a blank `starter.MD`), so this plan covers the full system from scratch.

**User decisions locked in:**
- **Languages:** English, Filipino, Cebuano, Ilocano (corpus turned out English-dominant + Cebuano + Tagalog; ~0 Ilocano since all restaurants are in Mindanao)
- **Data source:** Scraped Google Reviews from **10 real restaurants across 3 Mindanao cities** (Cagayan de Oro, Iligan, Marawi) — 390 reviews total. (Charter floor was 1; we exceeded it to deliver the comparison feature.)
- **Sentiment depth:** Aspect-Based Sentiment Analysis (ABSA) — per-aspect scoring (food, service, ambiance, price, cleanliness)
- **Auth:** None — single-tenant demo, no login page, no Users table
- **NLP approach:** **Hybrid pipeline** — open-source LLM (**Llama 3.1 8B Instant** via Groq free tier) as the multilingual sentiment engine, combined with traditional NLP components (NLTK preprocessing, VADER baseline, keyword extraction, rule-based aspect tagging) for defense-readiness and rigorous evaluation.
- **Frontend stack:** **React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts** (upgraded from the original Bootstrap plan so we can use the 21st-dev Magic MCP for high-quality components and a modern SaaS design language). Flask is a JSON-only API.

The biggest design driver is **multi-language Filipino/Cebuano/Ilocano support**, which rules out pure VADER. The hybrid approach gives state-of-the-art accuracy *and* visible traditional NLP components for the panel defense.

> **Model note:** the plan originally specified Llama **3.3 70B**, but batch-ingesting 390 reviews exhausted Groq's free-tier **100k-tokens/day** limit on that model (only ~245 reviews got through). We switched to **Llama 3.1 8B Instant** (~500k tokens/day) + trimmed the prompt, and re-ingested all 390 cleanly. Trade-off: 8B's language detection is weaker, so we re-derive `detected_language` with langdetect + a regional heuristic instead of trusting the LLM's guess.

---

## ✅ Current Status & Session Progress

**Overall: the system is functional end-to-end.** Frontend + backend + DB + NLP pipeline all work on real scraped data. Only the formal evaluation harness (Phase 4) and docs/demo (Phase 5) remain.

### What's live right now
- **Backend:** Flask on `127.0.0.1:5000`, Groq key loaded, SQLite with **390 analyzed reviews** across 10 restaurants / 3 cities.
- **Frontend:** React on `127.0.0.1:5173`, all **5 pages live on real API data** (Dashboard, Reviews, Analytics, Compare, Live Analyze).
- **Data snapshot:** 313 positive / 22 neutral / 55 negative; avg rating 4.5; languages English 346 / Tagalog 28 / Cebuano 14 / unknown 2.

### Done this session (chronological)
1. Built Flask backend skeleton (CORS, health check, stub routes) + verified frontend↔backend.
2. Built SQLite schema + `db/repo.py`; seeded sample data; wired Dashboard + Reviews to live API.
3. Chose self-hosted scraper (`georgekhananaev/google-reviews-scraper-pro`); built wrapper driving **Brave**; solved Chrome-missing, cp1252 Unicode crash, and the Windows colon/ADS export bug (read `scrape.db` directly).
4. Scraped **390 reviews** (10 restaurants, capped 80 each) across CDO / Iligan / Marawi with a `city` tag.
5. Built the full **hybrid NLP pipeline** (preprocess, langdetect, Groq LLM, rule aspects, TF-IDF, VADER baseline) + `scripts/ingest.py` (resumable, throttled).
6. Hit Groq 70B daily-token limit at ~245 reviews → switched to **Llama 3.1 8B**, trimmed prompt, re-ingested all 390.
7. Fixed language-detection noise (8B over-predicted Ilocano) via `scripts/relabel_languages.py` (no tokens).
8. Wired **Analytics** + **Live Analyze** to live API; fixed health-score >100 bug; fixed stale model labels.
9. Built **Compare page** — city summary, ranked chart, leaderboard with **Bayesian-shrinkage** ranking + city filter + small-sample badges; fixed the sidebar workspace chip.
10. Added **pagination** to Reviews (15/page).
11. Updated this plan document to match reality.

### Remaining (next sessions)
- **P4 — Evaluation harness:** hand-label ~50 reviews → `evaluation/test_set.json`; build `evaluation/evaluate.py` to run hybrid vs VADER; write `results.md`; fills the Analytics "Pipeline Evaluation" tab and proves the ≥80% accuracy requirement.
- **P5 — Docs & demo:** SRS, system-design diagrams, slides, defense rehearsal.
- **Minor:** smoke tests (`tests/test_pipeline.py`); optional ingest improvement (commit-as-you-go for live progress).

---

## 1. Hybrid NLP Pipeline (the critical decision)

### Architecture: 6 visible NLP components, LLM is one of them

```
Raw Review Text
    ↓
[1] NLTK Preprocessing       ← traditional NLP (tokenize, clean, normalize)
    ↓
[2] langdetect               ← traditional NLP (n-gram language ID)
    ↓
[3] LLM Sentiment Engine     ← modern NLP (Llama 3.1 8B Instant via Groq)
    │   Single structured prompt returns:
    │   { overall_sentiment, aspects[], keywords[], language, confidence }
    ↓
[4] Rule-based Aspect Validator  ← traditional NLP (keyword dictionary)
    │   Cross-checks LLM's aspect output against curated multilingual
    │   keyword dictionary; flags low-confidence cases
    ↓
[5] TF-IDF Keyword Extraction    ← traditional NLP (statistical NLP)
    │   Independent keyword extraction across the corpus (sklearn)
    ↓
[6] VADER Baseline (parallel)    ← traditional NLP (lexicon + rules)
    │   Run on cleaned text; used ONLY for evaluation comparison,
    │   never shown in dashboard
    ↓
Aggregate → SQLite
```

> **Language detection refinement (post-build):** langdetect can't tell Cebuano/Ilocano apart (both look like Tagalog), and Llama 3.1 8B over-predicted Ilocano. We added `nlp/language.py` with a regional-marker heuristic + a `scripts/relabel_languages.py` pass that re-derives `detected_language` from langdetect + heuristic (no LLM, no tokens). Result: English 346 / Tagalog 28 / Cebuano 14 / unknown 2 / Ilocano 0 — accurate for a Mindanao corpus.

### Why hybrid (LLM + traditional) over alternatives

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| **Hybrid LLM + traditional NLP** | Native multilingual (no translation loss), high accuracy, visible traditional NLP for defense, rigorous evaluation story | API key management, internet needed during batch processing (not demo) | ✅ **Chosen** |
| Pure LLM | Simplest code | Panel may push back ("you just called an API"); no comparison baseline | Defense risk |
| Translate-then-VADER | All-traditional, no API | Translation loses nuance, weaker on Cebuano/Ilocano, lower accuracy | Lower quality |
| Multilingual transformer (XLM-R) local | No API dependency | 500MB model, slow CPU, complex setup | Too heavy |
| Per-language lexicons | Most authentic | Building Cebuano/Ilocano lexicons = research-paper scope | Out of scope |

### LLM provider choice: **Groq + Llama 3.1 8B Instant** (was 3.3 70B)

- **Free tier:** 30 req/min, **~500k tokens/day** — enough to batch all 390 reviews in one pass (70B's 100k/day cap only allowed ~245)
- **Speed:** very fast, low latency — good for the Live Analyze demo
- **Open-source model:** Llama 3.1 is Meta's open-weight model — important for defense ("we use an open-source LLM, not a proprietary API")
- **Fallback:** Google Gemini 2.0 Flash (1500 req/day free) if Groq is down
- **Determinism:** `temperature=0` + cache raw LLM response in DB (`llm_raw_response`) → demo is reproducible without internet
- **Throttle:** `nlp/llm.py` has a token-bucket limiter (~28 req/min) + 1 stricter retry on malformed JSON

### LLM prompt design (structured JSON output)

```
SYSTEM: You analyze restaurant reviews in English, Filipino (Tagalog),
Cebuano, or Ilocano. Return ONLY valid JSON, no prose.

USER: Review: "{review_text}"

Return:
{
  "language": "en|tl|ceb|ilo|other",
  "overall_sentiment": "positive|neutral|negative",
  "overall_confidence": 0.0-1.0,
  "aspects": [
    {"aspect": "food|service|ambiance|price|cleanliness",
     "sentiment": "positive|neutral|negative",
     "evidence": "<quoted phrase from review>"}
  ],
  "keywords": ["...", "..."]
}
```

### Aspect keyword dictionary (still needed for component [4])

Curated multilingual dictionary (English + Filipino at launch, Cebuano/Ilocano added during P3):

```python
ASPECT_KEYWORDS = {
  "food":       ["food", "taste", "dish", "masarap", "lasa", "ulam", "lami", ...],
  "service":    ["service", "staff", "waiter", "mabagal", "mabilis", "serbisyo", ...],
  "ambiance":   ["ambiance", "place", "atmosphere", "lugar", "maingay", ...],
  "price":      ["price", "expensive", "cheap", "mahal", "mura", "presyo", ...],
  "cleanliness":["clean", "dirty", "malinis", "marumi", ...],
}
```

This is used to (a) validate LLM aspect output, (b) demonstrate traditional NLP work to the panel, (c) provide a fallback if the LLM misses an aspect.

---

## 2. Defense Strategy (NLP framing for the panel)

This is a **decision-support system** that applies a **hybrid NLP pipeline** — not "an NLP project that uses an API." Frame the contribution as the **integration, multilingual support, aspect taxonomy, dashboard, and evaluation** — not novel NLP research.

### Opening defense statement

> "RestoPulse implements a multi-stage hybrid NLP pipeline that combines traditional rule-based and lexicon-based techniques (NLTK, VADER, TF-IDF, keyword dictionaries) with a state-of-the-art transformer-based open-source language model (Llama 3.3) to handle the multilingual nature of Filipino restaurant reviews."

### Anticipated questions + canned answers

| Question | Answer |
|---|---|
| "Where is the NLP?" | Point to the 6-component diagram. NLTK preprocessing, langdetect, rule-based aspect tagging, TF-IDF keyword extraction, VADER baseline, AND the LLM — all are NLP techniques. |
| "Did you really build the NLP?" | "We built the pipeline architecture, the multilingual aspect taxonomy with 60+ Filipino/Cebuano keywords, the prompt engineering for structured ABSA output, the evaluation framework with VADER baseline comparison, and the integration layer. The LLM is one component." |
| "Why not just VADER?" | "We evaluated VADER as a baseline. Section 3 shows our comparison: VADER on translated text achieved [X]%, hybrid pipeline achieved [Y]%, with the gap concentrated on Filipino and Cebuano reviews where translation introduces semantic loss." |
| "Isn't using an LLM cheating?" | "LLMs are the current state-of-the-art in NLP, used in academic NLP research. Llama 3.3 is Meta's open-source model, not a proprietary black box. Selecting the appropriate tool for a multilingual problem is an engineering decision we documented and validated empirically." |
| "What if the API is down during defense?" | "All LLM responses are cached in SQLite at processing time. The demo runs entirely from local DB — no internet required." |

---

## 3. Evaluation Methodology (the +10% grade move)

Run **both pipelines** in parallel, compare empirically. This is what real NLP evaluation looks like.

### Test set construction

- Hand-label **50 reviews** from the scraped corpus (mix: ~20 Filipino, ~15 English, ~10 Cebuano, ~5 Ilocano)
- Each labeled with: ground-truth overall sentiment + ground-truth aspect sentiments
- Stored in `evaluation/test_set.json` (gold standard)

### Metrics computed per pipeline

- **Overall sentiment:** accuracy, precision/recall/F1 per class (positive/neutral/negative)
- **Aspect detection:** precision, recall, F1 per aspect
- **Aspect sentiment:** accuracy per aspect
- **Confusion matrix** for both pipelines
- **Per-language breakdown** (where each pipeline fails)

### Deliverable

`evaluation/results.md` — comparison table:

| Metric | VADER baseline | Hybrid (LLM) | Δ |
|---|---|---|---|
| Overall accuracy | XX% | YY% | +Z% |
| F1 (positive) | ... | ... | ... |
| F1 (negative) | ... | ... | ... |
| Filipino accuracy | ... | ... | ... |
| Cebuano accuracy | ... | ... | ... |

This satisfies the charter's 80% accuracy success metric *and* gives a defensible empirical justification for the architecture choice.

---

## 4. Data Acquisition (Scraping Strategy)

### Recommendation: **One-shot scrape → CSV, not live API** ✅ Done

Scraped once and committed the CSV. Do NOT scrape at runtime during the demo (network risk, TOS risk).

**Tool chosen:** `georgekhananaev/google-reviews-scraper-pro` (Python/SeleniumBase, free, no signup) — vendored under `backend/scraper/vendor/` in its own `.venv-scraper`. Driven via a thin wrapper `backend/scraper/google_scraper.py`.
- Evaluated SerpAPI / Apify / Outscraper first — all needed signup or (Outscraper) a card. The self-hosted scraper needs none.
- Drives **Brave** (not Chrome) via the vendor's `CHROME_BIN` hook — `_find_browser()` auto-detects Brave/Chrome/Edge.
- Reads the vendor's `scrape.db` **directly** (bypasses its CSV export, which breaks on Windows because Google place_ids contain a colon → NTFS alternate-data-stream bug).
- `PYTHONIOENCODING=utf-8` set for the child process (vendor's progress spinner crashed on cp1252).

**Actual result:** 10 restaurants × ≤80 newest reviews = **390 reviews** across Cagayan de Oro (192), Iligan (149), Marawi (49). Capped at 80/restaurant after an uncapped run pulled 600+ from one place.

**Canonical CSV schema (`data/reviews_raw.csv`):** `external_id, restaurant_name, restaurant_external_id, city, author, rating, original_text, translated_text, date_added, source` — produced by `scraper/adapter.py:normalize_sqlite()`.

**Ethics/scope note for documentation:** disclose scraping method, anonymize reviewer names, use only publicly visible reviews, academic-use disclaimer.

---

## 5. System Architecture (3-layer)

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (frontend/)             │
│  React 19 + TypeScript + Vite               │
│  Tailwind + shadcn/ui + Recharts            │
│  Pages: Dashboard, Reviews, Analytics,      │
│         Compare, Live Analyze               │
└─────────────────────────────────────────────┘
              ↓ fetch() — JSON
┌─────────────────────────────────────────────┐
│  Application Layer (backend/)               │
│  Flask — JSON API only (no templates)       │
│  Routes → Hybrid NLP Pipeline → DB          │
│  Modules: nlp/, scraper/, db/, evaluation/  │
└─────────────────────────────────────────────┘
              ↓ sqlite3
┌─────────────────────────────────────────────┐
│  Data Layer                                 │
│  SQLite (restopulse.db) + seed CSV + cache  │
└─────────────────────────────────────────────┘
```

**Key design rule:** LLM calls happen at **batch processing time** (when ingesting scraped CSV), NOT at request time. Dashboard reads from SQLite only — fully offline-capable demo.

---

## 6. Database Schema (revised — hybrid-aware)

```sql
CREATE TABLE restaurants (
  restaurant_id   INTEGER PRIMARY KEY,
  name            TEXT NOT NULL,
  external_id     TEXT UNIQUE,                 -- Google place_id (re-ingest dedup)
  city            TEXT,                          -- assigned in scraper config (CDO/Iligan/Marawi)
  source_url      TEXT
);

CREATE TABLE reviews (
  review_id          INTEGER PRIMARY KEY,
  restaurant_id      INTEGER REFERENCES restaurants(restaurant_id),
  external_id        TEXT UNIQUE,               -- Google review_id (re-ingest dedup)
  author             TEXT,
  original_text      TEXT NOT NULL,
  translated_text    TEXT,                      -- for VADER baseline only
  detected_language  TEXT,                      -- 'en','tl','ceb','ilo','unknown'
  rating             INTEGER,                   -- 1–5 from Google
  overall_sentiment  TEXT,                      -- 'positive'|'neutral'|'negative' (from LLM)
  overall_score      REAL,                      -- LLM confidence 0..1
  vader_sentiment    TEXT,                      -- baseline comparison
  vader_score        REAL,                      -- VADER compound, -1..1
  llm_raw_response   TEXT,                      -- cached LLM JSON (reproducibility)
  date_added         DATE,
  source             TEXT
);

CREATE TABLE aspect_sentiments (
  id              INTEGER PRIMARY KEY,
  review_id       INTEGER REFERENCES reviews(review_id),
  aspect          TEXT,                          -- 'food'|'service'|'ambiance'|'price'|'cleanliness'
  sentiment       TEXT,                          -- 'positive'|'neutral'|'negative'
  evidence        TEXT,                          -- quoted sentence/phrase from review
  source_method   TEXT                           -- 'llm'|'rule'|'both' (audit trail)
);

CREATE TABLE keywords (
  keyword_id    INTEGER PRIMARY KEY,
  review_id     INTEGER REFERENCES reviews(review_id),
  keyword       TEXT,
  frequency     INTEGER,
  tf_idf_score  REAL                             -- from TF-IDF component
);
```

**Changes vs charter:**
- No Users table (auth removed)
- Added `aspect_sentiments` (ABSA needs per-aspect rows)
- Added `original_text` + `translated_text` + `detected_language` for multilingual
- Added `vader_sentiment` + `vader_score` for baseline comparison
- Added `llm_raw_response` for reproducibility/auditability
- Added `source_method` on aspects to show LLM vs rule contribution
- Added `restaurants.city` + `restaurants.external_id` + `reviews.external_id` (city clustering for Compare page; external_ids make re-ingest idempotent/resumable)

---

## 7. Project Structure

```
sentiment-analysis-system/
├── starter.MD                       # this plan
├── RestoPulse Sentiment Analysis.pdf
│
├── frontend/                        # ✅ React SPA — built in this iteration
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                  # Router: /, /reviews, /analytics, /compare, /analyze
│       ├── index.css                # Tailwind + design tokens (light/dark)
│       ├── lib/
│       │   ├── utils.ts             # cn() helper
│       │   ├── api.ts               # ✅ typed fetch client + useApi() hook
│       │   └── mockData.ts          # graceful-fallback data if API is down
│       ├── components/
│       │   ├── ui/                  # shadcn primitives
│       │   ├── brand/Logo.tsx       # animated RestoPulse mark + wordmark
│       │   ├── layout/              # Sidebar (+ WorkspaceChip), Header, AppShell
│       │   └── widgets/             # StatCard, SentimentDonut, AspectBars,
│       │                            # TrendChart, TopKeywords, TopIssues,
│       │                            # LanguageBreakdown
│       └── pages/
│           ├── DashboardPage.tsx    # ✅ live
│           ├── ReviewsPage.tsx      # ✅ live + pagination (15/page)
│           ├── AnalyticsPage.tsx    # ✅ live (4 tabs; eval tab shows "pending")
│           ├── ComparePage.tsx      # ✅ live — Bayesian ranking + city filter
│           └── AnalyzePage.tsx      # ✅ live — real Groq /api/analyze
│
└── backend/                         # ✅ Flask API — built
    ├── app.py                       # Flask entrypoint, CORS, init_db
    ├── requirements.txt
    ├── .env                         # GROQ_API_KEY + GROQ_MODEL (gitignored)
    ├── .env.example
    ├── restopulse.db                # SQLite (390 reviews ingested), gitignored
    ├── data/
    │   ├── reviews_raw.csv          # ✅ 390 scraped reviews
    │   └── aspect_keywords.json     # ✅ multilingual aspect dictionary
    ├── scraper/
    │   ├── google_scraper.py        # ✅ wrapper (Brave, reads vendor scrape.db)
    │   ├── adapter.py               # ✅ normalize_sqlite() → canonical CSV
    │   ├── config.yaml              # ✅ 10 restaurants, max_reviews:80
    │   └── vendor/google-reviews-scraper-pro/   # vendored scraper + .venv-scraper
    ├── nlp/
    │   ├── pipeline.py              # ✅ orchestrates hybrid pipeline
    │   ├── preprocess.py            # ✅ NLTK cleaning, tokenization
    │   ├── language.py              # ✅ langdetect + regional heuristic + reconcile
    │   ├── llm.py                   # ✅ Groq + Llama 3.1 8B, throttle, retry
    │   ├── aspects.py               # ✅ rule-based aspect validator
    │   ├── keywords.py              # ✅ TF-IDF (sklearn)
    │   └── baseline_vader.py        # ✅ VADER baseline
    ├── db/
    │   ├── schema.sql               # ✅ (city + external_id added)
    │   └── repo.py                  # ✅ CRUD + dashboard/compare queries
    ├── routes/
    │   ├── dashboard.py             # ✅ /api/summary, /trend, /issues, /languages, /restaurants
    │   ├── reviews.py               # ✅ /api/reviews (filters)
    │   ├── analytics.py             # ✅ /api/aspects, /keywords, /evaluation (pending stub)
    │   └── analyze.py               # ✅ POST /api/analyze (live LLM)
    ├── scripts/
    │   ├── ingest.py                # ✅ CSV → pipeline → SQLite (resumable, throttled)
    │   ├── seed.py                  # ✅ sample-data seeder (early dev)
    │   └── relabel_languages.py     # ✅ re-derive detected_language (no LLM)
    ├── evaluation/                  # ⏳ to build (Phase 4)
    │   ├── test_set.json
    │   ├── evaluate.py
    │   └── results.md
    └── tests/test_pipeline.py       # ⏳ to build
```

---

## 8. Flask Routes (API contracts)

Flask is **JSON-only** (no HTML); the React app serves all pages.

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `{status, service, time, groq_key_loaded}` |
| GET | `/api/summary?restaurant_id=&city=` | `{total, positive, neutral, negative, avgRating, ...}` |
| GET | `/api/trend` | `{trend: [{day, positive, neutral, negative}]}` |
| GET | `/api/issues` | `{issues: [{issue, mentions, aspect}]}` (Top 3) |
| GET | `/api/languages` | `{languages: [{lang, count}]}` |
| GET | `/api/restaurants` | `{restaurants: [{id, name, city, reviews, avg_rating, pos/neu/neg}]}` (Compare) |
| GET | `/api/aspects` | `{aspects: [{aspect, positive, neutral, negative}]}` |
| GET | `/api/keywords?limit=` | `{keywords: [{word, count, sentiment}]}` |
| GET | `/api/reviews?sentiment=&aspect=&lang=&q=&limit=` | `{reviews: [...], total}` |
| GET | `/api/evaluation` | `{vader, hybrid, _pending}` — stub until Phase 4 |
| POST | `/api/analyze` | `{text}` → live LLM ABSA result (requires internet) |

---

## 9. Dashboard Pages (5 pages, login removed) — ✅ all live on real data

1. **Dashboard (`/`)** — 4 stat cards, sentiment donut, aspect-bars, trend area chart, top keywords, **Top 3 Issues Detected**, language mix. Live from `/api/summary|trend|issues|languages|aspects|keywords`.
2. **Reviews (`/reviews`)** — Filterable list (search + sentiment + aspect + language), each row shows avatar, stars, language badge, sentiment badge, original + translated text, aspect chips with evidence tooltips, expand for full ABSA. **Paginated (15/page)** with page-window controls.
3. **Analytics (`/analytics`)** — 4 tabs: (a) Aspect Performance (bar + radar + per-aspect cards, **health score = net sentiment mapped 0–100, clamped**), (b) Keyword Insights, (c) Rating vs Sentiment scatter, (d) **Pipeline Evaluation** — shows "pending" until `evaluation/evaluate.py` runs.
4. **Compare (`/compare`)** — NEW. City summary cards (CDO/Iligan/Marawi), ranked sentiment bar chart, and a **leaderboard** ranked by **Bayesian-shrinkage-adjusted** health score (IMDb method, so a 9-review place can't out-rank a 50-review one). **City filter** (All / each city) + "small sample" badges for <15-review restaurants. Delivers the charter's "+10% restaurant comparison" feature.
5. **Live Analyze (`/analyze`)** — Two-pane: paste/select a review → "Analyze with Hybrid Pipeline" → live Groq call returns detected language, overall sentiment + confidence, per-aspect ABSA cards with evidence, and keywords. Shows a clear error if backend/key is unavailable.

### Brand & design tokens

- **Wordmark:** `Resto` (foreground) + `Pulse` (brand indigo). Tagline: "Review Intelligence."
- **Logo mark:** rounded indigo→cyan gradient square with a white pulse-line glyph, surrounded by an animated pulse ring.
- **Palette:** Primary indigo `hsl(239 84% 60%)`, brand-accent cyan `hsl(188 94% 43%)`, sentiment green/neutral-slate/rose for positive/neutral/negative. Full dark-mode token set.
- **Typography:** Inter (UI) + JetBrains Mono (numbers/code).
- **Density:** modern SaaS — tight type scale, lots of `tabular-nums`, restrained shadows, subtle borders, animated micro-details (live status pulse, hover lifts).

---

## 10. Phased Build Order (mapped to WFP phases)

| Phase | Deliverable | Status |
|---|---|---|
| **P1a: Plan + UI scaffold** | This plan, React/Vite/Tailwind/shadcn frontend, all pages on mock data | ✅ Done |
| **P1b: Backend skeleton** | Flask + CORS, `requirements.txt`, `.env`, Groq key wired, stub routes | ✅ Done |
| **P2: Data + Schema** | Scraper built (Brave), **390 reviews scraped**, SQLite schema, aspect keyword dictionary | ✅ Done (test_set.json still pending) |
| **P3a: Hybrid NLP Engine** | All `nlp/*` modules, `scripts/ingest.py` runs CSV → DB with LLM + VADER both populated | ✅ Done |
| **P3b: Wire frontend to API** | All 5 pages call `/api/...`; mockData kept as graceful fallback | ✅ Done |
| **P4: Test + Evaluate** | `evaluation/evaluate.py` → `results.md`, ≥80% target, fills the "pending" eval tab | ⏳ **Next / remaining** |
| **P5: Docs + Demo** | SRS, slides, demo rehearsal, defense Q&A practice | ⏳ Pending |

**Bonus work delivered beyond the original plan:** Compare page (city clustering + Bayesian-adjusted leaderboard), Reviews pagination, language-detection relabel pass, small-sample badges.

---

## 11. Critical Files to Create

- `app.py` — Flask app factory + route registration
- `nlp/pipeline.py` — single `process_review(text) -> dict` orchestrating preprocess → langdetect → LLM → aspect validate → keyword extract → VADER baseline
- `nlp/llm.py` — Groq client wrapper, prompt template, JSON schema validation, retry logic, response caching
- `nlp/aspects.py` — loads `data/aspect_keywords.json`, provides `validate_aspects(llm_aspects, text) -> list[dict]`
- `nlp/baseline_vader.py` — `vader_sentiment(translated_text) -> dict` (evaluation only)
- `db/schema.sql` — DDL above; run on first launch via `db/repo.py:init_db()`
- `data/aspect_keywords.json` — multilingual aspect dictionary
- `scraper/google_scraper.py` — one-shot script
- `scripts/ingest.py` — batch processor (CSV → pipeline → DB)
- `evaluation/test_set.json` — 50 hand-labeled reviews
- `evaluation/evaluate.py` — runs both pipelines on test set, computes metrics, writes `results.md`

---

## 12. Verification Plan

**Unit:**
- `pytest tests/test_pipeline.py` — smoke test: `process_review("Masarap ang pagkain pero mabagal ang serbisyo")` returns expected ABSA structure
- LLM JSON schema validation — every response parses cleanly

**Evaluation (the big one):**
- `python evaluation/evaluate.py` runs both pipelines on `test_set.json`, writes `results.md`
- Hybrid pipeline accuracy ≥ 80% (charter success metric)
- Hybrid pipeline outperforms VADER baseline on Filipino + Cebuano subsets

**Integration:**
- `python scripts/ingest.py data/reviews_raw.csv` — populates SQLite end-to-end
- `python -c "from nlp.pipeline import process_review; print(process_review('Masarap ang pagkain pero mabagal ang serbisyo'))"` returns `food=positive, service=negative`

**End-to-end:**
- `cd frontend && npm run dev` → open `http://127.0.0.1:5173`
- `cd backend && flask run` → JSON API on `http://127.0.0.1:5000`
- Dashboard loads with charts populated **with no internet** (offline DB demo)
- Reviews page filters work (filter by aspect=service, sentiment=negative, lang=tl)
- Analytics page shows aspect breakdown + pipeline comparison panel
- POST a manual review via `/api/analyze` → live LLM call returns ABSA result (online-only feature)

**Frontend smoke (already passing):**
- `cd frontend && npx tsc --noEmit` — type check clean
- `npx vite build` — production bundle builds cleanly (~833 kB JS / 28 kB CSS)
- `npx vite` → server responds on `http://127.0.0.1:5173`, all 4 routes render

**Defense readiness:**
- Demo runs from localhost using cached LLM responses — no internet required
- Have a fallback CSV + DB backup if SQLite gets corrupted
- Prepare 3 example reviews in 3 different languages to demo the live `/api/analyze` endpoint
- Print `evaluation/results.md` on a slide — empirical justification for architecture
- Rehearse the canned answers in Section 2

---

## 13. Open Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Panel pushes back on "is this really NLP?" | Section 2 defense framing; 6-component pipeline diagram; evaluation comparison report |
| Groq API down during batch processing | Cached responses in `llm_raw_response` column; Gemini fallback; can re-process incrementally |
| Groq API down during defense | Demo uses cached DB — no live LLM call needed except optional `/api/analyze` endpoint |
| LLM returns malformed JSON | JSON schema validation + 1 retry with stricter prompt; log failures |
| Cebuano/Ilocano accuracy low even for LLM | Document per-language metrics; report honestly; LLM still beats VADER baseline |
| Google Maps blocks scraper | Apify free tier as backup; manual copy-paste of ~100 reviews as last resort |
| Hand-labeling 50 reviews is tedious | Split across 4 team members (12-13 each); use consensus on disagreements |
| API key leaked to git | `.env` in `.gitignore` from day one; `.env.example` checked in instead |



GROQ: <set in backend/.env as GROQ_API_KEY — never commit the real key>
Temp Token: <use a GitHub PAT supplied at push time — never commit it>