# GitHub Alt-Data Pipeline — clean.py / transform.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `clean.py` and `transform.py` for the GitHub alt-data pipeline (drop partial/duplicate raw rows; reshape + normalize + engineer rolling/pct-change/z-score features), plus the `upsert_features()` addition to `storage.py` needed to land `transform.py`'s output, per the approved design in `design.md`'s "clean.py — cleaning", "transform.py — normalization + feature extraction", and "Storage & export" sections.

**Architecture:** `clean.py` takes `collect.py`'s raw record list and returns a filtered, deduplicated DataFrame in the same raw shape (`repo, date, metric, stars, forks, commits, is_partial`) — no reshaping. `transform.py` takes that DataFrame, melts it into long format (`repo, date, metric, value` with `metric ∈ {stars, forks, commits}` — a `"snapshot"` row explodes into two rows since `github_features` has one `value` column per row but a snapshot carries two numbers), then computes `value_norm`/`rolling_avg`/`pct_change`/`zscore` per `(repo, metric)` group. `storage.py` gains `upsert_features()`, a 3-column-key adaptation of the Google Trends sibling's function, using the same `ON CONFLICT DO UPDATE` upsert pattern as the existing `upsert_raw()`.

**Tech Stack:** Python 3.12, `pandas` (DataFrame reshaping/rolling stats), `sqlite3` (stdlib), `pytest` (testing, no network calls — this stage never touches the network).

## Global Constraints

- Project lives at `D:\news scrapper\GitHub` — **not a git repo** (already verified in the prior plan). Every task below ends with a "Commit" step in the standard template; skip that step entirely here and just confirm tests pass. Do not run `git init` or any git command in this folder unless the user asks.
- No real network calls in any test — this stage operates purely on in-memory records/DataFrames or `:memory:` SQLite; there is nothing to mock.
- Follow the file/style conventions already established in this project's `collect.py`, `storage.py`, `export_excel.py`: a module-level docstring explaining the stage, `logging` (not `print`) for diagnostics where applicable, private helpers prefixed with `_`.
- Reference implementations for patterns: `../Google trends/clean.py`, `../Google trends/transform.py`, `../Google trends/storage.py` (its `upsert_features` function) — already read in full during design; this plan's code adapts their conventions to this project's 3-column `(repo, date, metric)` key and mixed-metric raw shape.
- **No zero-fill/forward-fill step in `clean.py`** (deliberate deviation from the Google Trends sibling) — a `0` here is a real data point (a quiet commit week), not evidence of a reporting gap.
- **Same rolling-window sizes (7 and 30 data points) across all three metrics** (`stars`, `forks`, `commits`) in `transform.py` — no metric-specific tuning, matching the approved design.
- Scope: this plan covers `clean.py`, `transform.py`, the `upsert_features()` addition to `storage.py`, their tests, and a `README.md` update. `pipeline.py`/`scheduler.py` are explicitly deferred (see `design.md`'s "Open items for later stages") — do not create them in this plan.

---

### Task 1: Data cleaning (`clean.py`)

**Files:**
- Create: `D:\news scrapper\GitHub\clean.py`
- Test: `D:\news scrapper\GitHub\test_clean.py`

**Interfaces:**
- Consumes: raw record dicts shaped like `collect.py`'s output (`repo`, `date`, `metric` ∈ `{"snapshot", "commits"}`, plus `stars`/`forks` or `commits`, plus `is_partial`).
- Produces: `clean(records: list[dict]) -> pd.DataFrame` with columns `repo, date, metric, stars, forks, commits, is_partial` (`date` as `pd.Timestamp`), fewer rows than the input (partial rows dropped, duplicates deduplicated). Task 2/3's `transform()` consumes this DataFrame shape directly.

- [ ] **Step 1: Write the failing tests**

```python
# test_clean.py
"""
test_clean.py — Stage 8: Testing (clean.py)

Run with: pytest test_clean.py
"""

import pandas as pd

from clean import clean


def test_clean_drops_partial_rows():
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 3, "is_partial": True},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-20")


def test_clean_deduplicates_keeping_latest():
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 9, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["commits"] == 9


def test_clean_keeps_zero_values_as_is():
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 0, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["commits"] == 0


def test_clean_handles_mixed_snapshot_and_commits_metrics():
    records = [
        {"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2
    assert set(df["metric"]) == {"snapshot", "commits"}


def test_clean_different_metrics_on_same_date_are_not_deduplicated_away():
    records = [
        {"repo": "x/y", "date": "2026-07-27", "metric": "snapshot", "stars": 100, "forks": 20, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2


def test_clean_empty_records_returns_empty_dataframe_with_columns():
    df = clean([])

    assert df.empty
    assert list(df.columns) == ["repo", "date", "metric", "stars", "forks", "commits", "is_partial"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_clean.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'clean'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# clean.py
"""
clean.py — Stage 2: Data Cleaning

Takes the raw records from collect.py and:
  - drops rows flagged is_partial=True — the current, still-accumulating
    commit week would otherwise pollute downstream feature calculations
    with a not-finished-yet value
  - drops duplicate (repo, date, metric) triples, keeping the latest

Unlike ../Google trends/clean.py, there is no zero-fill/forward-fill
step here: a 0 is a real data point (a quiet commit week), not evidence
of a reporting gap the way Google Trends' interest score dropping to 0
often is — GitHub's commit-count endpoint doesn't have that failure
mode, and stars/forks realistically never hit 0 for these repos.

No reshaping happens here — the output stays in the same raw shape as
the input (repo, date, metric, stars, forks, commits, is_partial), just
with fewer rows. Reshaping into the per-metric long format is
transform.py's job.
"""

import pandas as pd

RAW_COLUMNS = ["repo", "date", "metric", "stars", "forks", "commits", "is_partial"]


def clean(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=RAW_COLUMNS)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    df = df.drop_duplicates(subset=["repo", "date", "metric"], keep="last")
    df = df[~df["is_partial"]].copy()

    for col in RAW_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df.sort_values(["repo", "metric", "date"])[RAW_COLUMNS].reset_index(drop=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_clean.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 2.**

---

### Task 2: Reshape to long format (`transform.py`)

**Files:**
- Create: `D:\news scrapper\GitHub\transform.py`
- Test: `D:\news scrapper\GitHub\test_transform.py`

**Interfaces:**
- Consumes: `clean()`'s output DataFrame shape from Task 1 (`repo, date, metric, stars, forks, commits, is_partial`).
- Produces: `_melt_to_long(df: pd.DataFrame) -> pd.DataFrame` with columns `repo, date, metric, value`, `metric ∈ {"stars", "forks", "commits"}`. Task 3's `transform()` calls this internally.

- [ ] **Step 1: Write the failing tests**

```python
# test_transform.py
"""
test_transform.py — Stage 8: Testing (transform.py)

Run with: pytest test_transform.py
"""

import pandas as pd

from transform import _melt_to_long


def test_melt_splits_snapshot_into_stars_and_forks():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-30"), "metric": "snapshot",
         "stars": 100, "forks": 20, "commits": pd.NA, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert set(long_df["metric"]) == {"stars", "forks"}
    assert long_df[long_df["metric"] == "stars"]["value"].iloc[0] == 100
    assert long_df[long_df["metric"] == "forks"]["value"].iloc[0] == 20


def test_melt_renames_commits_column_to_value():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert list(long_df["metric"]) == ["commits"]
    assert long_df["value"].iloc[0] == 5


def test_melt_output_has_exactly_these_columns():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert list(long_df.columns) == ["repo", "date", "metric", "value"]


def test_melt_handles_mixed_snapshot_and_commits_rows():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-30"), "metric": "snapshot",
         "stars": 100, "forks": 20, "commits": pd.NA, "is_partial": False},
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert len(long_df) == 3
    assert set(long_df["metric"]) == {"stars", "forks", "commits"}


def test_melt_empty_dataframe_returns_empty_long_dataframe():
    df = pd.DataFrame(columns=["repo", "date", "metric", "stars", "forks", "commits", "is_partial"])

    long_df = _melt_to_long(df)

    assert long_df.empty
    assert list(long_df.columns) == ["repo", "date", "metric", "value"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_transform.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'transform'`

- [ ] **Step 3: Write minimal implementation**

```python
# transform.py
"""
transform.py — Stage 3: Normalization, Stage 4: Feature Extraction

collect.py's raw taxonomy has 2 metrics ("snapshot" carrying both stars
and forks; "commits" carrying one number), but github_features has one
`value` column per (repo, date, metric) row — there's no schema room
for two numbers on one row. So _melt_to_long() explodes each
"snapshot" row into two rows ("stars", "forks"); "commits" rows keep
their row, renamed to "value". The result is three fully independent
series per repo (stars, forks, commits) — their growth rates don't
meaningfully correlate on any short window, so each gets its own
normalization and rolling stats, grouped by (repo, metric) rather than
Google Trends' single-key groupby("keyword").
"""

import pandas as pd

LONG_COLUMNS = ["repo", "date", "metric", "value"]


def _melt_to_long(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=LONG_COLUMNS)

    commits_rows = (
        df[df["metric"] == "commits"][["repo", "date", "commits"]]
        .rename(columns={"commits": "value"})
        .assign(metric="commits")
    )

    snapshot = df[df["metric"] == "snapshot"]
    stars_rows = (
        snapshot[["repo", "date", "stars"]]
        .rename(columns={"stars": "value"})
        .assign(metric="stars")
    )
    forks_rows = (
        snapshot[["repo", "date", "forks"]]
        .rename(columns={"forks": "value"})
        .assign(metric="forks")
    )

    long_df = pd.concat([commits_rows, stars_rows, forks_rows], ignore_index=True)
    return long_df[LONG_COLUMNS]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_transform.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 3.**

---

### Task 3: Feature computation (`transform.py`)

**Files:**
- Modify: `D:\news scrapper\GitHub\transform.py`
- Modify: `D:\news scrapper\GitHub\test_transform.py`

**Interfaces:**
- Consumes: `_melt_to_long(df) -> pd.DataFrame` from Task 2; `clean()`'s output shape from Task 1 as the public entry point's input.
- Produces: `transform(df: pd.DataFrame) -> pd.DataFrame` with columns `repo, date, metric, value, value_norm, rolling_avg, pct_change, zscore` (`date` as a string `"YYYY-MM-DD"`). This is the shape Task 4's `upsert_features()` and a future `pipeline.py` consume.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_transform.py
from transform import transform


def test_transform_adds_expected_columns():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    out = transform(df)

    assert set(out.columns) == {"repo", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}


def test_transform_normalizes_within_zero_one_per_series():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp(f"2026-01-0{i}"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": v, "is_partial": False}
        for i, v in zip(range(1, 4), [5, 10, 15])
    ])

    out = transform(df)

    assert out["value_norm"].min() == 0.0
    assert out["value_norm"].max() == 1.0


def test_transform_computes_independent_series_per_metric():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-30"), "metric": "snapshot",
         "stars": 100, "forks": 20, "commits": pd.NA, "is_partial": False},
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    out = transform(df)

    stars_rows = out[out["metric"] == "stars"]
    forks_rows = out[out["metric"] == "forks"]
    commits_rows = out[out["metric"] == "commits"]
    assert len(stars_rows) == 1 and stars_rows["value"].iloc[0] == 100
    assert len(forks_rows) == 1 and forks_rows["value"].iloc[0] == 20
    assert len(commits_rows) == 1 and commits_rows["value"].iloc[0] == 5


def test_transform_two_repos_do_not_mix_series():
    df = pd.DataFrame([
        {"repo": "a/a", "date": pd.Timestamp("2026-01-01"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 100, "is_partial": False},
        {"repo": "b/b", "date": pd.Timestamp("2026-01-01"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 1, "is_partial": False},
    ])

    out = transform(df)

    assert (out["value_norm"] == 0.0).all()


def test_transform_date_formatted_as_string():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    out = transform(df)

    assert out["date"].iloc[0] == "2026-07-27"


def test_transform_empty_dataframe_returns_empty_with_all_columns():
    df = pd.DataFrame(columns=["repo", "date", "metric", "stars", "forks", "commits", "is_partial"])

    out = transform(df)

    assert out.empty
    assert set(out.columns) == {"repo", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_transform.py -v`
Expected: FAIL — `ImportError: cannot import name 'transform' from 'transform'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to transform.py, after _melt_to_long

FEATURE_COLUMNS = ["repo", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    long_df = _melt_to_long(df)

    if long_df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    out = long_df.sort_values(["repo", "metric", "date"]).reset_index(drop=True)
    grouped = out.groupby(["repo", "metric"])["value"]

    out["value_norm"] = grouped.transform(
        lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0.0
    )
    out["rolling_avg"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).mean())
    out["pct_change"] = grouped.transform(lambda s: s.pct_change(periods=7))

    roll_mean_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).mean())
    roll_std_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).std())
    out["zscore"] = (out["value"] - roll_mean_30) / roll_std_30
    out["zscore"] = out["zscore"].replace([float("inf"), float("-inf")], None)

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out[FEATURE_COLUMNS]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_transform.py -v`
Expected: PASS (11 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 4.**

---

### Task 4: Feature storage (`storage.py`)

**Files:**
- Modify: `D:\news scrapper\GitHub\storage.py`
- Modify: `D:\news scrapper\GitHub\test_storage.py`

**Interfaces:**
- Consumes: `transform()`'s output record shape from Task 3 (`repo, date, metric, value, value_norm, rolling_avg, pct_change, zscore`) — passed in as `list[dict]` (e.g. via `transform(df).to_dict(orient="records")`, mirroring how the Google Trends sibling's `pipeline.py` calls its own `upsert_features`).
- Produces: `upsert_features(conn: sqlite3.Connection, records: list[dict]) -> None`. A future `pipeline.py` calls this after `transform()`.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_storage.py — also update the existing import line at the top from
#   from storage import get_connection, upsert_raw
# to:
from storage import get_connection, upsert_raw, upsert_features


def test_upsert_features_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "value": 5,
         "value_norm": 0.5, "rolling_avg": 5.0, "pct_change": 0.1, "zscore": 0.2},
    ]

    upsert_features(conn, records)
    upsert_features(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_features_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_features(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "value": 5,
         "value_norm": 0.5, "rolling_avg": 5.0, "pct_change": 0.1, "zscore": 0.2},
    ])
    upsert_features(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "value": 9,
         "value_norm": 0.9, "rolling_avg": 7.0, "pct_change": 0.2, "zscore": 0.5},
    ])

    row = conn.execute("SELECT value, value_norm FROM github_features").fetchone()

    assert row == (9, 0.9)
    conn.close()


def test_upsert_features_stores_multiple_metrics_for_same_repo_date():
    conn = get_connection(":memory:")

    upsert_features(
        conn,
        [
            {"repo": "x/y", "date": "2026-07-30", "metric": "stars", "value": 100,
             "value_norm": 1.0, "rolling_avg": 100.0, "pct_change": None, "zscore": None},
            {"repo": "x/y", "date": "2026-07-30", "metric": "forks", "value": 20,
             "value_norm": 1.0, "rolling_avg": 20.0, "pct_change": None, "zscore": None},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    assert count == 2
    conn.close()


def test_upsert_features_handles_null_pct_change_and_zscore():
    conn = get_connection(":memory:")

    upsert_features(conn, [
        {"repo": "x/y", "date": "2026-07-30", "metric": "stars", "value": 100,
         "value_norm": 1.0, "rolling_avg": 100.0, "pct_change": None, "zscore": None},
    ])

    row = conn.execute("SELECT pct_change, zscore FROM github_features").fetchone()

    assert row == (None, None)
    conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_storage.py -v`
Expected: FAIL — `ImportError: cannot import name 'upsert_features' from 'storage'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to storage.py, after upsert_raw

def upsert_features(conn: sqlite3.Connection, records: "list[dict]") -> None:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO github_features (
                repo, date, metric, value, value_norm, rolling_avg,
                pct_change, zscore, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo, date, metric) DO UPDATE SET
                value=excluded.value,
                value_norm=excluded.value_norm,
                rolling_avg=excluded.rolling_avg,
                pct_change=excluded.pct_change,
                zscore=excluded.zscore,
                processed_at=excluded.processed_at
            """,
            (
                r["repo"],
                r["date"],
                r["metric"],
                r["value"],
                r["value_norm"],
                r["rolling_avg"],
                r["pct_change"],
                r["zscore"],
                now,
            ),
        )
    conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_storage.py -v`
Expected: PASS (8 tests — 4 existing `upsert_raw`/schema tests + 4 new `upsert_features` tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 5.**

---

### Task 5: Documentation (`README.md`)

**Files:**
- Modify: `D:\news scrapper\GitHub\README.md`

**Interfaces:**
- Consumes: everything from Tasks 1-4 (documents how to run `clean()`/`transform()`/`upsert_features()` manually).
- Produces: nothing further consumes this — it's the last task in this plan.

- [ ] **Step 1: Update the Status line**

In `README.md`, replace:

```markdown
**Status:** `collect.py`, `storage.py`, and `export_excel.py` are
implemented and tested. `clean.py`, `transform.py`, `pipeline.py`, and
`scheduler.py` are not yet built — see `design.md`'s "Open items for
later stages".
```

with:

```markdown
**Status:** `collect.py`, `storage.py`, `export_excel.py`, `clean.py`,
and `transform.py` are implemented and tested. `pipeline.py` and
`scheduler.py` (the orchestrator and daily-run automation) are not yet
built — see `design.md`'s "Open items for later stages".
```

- [ ] **Step 2: Add a cleaning + feature computation example to the Running section**

In `README.md`, after the existing "**Export to Excel for handoff:**" code block and before the `## Testing` heading, insert:

```markdown
**Clean + compute features (once raw data has been collected):**

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
```

- [ ] **Step 3: Update the Testing section**

In `README.md`, replace:

```markdown
```bash
pytest test_collect.py test_storage.py test_export.py -v
```
```

with:

```markdown
```bash
pytest test_collect.py test_storage.py test_export.py test_clean.py test_transform.py -v
```
```

- [ ] **Step 4: Document the `github_features` output schema**

In `README.md`, replace:

```markdown
`github_features` exists (same key) but stays empty until `transform.py`
is built.
```

with:

```markdown
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
```

- [ ] **Step 5: No git repo — skip commit. Implementation plan complete.**
