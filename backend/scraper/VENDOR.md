# Vendored: `georgekhananaev/google-reviews-scraper-pro`

| | |
|---|---|
| Upstream | https://github.com/georgekhananaev/google-reviews-scraper-pro |
| Pinned tag | `v1.2.3` |
| Pinned commit | `09bfa6215cb37edecc777bb40055d100e88ef767` |
| License | MIT |
| Vendored on | 2026-05-18 |
| Why pinned | Output schema or CLI flags can change between releases; pinning protects [adapter.py](adapter.py) from silent breakage. |

## Update procedure

```bash
cd backend/scraper/vendor/google-reviews-scraper-pro
git fetch --tags origin
git checkout v<NEW_TAG>          # e.g. v1.3.0
cd ../../..
# Re-run the smoke test in §14 / S7 of the plan to confirm
# adapter.py still maps the output schema correctly.
```

If a column rename or field-type change shows up, patch [adapter.py](adapter.py) — do **not** modify any file inside `vendor/`.

## Why we vendor instead of pip install

- Not published on PyPI
- Lets us read/patch the scraper code directly if Google Maps changes break it
- Pin guarantees deterministic output for our [adapter.py](adapter.py)
- See §14 of `starter.MD` (or `~/.claude/plans/hmm-please-help-me-staged-glacier.md`) for the full rationale
