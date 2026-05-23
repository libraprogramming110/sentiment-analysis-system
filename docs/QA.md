# RestoPulse — Anticipated Questions & Answers

Practice these out loud. Keep answers short and confident; expand only if asked.

## About the NLP

**Q: Where is the actual NLP in this project?**
A: There are six NLP components. Five are classical: NLTK preprocessing, language
detection, rule-based aspect tagging with a multilingual keyword dictionary, TF-IDF
keyword extraction, and a VADER baseline. The sixth is the LLM. The NLP is the whole
pipeline, not just the model.

**Q: Did you really build the NLP, or just call an API?**
A: We built the pipeline architecture, the multilingual aspect taxonomy, the prompt
design for structured ABSA output, the language-detection logic that separates
Cebuano from Tagalog, and the evaluation framework that compares against a baseline.
The LLM is one component we integrated — not the whole project.

**Q: Isn't using an LLM cheating / too easy?**
A: LLMs are the current state of the art in NLP and are used in academic NLP research.
Llama 3.1 is Meta's open-source model, not a proprietary black box. Choosing the right
tool for a multilingual problem and validating it empirically is an engineering
decision, which we documented and measured.

**Q: Why not just use VADER, or translate then use VADER?**
A: We tested VADER as our baseline — it scored 58% vs our 78%, and it fails most on
Tagalog and Cebuano because its lexicon is English-only. Translating first loses
nuance, especially for code-mixed "Taglish." The hybrid approach reads the languages
natively.

**Q: How do you handle the mixed languages (Taglish/Bisaya-English)?**
A: We don't translate. The LLM reads multilingual and code-mixed text directly, and
our language detector uses langdetect plus a regional-marker heuristic because
langdetect can't tell Cebuano and Tagalog apart on its own.

## About the evaluation

**Q: How did you create your test set / who labeled it?**
A: We sampled 50 reviews, stratified by language so Cebuano and Tagalog are
well-represented. We seeded candidate labels from the star rating, then a human
verified every one by reading the text — when the text and the stars disagreed, the
text won, because we're measuring how the system reads text.

**Q: Your accuracy is 78%, not 80% — didn't you miss the target?**
A: We're one review short of 80% on a 50-item test set, where each review is worth
2%, so statistically that's a tie with the target. The robust, decisive finding is
the +20-point gap over the baseline — that's what proves the approach works.

**Q: Why is the per-aspect accuracy not in the main comparison?**
A: Honesty. The aspect gold labels were seeded from the LLM's own output, so scoring
the LLM against them would be circular. We kept that table out of the headline and
flagged it; the overall and per-language numbers use independent, human-verified
labels.

**Q: How do we know the results are reproducible?**
A: Every LLM response is cached in the database, and the LLM runs at temperature 0.
The evaluation reads cached predictions, so re-running gives the same numbers with no
internet and no API calls.

## About the system

**Q: What if the internet/API is down during the demo?**
A: The dashboard runs entirely from the local database — no internet needed. Only the
optional Live Analyze page makes a live call, and we can skip it.

**Q: Why Flask + SQLite instead of something bigger?**
A: It's a single-tenant demo with 390 reviews. SQLite is more than enough, keeps the
project portable, and lets the whole thing run offline. The architecture would extend
to Postgres if we needed multi-user scale.

**Q: How does the Compare page ranking work?**
A: It uses Bayesian shrinkage (the IMDb method): a restaurant's score is pulled
toward the global average based on how few reviews it has, so a place with 9 reviews
can't unfairly out-rank one with 50.

**Q: How did you get the data? Is scraping allowed?**
A: We scraped publicly visible Google reviews once with a free self-hosted tool, for
academic use, and stored them locally. We don't scrape during the demo.

## Curveballs

**Q: What was the hardest part?**
A: The multilingual handling — specifically that langdetect maps Cebuano and Ilocano
to Tagalog. We added a regional-marker heuristic to separate them, and we re-derived
languages after noticing the small model over-predicted Ilocano.

**Q: What would you do differently / improve next?**
A: Expand the test set beyond 50 for a tighter accuracy estimate, independently verify
the aspect labels, and scope every dashboard chart by restaurant/city (right now only
the summary cards filter).

**Q: What's the single most important result?**
A: The hybrid pipeline reads multilingual Filipino reviews 20 points more accurately
than the traditional baseline — 78% vs 58% — and wins on every language.
