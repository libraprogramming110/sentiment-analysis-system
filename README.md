# RestoPulse — Multilingual Restaurant Review Sentiment Analysis

RestoPulse turns scraped Google restaurant reviews into an aspect-based sentiment
dashboard. It uses a **hybrid NLP pipeline** (NLTK, langdetect, rule-based aspects,
TF-IDF, VADER baseline, and an open-source LLM via Groq) to handle reviews written
in English, Tagalog, and Cebuano.

- **Frontend:** React 19 + TypeScript + Vite + Tailwind + shadcn/ui + Recharts
- **Backend:** Flask (JSON API) + SQLite
- **NLP:** Hybrid pipeline — Llama 3.1 8B Instant (Groq) + classical NLP components

See [`docs/REPORT.md`](docs/REPORT.md) for the full write-up and architecture.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A free [Groq](https://console.groq.com) API key (only needed to *re-ingest* data
  or use the Live Analyze page — the dashboard runs offline from the bundled DB)

## Setup

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# create your .env from the template and add your key
copy .env.example .env
# then edit .env:  GROQ_API_KEY=...   GROQ_MODEL=llama-3.1-8b-instant
```

### 2. Frontend

```powershell
cd frontend
npm install
```

## Running

Open two terminals.

**Backend** (JSON API on http://127.0.0.1:5000):
```powershell
cd backend
.venv\Scripts\python.exe app.py
```

**Frontend** (dev server on http://127.0.0.1:5173):
```powershell
cd frontend
npm run dev
```

Then open http://127.0.0.1:5173. The dashboard loads from the local SQLite database
and works **without internet**. Only the *Live Analyze* page makes a live LLM call.

## Data pipeline (optional — data is already ingested)

The repository ships with `restopulse.db` already populated (390 analyzed reviews).
To rebuild it from the raw CSV:

```powershell
cd backend
.venv\Scripts\python.exe scripts\ingest.py            # CSV → hybrid pipeline → SQLite
.venv\Scripts\python.exe scripts\ingest.py --reset    # wipe and re-ingest
```

## Evaluation

Compare the hybrid pipeline against the VADER baseline on the gold-standard test set:

```powershell
cd backend
.venv\Scripts\python.exe evaluation\build_test_set.py   # (re)build candidate test set
.venv\Scripts\python.exe evaluation\evaluate.py          # score both pipelines
```

This writes `backend/evaluation/results.md` (human-readable) and `results.json`
(consumed by the Analytics → Pipeline Evaluation tab). Current result:
**Hybrid 78.0% vs VADER 58.0% overall accuracy (+20 points).**

> ⚠️ Don't re-run `build_test_set.py` after hand-verifying labels — it overwrites
> `test_set.json` and your verified labels would be lost.

## Project structure

```
sentiment-analysis-system/
├── README.md
├── docs/                      # report, slides, demo runbook, Q&A
├── backend/
│   ├── app.py                 # Flask entrypoint
│   ├── nlp/                   # hybrid pipeline (preprocess, language, llm, aspects, keywords, vader)
│   ├── routes/                # JSON API endpoints
│   ├── db/                    # schema + SQLite repository
│   ├── scripts/               # ingest, relabel, seed
│   ├── evaluation/            # test_set.json, evaluate.py, results.*
│   └── data/                  # raw CSV + aspect keyword dictionary
└── frontend/
    └── src/                   # React SPA (pages, components, api client)
```

## API endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | service status + whether the Groq key is loaded |
| GET | `/api/summary` | totals, sentiment counts, average rating |
| GET | `/api/trend` | sentiment volume per day |
| GET | `/api/issues` | top negative aspects |
| GET | `/api/languages` | language distribution |
| GET | `/api/restaurants` | per-restaurant stats (Compare page) |
| GET | `/api/aspects` | aspect-level sentiment breakdown |
| GET | `/api/keywords` | top keywords with dominant sentiment |
| GET | `/api/reviews` | filterable review list |
| GET | `/api/evaluation` | hybrid vs VADER comparison |
| POST | `/api/analyze` | live LLM ABSA on submitted text |

## Notes

- This is an academic course project. Reviews are public Google data, used for
  educational purposes; reviewer identities are not the focus of analysis.
- Secrets live in `backend/.env` (gitignored). Never commit a real API key.
