# GitHub Alt-Data Pipeline — Member 11 (FundForge)

Tracks commit activity, stars, and forks for five major blockchain
ecosystem repos, as a developer-activity signal pairing with the
Blockchain Wallet Metrics source. See `design.md` for the full design
rationale (why stars/forks can't be backfilled, the commit-counting
trick, etc.).

**Status:** All stages are implemented and tested: `collect.py`,
`clean.py`, `transform.py`, `storage.py`, `export_excel.py`, and
`pipeline.py` (the orchestrator). No `scheduler.py` — Windows Task
Scheduler runs the pipeline directly (see `design.md`'s "Scheduling" for
the reasoning).

## Setup

```bash
pip install -r requirements.txt
```

Set a GitHub Personal Access Token (no special scopes needed — this
only reads public data) as an environment variable:

```bash
# Windows (PowerShell)
$env:GITHUB_TOKEN = "your-token-here"

# bash
export GITHUB_TOKEN="your-token-here"
```

Running without a token still works, but is capped at 60 requests/hour
instead of 5,000 — fine for a quick test, not enough for the 2-year
backfill (~520 requests).

## Running

**One-time historical backfill (run this first, once):**

```python
from collect import backfill_commit_history
from storage import get_connection, upsert_raw

conn = get_connection()
upsert_raw(conn, backfill_commit_history())
conn.close()
```

**Daily collection and feature computation (the pipeline):**

```bash
python pipeline.py
```

Or call directly in Python:

```python
from pipeline import run_once

run_once()
```

This runs the full sequence: `collect() -> upsert_raw -> get_raw_records -> clean -> transform -> upsert_features -> export_to_excel`. It is the single entry point for daily scheduled runs and one-off manual invocations.

**Export to Excel for handoff:**

```python
from storage import get_connection
from export_excel import export_to_excel

conn = get_connection()
export_to_excel(conn)  # writes github_data.xlsx
conn.close()
```

**Clean + compute features from backfill (commits only):**

```python
from collect import backfill_commit_history
from clean import clean
from transform import transform
from storage import get_connection, upsert_raw, upsert_features

conn = get_connection()
raw_records = backfill_commit_history()
upsert_raw(conn, raw_records)

cleaned = clean(raw_records)
featured = transform(cleaned)
upsert_features(conn, featured.to_dict(orient="records"))
conn.close()
```

**Note:** `backfill_commit_history()` returns only commit records (not snapshot records for stars/forks). As a result, initial backfill produces only `commits` metric rows; `stars` and `forks` feature rows accumulate from `collect()`'s daily snapshot records. Feature computation over the full `github_raw` history (not just fresh daily records) is now handled by `pipeline.py`'s `get_raw_records()` + `transform()` + `upsert_features()` sequence.

## Testing

```bash
pytest test_collect.py test_storage.py test_export.py test_clean.py test_transform.py test_pipeline.py -v
```

No network calls are made during tests — `requests.get` is mocked
throughout.

## Output schema

`github_raw` — one row per (repo, date, metric):

| Column | Type | Meaning |
|---|---|---|
| `repo` | text | e.g. `bitcoin/bitcoin` |
| `date` | text (YYYY-MM-DD) | snapshot date, or the Monday-ish start of a commit week |
| `metric` | text | `"snapshot"` or `"commits"` |
| `stars` | int, nullable | populated only on `snapshot` rows |
| `forks` | int, nullable | populated only on `snapshot` rows |
| `commits` | int, nullable | populated only on `commits` rows |
| `is_partial` | int (0/1), nullable | `True` for the current, still-accumulating commit week; `False` for completed weeks and all snapshot rows |
| `fetched_at` | text (ISO timestamp) | when this row was last written |

`github_features` — one row per (repo, date, metric), `metric ∈
{"stars", "forks", "commits"}` (note: three metrics here, vs. two on
`github_raw` — a `"snapshot"` raw row splits into separate `"stars"`
and `"forks"` feature rows, since this table has one `value` column
per row and a snapshot carries two numbers):

| Column | Type | Meaning |
|---|---|---|
| `repo` | text | e.g. `bitcoin/bitcoin` |
| `date` | text (YYYY-MM-DD) | the day/week this value applies to |
| `metric` | text | `"stars"`, `"forks"`, or `"commits"` |
| `value` | real | the cleaned raw value for that metric |
| `value_norm` | real, 0-1 | `value`, min-max normalized to that (repo, metric) series' own history |
| `rolling_avg` | real | rolling mean over the last 7 *data points* for that series |
| `pct_change` | real | % change vs. 7 data points prior for that series |
| `zscore` | real | std devs from the trailing 30-data-point mean for that series — spike/anomaly indicator |
| `processed_at` | text (ISO timestamp) | when this row was last (re)computed |

`commits` already has ~106 weeks of real backfilled history, so its
features are meaningful immediately. `stars`/`forks` only accumulate
one point per day going forward (no historical backfill exists or is
possible for these — see `design.md`'s "Metrics collected"), so
`zscore` will be `NaN` and `value_norm`/`rolling_avg` won't be very
meaningful for roughly the first 5-7 real days.

## Common metadata schema

Every record collected by this pipeline's daily run is also mapped onto
FundForge's team-wide "Common Requirements (For Everyone)" metadata contract
(see `../PROJECT_OVERVIEW.md` section 2b) and stored in the `github_common`
table and Excel sheet, alongside this pipeline's own native schema. See
`common_schema.py` for the exact field mapping. One-time historical backfills
(`backfill_commit_history()`) write directly to `github_raw` and are not
retroactively mapped to the common schema.
