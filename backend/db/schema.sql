-- RestoPulse schema. Matches starter.MD §6.
-- Idempotent: safe to run repeatedly.

CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    source_url    TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id      INTEGER REFERENCES restaurants(restaurant_id) ON DELETE CASCADE,
    author             TEXT,
    original_text      TEXT NOT NULL,
    translated_text    TEXT,
    detected_language  TEXT,                       -- 'en','tl','ceb','ilo','unknown'
    rating             INTEGER,
    overall_sentiment  TEXT,                       -- 'positive'|'neutral'|'negative'
    overall_score      REAL,                       -- LLM confidence 0..1
    vader_sentiment    TEXT,
    vader_score        REAL,
    llm_raw_response   TEXT,                       -- cached JSON for reproducibility
    date_added         DATE,
    source             TEXT
);

CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(overall_sentiment);
CREATE INDEX IF NOT EXISTS idx_reviews_lang      ON reviews(detected_language);
CREATE INDEX IF NOT EXISTS idx_reviews_date      ON reviews(date_added);

CREATE TABLE IF NOT EXISTS aspect_sentiments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id     INTEGER REFERENCES reviews(review_id) ON DELETE CASCADE,
    aspect        TEXT,
    sentiment     TEXT,
    evidence      TEXT,
    source_method TEXT                              -- 'llm'|'rule'|'both'
);

CREATE INDEX IF NOT EXISTS idx_aspects_review ON aspect_sentiments(review_id);
CREATE INDEX IF NOT EXISTS idx_aspects_aspect ON aspect_sentiments(aspect);

CREATE TABLE IF NOT EXISTS keywords (
    keyword_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id     INTEGER REFERENCES reviews(review_id) ON DELETE CASCADE,
    keyword       TEXT,
    frequency     INTEGER DEFAULT 1,
    tf_idf_score  REAL
);

CREATE INDEX IF NOT EXISTS idx_keywords_word ON keywords(keyword);
