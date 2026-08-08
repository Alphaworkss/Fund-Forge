# Google Trends Pipeline — Alternative Data (Member 11)

Part of FundForge's News Collection / market-conditions data feed. Tracks
public search interest in Pakistani market/economic terms as a qualitative
signal alongside the financial news sentiment score, for the central
prediction engine.

## Pipeline stages

| Stage | File | What it does |
|---|---|---|
| 1. Data collection | `collect.py` | Pulls interest-over-time from Google Trends via `pytrends` |
| 2. Data cleaning | `clean.py` | Drops partial/incomplete data points, deduplicates, fills data gaps |
| 3. Normalization | `transform.py` | Min-max scales each keyword to its own [0,1] history |
| 4. Feature extraction | `transform.py` | 7-day rolling average, 7-day % change, 30-day z-score (spike detector) |
| 5. Storage | `storage.py` | SQLite, two tables: `google_trends_raw` and `google_trends_features` |
| 6. Documentation | `README.md` | This file |
| 7. Scheduler/automation | `scheduler.py` | Runs the full pipeline once daily |
| 8. Testing | `test_pipeline.py` | Unit tests for cleaning/transform/storage (pytest, no network calls) |

`pipeline.py` is the orchestrator that chains stages 1–5 together; it's
the one entry point both `scheduler.py` and a one-off manual run should
call.

## Setup

```bash
pip install -r ../requirements.txt
```

## Running

One-off run:
```bash
python pipeline.py
```

Scheduled (runs once immediately, then daily at 08:00 — edit `RUN_AT` in
`scheduler.py` to change):
```bash
python scheduler.py
```

Tests:
```bash
pytest test_pipeline.py
```

## Output schema (what the prediction engine integrates against)

`google_trends_features` — one row per (keyword, date):

| Column | Type | Meaning |
|---|---|---|
| `keyword` | text | search term |
| `date` | text (YYYY-MM-DD) | the day this value applies to |
| `interest` | float | cleaned raw interest score |
| `interest_norm` | float [0,1] | interest, min-max normalized to that keyword's own history |
| `rolling_avg_7d` | float | rolling mean over last 7 *data points* (weekly, not daily, given the 2-year window) |
| `pct_change_7d` | float | % change vs. 7 data points prior (~7 weeks, not 7 days, currently) |
| `zscore_30d` | float | std devs from the trailing 30-data-point mean (~30 weeks, not 30 days, currently) — spike/anomaly indicator |
| `processed_at` | text (ISO timestamp) | when this row was last (re)computed |

Join on `date` (and `keyword`, if the downstream model wants per-term
features rather than an aggregate) to combine with the MUFAP NAV time
series and news sentiment scores.

## Known limitations

- **trendspy is unofficial.** Like its predecessor pytrends, it works
  against Google Trends' internal (undocumented) endpoints rather than a
  supported public API. It's actively maintained as of this writing, but
  if calls ever start failing outright, check the
  [trendspy GitHub repo](https://github.com/sdil87/trendspy) for known
  issues before assuming the code is at fault. (pytrends itself was
  archived by its maintainer in April 2025 and stopped working — that's
  why this pipeline uses trendspy instead.)
- **Cross-batch normalization.** Google Trends only normalizes scores
  0–100 *within* a single batch of up to 5 keywords queried together.
  `KEYWORDS` currently has exactly 5 entries so this isn't an issue yet —
  but if you add more, later batches won't be on the same raw scale as
  earlier ones. `interest_norm` in `transform.py` sidesteps this by
  normalizing each keyword against its own history instead of across
  keywords, so it stays valid regardless of batch size.
- **"7d"/"30d" are data points, not calendar days.** Google Trends
  switches from daily to weekly granularity once a requested window
  exceeds ~9 months. `collect.py` now requests a rolling 2-year window
  (`HISTORY_YEARS = 2`, recomputed fresh on every run), so the data
  collected
  is weekly, so `rolling_avg_7d` is really ~7 weeks and `zscore_30d` is
  really ~30 weeks (~7 months). See the note at the top of `transform.py`.
- **Zero-fill assumption.** `clean.py` treats an isolated `0` between two
  non-zero values as a data gap and forward-fills it. This is usually
  correct for Google Trends but could mask a genuine, real drop to zero
  interest — worth a spot check if a keyword's zeros look meaningful.
- **History depth.** Each run fetches a rolling 2-year window in one
  call (edit `HISTORY_YEARS` in `collect.py` to change), so
  (unlike a scraper that only builds history going forward) there's no
  need to wait weeks to get a usable dataset.

## Common metadata schema

Every record this pipeline collects is also mapped onto FundForge's
team-wide "Common Requirements (For Everyone)" metadata contract (see
`../PROJECT_OVERVIEW.md` section 2b) and stored in the `google_trends_common` table
and Excel sheet, alongside this pipeline's own native schema. See
`common_schema.py` for the exact field mapping.