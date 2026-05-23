"""Re-derive `detected_language` for all stored reviews using ONLY langdetect +
the refined regional heuristic — no LLM calls, no tokens.

Why: the Llama 3.1 8B language field is unreliable (it invented Ilocano on a
Cebuano-region corpus). Our langdetect+heuristic detector is more conservative
and accurate for English/Cebuano/Tagalog, which is what this corpus contains.

Usage (from backend/):
    .venv\\Scripts\\python.exe scripts\\relabel_languages.py
"""
from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nlp.language import detect_language  # noqa: E402

DB = Path(__file__).resolve().parent.parent / "restopulse.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT review_id, original_text FROM reviews").fetchall()

    before = Counter(
        r[0] for r in conn.execute("SELECT detected_language FROM reviews")
    )

    updates = []
    for r in rows:
        lang = detect_language(r["original_text"] or "")
        updates.append((lang, r["review_id"]))

    conn.executemany(
        "UPDATE reviews SET detected_language = ? WHERE review_id = ?", updates
    )
    conn.commit()

    after = Counter(
        r[0] for r in conn.execute("SELECT detected_language FROM reviews")
    )
    conn.close()

    print("language distribution BEFORE:", dict(before))
    print("language distribution AFTER :", dict(after))
    print(f"relabeled {len(updates)} reviews.")


if __name__ == "__main__":
    main()
