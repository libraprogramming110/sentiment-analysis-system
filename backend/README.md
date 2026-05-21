# RestoPulse Backend

Flask JSON API for the React frontend.

## Setup (once)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and paste your Groq API key from https://console.groq.com/keys
```

## Run

```powershell
cd backend
.venv\Scripts\activate
python app.py
```

API will be live at `http://127.0.0.1:5000`.

Quick check:

```powershell
curl http://127.0.0.1:5000/api/health
```

## Endpoints (current scaffold — all stubbed until P3a)

| Method | Path                | Purpose                                |
|--------|---------------------|----------------------------------------|
| GET    | /api/health         | Service liveness + env-key check       |
| GET    | /api/summary        | Dashboard top stats                    |
| GET    | /api/trend          | Sentiment volume over time             |
| GET    | /api/issues         | Top 3 auto-detected issues             |
| GET    | /api/languages      | Language mix of corpus                 |
| GET    | /api/reviews        | Filtered reviews list                  |
| GET    | /api/aspects        | Per-aspect sentiment breakdown         |
| GET    | /api/keywords       | Top keywords (optional ?sentiment=…)   |
| GET    | /api/evaluation     | VADER vs Hybrid (LLM) comparison       |
| POST   | /api/analyze        | Live single-review ABSA via Llama 3.3  |
