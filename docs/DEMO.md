# RestoPulse — Live Demo Runbook

A click-by-click script for the demonstration. Rehearse this once end-to-end.

## Before the demo (setup checklist)

- [ ] Backend running: `cd backend && .venv\Scripts\python.exe app.py`
      → confirm http://127.0.0.1:5000/api/health returns `{"status":"ok",...}`
- [ ] Frontend running: `cd frontend && npm run dev`
      → open http://127.0.0.1:5173
- [ ] Browser zoom ~100–110%, window maximized, dark mode set as you prefer.
- [ ] **Internet available** if you plan to show the Live Analyze page (it makes a
      real LLM call). Everything else works offline.
- [ ] Have 2–3 example reviews ready to paste (see bottom of this file).
- [ ] Close other tabs / notifications.

> If the internet fails: skip the Live Analyze step. The rest of the demo runs
> entirely from the cached database — say so out loud, it's a design feature.

---

## Demo flow (~5–7 minutes)

### 1. Dashboard (`/`) — "the overview"
- Point out the **stat cards** (total reviews, sentiment split, avg rating).
- Show the **sentiment donut** and **aspect bars** — "at a glance, food is loved,
  service is the weak point."
- Show **Top 3 Issues Detected** and the **language mix** (English + Tagalog +
  Cebuano) — "this is the multilingual data we're working with."

### 2. Reviews (`/reviews`) — "drill into the data"
- Apply a filter: **sentiment = negative**, **aspect = service**.
- Expand one review → show the **original text**, **language badge**, and the
  **per-aspect chips with evidence** (the quoted phrase that justifies each label).
- Key line: _"Every aspect verdict is backed by evidence from the text — it's not a
  black box."_
- Optionally filter **language = Cebuano** to show a non-English review handled correctly.

### 3. Analytics (`/analytics`) → Pipeline Evaluation tab — "the proof"
- Show the **Hybrid vs VADER** comparison chart and the three stat cards.
- Key line: _"We didn't just build it — we measured it. The hybrid pipeline scores
  78% vs 58% for the traditional baseline, and the gap is biggest on Tagalog and
  Cebuano, exactly where an English-only tool fails."_

### 4. Compare (`/compare`) — "the bonus feature"
- Show the **city summaries** and the **leaderboard**.
- Key line: _"Restaurants are ranked with a Bayesian-adjusted score, so a place with
  9 great reviews can't unfairly beat one with 50."_
- Toggle a **city filter** to show it updating.

### 5. Live Analyze (`/analyze`) — "the live finale" (needs internet)
- Paste a **Tagalog/Cebuano** example (below).
- Click **Analyze** → show detected language, overall sentiment + confidence,
  per-aspect cards, and keywords appearing live.
- Key line: _"This is the same pipeline running in real time on a brand-new review
  it has never seen."_

---

## Example reviews to paste (Live Analyze)

**Tagalog (mixed sentiment):**
> Masarap ang pagkain at sulit ang presyo, pero sobrang bagal ng serbisyo.

_Expect: food = positive, price = positive, service = negative._

**Cebuano (positive):**
> Lami kaayo ang ila nga sinugba ug barato ra. Maayo sad ang staff.

_Expect: food = positive, price = positive, service = positive._

**English (negative):**
> The place looked nice but the food was cold and we waited an hour to be served.

_Expect: ambiance = positive, food = negative, service = negative._

---

## If something goes wrong

| Problem | What to do / say |
|---|---|
| Live Analyze errors out | "That endpoint needs internet; the rest is offline." Skip it. |
| A page is slow to load | Refresh once; data is local so it's quick. |
| Backend not responding | Restart `app.py`; check the health endpoint. |
| Chart looks empty | You may have a filter applied — reset filters. |

**Golden rule:** if the live LLM call fails, calmly fall back to the cached data —
the demo never depends on the internet except for that one optional step.
