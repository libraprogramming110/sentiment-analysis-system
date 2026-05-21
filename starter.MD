# RestoPulse System Design Plan

## Context

RestoPulse is a 26-day student capstone (Apr 23 – May 19, 2026) that turns scraped restaurant reviews into a sentiment + aspect-mining dashboard. The project directory is currently empty (only the charter PDF and a blank `starter.MD`), so this plan covers the full system from scratch.

**User decisions locked in:**
- **Languages:** English, Filipino, Cebuano, Ilocano (most reviews will be Filipino)
- **Data source:** Scraped Google Reviews from 1–3 real Philippine restaurants
- **Sentiment depth:** Aspect-Based Sentiment Analysis (ABSA) — per-aspect scoring (food, service, ambiance, price, cleanliness)
- **Auth:** None — single-tenant demo, no login page, no Users table
- **NLP approach:** **Hybrid pipeline** — open-source LLM (Llama 3.3 via Groq free tier) as the multilingual sentiment engine, combined with traditional NLP components (NLTK preprocessing, VADER baseline, keyword extraction, rule-based aspect tagging) for defense-readiness and rigorous evaluation.
- **Frontend stack:** **React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts** (upgraded from the original Bootstrap plan so we can use the 21st-dev Magic MCP for high-quality components and a modern SaaS design language). Flask becomes a JSON-only API.

The biggest design driver is **multi-language Filipino/Cebuano/Ilocano support**, which rules out pure VADER. The hybrid approach gives state-of-the-art accuracy *and* visible traditional NLP components for the panel defense.

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
[3] LLM Sentiment Engine     ← modern NLP (Llama 3.3 70B via Groq)
    │   Single structured prompt returns:
    │   { overall_sentiment, aspects[], keywords[], language, confidence }
    ↓
[4] Rule-based Aspect Validator  ← traditional NLP (keyword dictionary)
    │   Cross-checks LLM's aspect output against curated multilingual
    │   keyword dictionary; flags low-confidence cases
    ↓
[5] TF-IDF Keyword Extraction    ← traditional NLP (statistical NLP)
    │   Independent keyword extraction across the corpus
    ↓
[6] VADER Baseline (parallel)    ← traditional NLP (lexicon + rules)
    │   Run on English-translated text; used ONLY for evaluation comparison,
    │   never shown in dashboard
    ↓
Aggregate → SQLite
```

### Why hybrid (LLM + traditional) over alternatives

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| **Hybrid LLM + traditional NLP** | Native multilingual (no translation loss), high accuracy, visible traditional NLP for defense, rigorous evaluation story | API key management, internet needed during batch processing (not demo) | ✅ **Chosen** |
| Pure LLM | Simplest code | Panel may push back ("you just called an API"); no comparison baseline | Defense risk |
| Translate-then-VADER | All-traditional, no API | Translation loses nuance, weaker on Cebuano/Ilocano, lower accuracy | Lower quality |
| Multilingual transformer (XLM-R) local | No API dependency | 500MB model, slow CPU, complex setup | Too heavy |
| Per-language lexicons | Most authentic | Building Cebuano/Ilocano lexicons = research-paper scope | Out of scope |

### LLM provider choice: **Groq + Llama 3.3 70B**

- **Free tier:** ~14k requests/day — far more than the 100–300 reviews we need
- **Speed:** ~500 tokens/sec (fastest inference available)
- **Open-source model:** Llama 3.3 is Meta's open-weight model — important for defense ("we use an open-source LLM, not a proprietary API")
- **Fallback:** Google Gemini 2.0 Flash (1500 req/day free) if Groq is down
- **Determinism:** `temperature=0` + cache raw LLM response in DB → demo is reproducible without internet

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

### Recommendation: **One-shot scrape → CSV, not live API**

Scrape once during Phase 2 (May 5–8) and commit the CSV. Do NOT scrape at runtime during the demo (network risk, TOS risk).

**Tool choice:** `google-maps-scraper` (Python, free) or **Apify Google Maps Reviews Scraper** (free tier ~100 reviews) or manual Selenium script.

**Target:** 1–3 restaurants × ~100 reviews each = 100–300 reviews (matches charter's data requirement).

**CSV schema:** `review_id, restaurant_name, review_text, rating, date, source`

**Ethics/scope note for documentation:** disclose scraping method, anonymize reviewer names, use only publicly visible reviews, academic-use disclaimer.

---

## 5. System Architecture (3-layer)

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (frontend/)             │
│  React 19 + TypeScript + Vite               │
│  Tailwind + shadcn/ui + Recharts            │
│  Pages: Dashboard, Reviews, Analytics,      │
│         Live Analyze                        │
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
  source_url      TEXT
);

CREATE TABLE reviews (
  review_id          INTEGER PRIMARY KEY,
  restaurant_id      INTEGER REFERENCES restaurants(restaurant_id),
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
│       ├── App.tsx                  # Router: /, /reviews, /analytics, /analyze
│       ├── index.css                # Tailwind + design tokens (light/dark)
│       ├── lib/
│       │   ├── utils.ts             # cn() helper
│       │   └── mockData.ts          # placeholder data (replace with API)
│       ├── components/
│       │   ├── ui/                  # shadcn primitives (button, card, badge,
│       │   │                        # input, select, tabs, tooltip, popover,
│       │   │                        # separator, scroll-area)
│       │   ├── brand/Logo.tsx       # animated RestoPulse mark + wordmark
│       │   ├── layout/              # Sidebar, Header, AppShell
│       │   └── widgets/             # StatCard, SentimentDonut, AspectBars,
│       │                            # TrendChart, TopKeywords, TopIssues,
│       │                            # LanguageBreakdown
│       └── pages/
│           ├── DashboardPage.tsx
│           ├── ReviewsPage.tsx
│           ├── AnalyticsPage.tsx
│           └── AnalyzePage.tsx
│
└── backend/                         # ⏳ Flask API — to be built next
    ├── app.py                       # Flask entrypoint, CORS-enabled
    ├── requirements.txt
    ├── .env                         # GROQ_API_KEY (gitignored)
    ├── .env.example
    ├── restopulse.db                # SQLite, gitignored
    ├── data/
    │   ├── reviews_raw.csv
    │   └── aspect_keywords.json
    ├── scraper/google_scraper.py
    ├── nlp/
    │   ├── pipeline.py              # orchestrates hybrid pipeline
    │   ├── preprocess.py            # NLTK cleaning, tokenization
    │   ├── language.py              # langdetect
    │   ├── llm.py                   # Groq + Llama 3.3
    │   ├── aspects.py               # rule-based aspect validator
    │   ├── keywords.py              # TF-IDF
    │   └── baseline_vader.py        # VADER baseline
    ├── db/
    │   ├── schema.sql
    │   └── repo.py
    ├── routes/
    │   ├── dashboard.py             # /api/summary
    │   ├── reviews.py               # /api/reviews
    │   ├── analytics.py             # /api/aspects, /api/keywords
    │   └── analyze.py               # POST /api/analyze (live LLM)
    ├── evaluation/
    │   ├── test_set.json
    │   ├── evaluate.py
    │   └── results.md
    ├── scripts/ingest.py
    └── tests/test_pipeline.py
```

---

## 8. Flask Routes (API contracts)

| Method | Path | Returns |
|---|---|---|
| GET | `/` | Dashboard HTML |
| GET | `/api/summary` | `{total, positive, neutral, negative, avg_rating, trend[]}` |
| GET | `/reviews` | Reviews table HTML |
| GET | `/api/reviews?sentiment=&aspect=&q=&lang=` | Paginated review list |
| GET | `/analytics` | Analytics HTML |
| GET | `/api/aspects` | `{food:{pos,neu,neg}, service:{...}, ...}` |
| GET | `/api/keywords?sentiment=positive` | Top N keywords |
| POST | `/api/analyze` | Manual single-review input → live LLM call → returns ABSA result (demo feature, requires internet) |

---

## 9. Dashboard Pages (4 pages, login removed) — ✅ UI built

1. **Dashboard (`/`)** — 4 stat cards (Total / Positive / Negative / Avg Rating) with deltas, sentiment donut, aspect-bars (stacked positive/neutral/negative per aspect), trend area chart (sentiment over time), top keywords cloud-badges, **Top 3 Issues Detected** card (the +10% feature), language mix breakdown.
2. **Reviews (`/reviews`)** — Filterable list (search + sentiment + aspect + language + date), each row shows author avatar, star rating, language flag-badge, sentiment badge, original + translated text, aspect chips with hover tooltips showing the LLM's evidence quote. Click to expand for full ABSA breakdown.
3. **Analytics (`/analytics`)** — 4 tabs: (a) Aspect Performance with grouped bar chart + radar chart of aspect health scores + per-aspect cards, (b) Keyword Insights with top positive/negative bars and a typographic keyword cloud, (c) Rating vs Sentiment scatter plot for spotting mismatches/sarcasm, (d) **Pipeline Evaluation** panel comparing VADER baseline vs Hybrid (LLM) accuracy across all metrics — the empirical defense.
4. **Live Analyze (`/analyze`)** — Two-pane: paste/select a review (sample buttons for each language) → click "Analyze with Hybrid Pipeline" → right pane shows detected language, overall sentiment + confidence, per-aspect ABSA cards with evidence quotes, and extracted keywords. The defense-demo feature.

### Brand & design tokens

- **Wordmark:** `Resto` (foreground) + `Pulse` (brand indigo). Tagline: "Review Intelligence."
- **Logo mark:** rounded indigo→cyan gradient square with a white pulse-line glyph, surrounded by an animated pulse ring.
- **Palette:** Primary indigo `hsl(239 84% 60%)`, brand-accent cyan `hsl(188 94% 43%)`, sentiment green/neutral-slate/rose for positive/neutral/negative. Full dark-mode token set.
- **Typography:** Inter (UI) + JetBrains Mono (numbers/code).
- **Density:** modern SaaS — tight type scale, lots of `tabular-nums`, restrained shadows, subtle borders, animated micro-details (live status pulse, hover lifts).

---

## 10. Phased Build Order (mapped to WFP phases)

| Phase | Dates | Deliverable | Status |
|---|---|---|---|
| **P1a: Plan + UI scaffold** | Apr 23–27 | This plan, React/Vite/Tailwind/shadcn frontend with all 4 pages on mock data | ✅ Done |
| **P1b: Backend skeleton** | Apr 28–May 4 | Flask + CORS scaffold, `requirements.txt`, `.env.example`, Groq API key wired | ⏳ Next |
| **P2: Data + Schema** | May 5–8 | Scrape script run → `reviews_raw.csv`, SQLite schema, aspect keyword dictionary, hand-label 50 reviews → `test_set.json` | |
| **P3a: Hybrid NLP Engine** | May 9–11 | All `nlp/*` modules built, `scripts/ingest.py` runs CSV → DB end-to-end with LLM + VADER baseline both populated | |
| **P3b: Wire frontend to API** | May 12–13 | Replace `lib/mockData.ts` calls with `fetch('/api/...')`, ship Flask routes for `/api/summary`, `/api/reviews`, `/api/aspects`, `/api/keywords`, `/api/analyze` | |
| **P4: Test + Evaluate** | May 14–16 | `evaluation/evaluate.py` produces `results.md`, target ≥80% on hybrid pipeline, usability fixes | |
| **P5: Docs + Demo** | May 17–19 | SRS, slides, demo rehearsal, defense Q&A practice | |

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