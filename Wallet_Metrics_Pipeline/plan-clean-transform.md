# Blockchain Wallet Metrics Pipeline — clean.py / transform.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `clean.py` and `transform.py` for the Blockchain Wallet Metrics pipeline (drop partial/duplicate raw rows; compute normalized/rolling/pct-change/z-score features), plus the `upsert_features()` addition to `storage.py` needed to land `transform.py`'s output, per the approved design in `design.md`'s "`clean.py` — cleaning", "`transform.py` — normalization + feature extraction", and "Storage & export" sections.

**Architecture:** `clean.py` takes `collect.py`'s raw record list (already long-format: one row per `(coin, date, metric)` with a single `value` column) and returns a filtered, deduplicated DataFrame in that same shape — no reshaping needed. This is simpler than the GitHub pipeline's `clean.py`/`transform.py` split: GitHub's raw records mixed two metrics per "snapshot" row (`stars` + `forks`), requiring a melt step in `transform.py`; this pipeline's `collect.py` (see `plan.md`) already emits one row per metric, so `transform.py` here skips straight to feature computation, grouped by `(coin, metric)`. `storage.py` gains `upsert_features()`, adapted from the GitHub sibling's function to this pipeline's `wallet_metrics_features` table.

**Tech Stack:** Python 3.12, `pandas` (DataFrame reshaping/rolling stats), `sqlite3` (stdlib), `pytest` (testing, no network calls — this stage never touches the network).

## Global Constraints

- Project lives at `D:\news scrapper\Blockchain wallet metrics` — **not a git repo** (verified the same way as the GitHub pipeline). Every task below ends with a "Commit" step in the standard template; skip that step entirely here and just confirm tests pass. Do not run `git init` or any git command in this folder unless the user asks.
- No real network calls in any test — this stage operates purely on in-memory records/DataFrames or `:memory:` SQLite; there is nothing to mock.
- Follow the file/style conventions already established in this project's `collect.py`/`sources/*.py`: a module-level docstring explaining the stage, `logging` (not `print`) for diagnostics where applicable, private helpers prefixed with `_`.
- Reference implementations for patterns: `..\GitHub\clean.py`, `..\GitHub\transform.py`, `..\GitHub\storage.py`'s `upsert_features` (already read in full during design) — this plan's code adapts their conventions, but **skips the melt step GitHub's `transform.py` needed**, since this pipeline's raw record shape is already one row per `(coin, date, metric)` — see Architecture above.
- **No zero-fill/forward-fill step in `clean.py`**, matching the GitHub sibling's reasoning — a `0` is a real data point, not evidence of a reporting gap.
- **Same rolling-window sizes (7 and 30 data points) across all metrics** in `transform.py` — no metric-specific tuning, matching the approved design.
- Every raw record's `is_partial` is always `False` for this pipeline's 3 in-scope coins (see `plan.md`'s Global Constraints) — `clean.py`'s partial-row-drop logic is a no-op on real data today, kept only for schema consistency and any future coin that does have partial data. Tests still cover it, since the function's contract doesn't depend on which coins happen to be wired up.
- Scope: this plan covers `clean.py`, `transform.py`, and the `upsert_features()` addition to `storage.py`, plus their tests. `storage.py`'s base schema/`get_connection()`/`upsert_raw()` and `export_excel.py` were already built in `plan.md` (Tasks 5-6) — this plan's Task 3 builds directly on that. `storage.py`'s `get_raw_records()` addition and `pipeline.py` are covered by `plan-pipeline.md` — do not create those here. **Execution order: `plan.md` must be implemented before this plan** (this plan's Task 3 modifies the `storage.py` that `plan.md`'s Task 5 creates).

---

### Task 1: Data cleaning (`clean.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\clean.py`
- Test: `D:\news scrapper\Blockchain wallet metrics\test_clean.py`

**Interfaces:**
- Consumes: raw record dicts shaped like `collect.py`'s output (`coin`, `date`, `metric`, `value`, `is_partial`) from `plan.md`.
- Produces: `clean(records: list[dict]) -> pd.DataFrame` with columns `coin, date, metric, value, is_partial` (`date` as `pd.Timestamp`), fewer rows than the input (partial rows dropped, duplicates deduplicated). Task 2's `transform()` consumes this DataFrame shape directly.

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
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 700000, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-27", "metric": "tx_count", "value": 650000, "is_partial": True},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-20")


def test_clean_deduplicates_keeping_latest():
    records = [
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 700000, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 712078, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["value"] == 712078


def test_clean_keeps_zero_values_as_is():
    records = [
        {"coin": "bnb", "date": "2020-08-29", "metric": "tx_count", "value": 0, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["value"] == 0


def test_clean_handles_multiple_metrics_for_same_coin_and_date():
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses", "value": 497475, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2
    assert set(df["metric"]) == {"tx_count", "active_addresses"}


def test_clean_different_metrics_on_same_date_are_not_deduplicated_away():
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_volume", "value": 92620.9, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2


def test_clean_different_coins_on_same_date_and_metric_are_not_deduplicated_away():
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "ethereum", "date": "2026-07-30", "metric": "tx_count", "value": 1766208, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2


def test_clean_empty_records_returns_empty_dataframe_with_columns():
    df = clean([])

    assert df.empty
    assert list(df.columns) == ["coin", "date", "metric", "value", "is_partial"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_clean.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'clean'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# clean.py
"""
clean.py — Stage 2: Data Cleaning

Takes the raw records from collect.py (or any sources/ adapter's
backfill()/collect()) and:
  - drops rows flagged is_partial=True — a no-op on this pipeline's
    current 3 coins (Bitcoin/Ethereum/BNB Chain never publish an
    in-progress day, verified live — see design.md), kept for schema
    consistency with the sibling pipelines and any future coin that
    does have partial data
  - drops duplicate (coin, date, metric) triples, keeping the latest

No zero-fill/forward-fill step: a 0 (e.g. a genuinely quiet day for a
low-activity metric) is a real data point, not evidence of a reporting
gap — same reasoning as the GitHub pipeline's commit counts.

No reshaping happens here — collect.py already emits one row per
(coin, date, metric) with a single value column, so unlike the GitHub
pipeline's clean.py/transform.py split, there's no melt step needed
anywhere in this pipeline.
"""

import pandas as pd

RAW_COLUMNS = ["coin", "date", "metric", "value", "is_partial"]


def clean(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=RAW_COLUMNS)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    df = df.drop_duplicates(subset=["coin", "date", "metric"], keep="last")
    df = df[~df["is_partial"]].copy()

    return df.sort_values(["coin", "metric", "date"])[RAW_COLUMNS].reset_index(drop=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_clean.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 2.**

---

### Task 2: Feature computation (`transform.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\transform.py`
- Test: `D:\news scrapper\Blockchain wallet metrics\test_transform.py`

**Interfaces:**
- Consumes: `clean()`'s output DataFrame shape from Task 1 (`coin, date, metric, value, is_partial`).
- Produces: `transform(df: pd.DataFrame) -> pd.DataFrame` with columns `coin, date, metric, value, value_norm, rolling_avg, pct_change, zscore` (`date` as a string `"YYYY-MM-DD"`). This is the shape Task 3's `upsert_features()` and `plan-pipeline.md`'s `pipeline.py` consume.

- [ ] **Step 1: Write the failing tests**

```python
# test_transform.py
"""
test_transform.py — Stage 8: Testing (transform.py)

Run with: pytest test_transform.py
"""

import pandas as pd

from transform import transform


def test_transform_adds_expected_columns():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-30"), "metric": "tx_count", "value": 712078, "is_partial": False},
    ])

    out = transform(df)

    assert set(out.columns) == {"coin", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}


def test_transform_normalizes_within_zero_one_per_series():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp(f"2026-01-0{i}"), "metric": "tx_count", "value": v, "is_partial": False}
        for i, v in zip(range(1, 4), [500000, 600000, 700000])
    ])

    out = transform(df)

    assert out["value_norm"].min() == 0.0
    assert out["value_norm"].max() == 1.0


def test_transform_computes_independent_series_per_metric():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-30"), "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-30"), "metric": "active_addresses", "value": 497475, "is_partial": False},
    ])

    out = transform(df)

    tx_rows = out[out["metric"] == "tx_count"]
    addr_rows = out[out["metric"] == "active_addresses"]
    assert len(tx_rows) == 1 and tx_rows["value"].iloc[0] == 712078
    assert len(addr_rows) == 1 and addr_rows["value"].iloc[0] == 497475


def test_transform_two_coins_do_not_mix_series():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-01-01"), "metric": "tx_count", "value": 1000000, "is_partial": False},
        {"coin": "ethereum", "date": pd.Timestamp("2026-01-01"), "metric": "tx_count", "value": 10, "is_partial": False},
    ])

    out = transform(df)

    assert (out["value_norm"] == 0.0).all()


def test_transform_date_formatted_as_string():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-27"), "metric": "tx_count", "value": 712078, "is_partial": False},
    ])

    out = transform(df)

    assert out["date"].iloc[0] == "2026-07-27"


def test_transform_pct_change_infinity_becomes_null():
    df = pd.DataFrame([
        {"coin": "bnb", "date": pd.Timestamp(f"2026-01-0{i}"), "metric": "tx_count", "value": v, "is_partial": False}
        for i, v in zip(range(1, 10), [0, 0, 0, 0, 0, 0, 0, 5, 10])
    ])

    out = transform(df)

    # pct_change vs 7 points prior: the row for 2026-01-08 (index 7,
    # value 5) divides by the value from 2026-01-01 (0) -> inf without
    # the fix. Must be null (None/NaN), not inf, matching the GitHub
    # pipeline's Bug #3 lesson.
    row = out[out["date"] == "2026-01-08"]
    assert pd.isna(row["pct_change"].iloc[0])


def test_transform_empty_dataframe_returns_empty_with_all_columns():
    df = pd.DataFrame(columns=["coin", "date", "metric", "value", "is_partial"])

    out = transform(df)

    assert out.empty
    assert set(out.columns) == {"coin", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_transform.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'transform'`

- [ ] **Step 3: Write minimal implementation**

```python
# transform.py
"""
transform.py — Stage 3: Normalization, Stage 4: Feature Extraction

Unlike the GitHub pipeline's transform.py, there's no melt step here:
collect.py already emits one row per (coin, date, metric) with a
single value column (see design.md), so this module goes straight to
feature computation, grouped by (coin, metric) — same 2-key grouping
as GitHub's (repo, metric).

Same math as both sibling pipelines: min-max value_norm within that
series' own history; rolling_avg (7 data points, min_periods=1);
pct_change (vs. 7 data points prior, inf treated as unknown/blank per
the GitHub pipeline's Bug #3 lesson — dividing by a real zero, e.g. a
quiet day, is a valid data point, not an error, but the resulting
infinity must not leak into storage/exports); zscore (30-data-point
trailing mean/std, min_periods=5).
"""

import pandas as pd

FEATURE_COLUMNS = ["coin", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    out = df.sort_values(["coin", "metric", "date"]).reset_index(drop=True)
    grouped = out.groupby(["coin", "metric"])["value"]

    out["value_norm"] = grouped.transform(
        lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0.0
    )
    out["rolling_avg"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).mean())
    out["pct_change"] = grouped.transform(lambda s: s.pct_change(periods=7))
    out["pct_change"] = out["pct_change"].replace([float("inf"), float("-inf")], None)

    roll_mean_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).mean())
    roll_std_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).std())
    out["zscore"] = (out["value"] - roll_mean_30) / roll_std_30
    out["zscore"] = out["zscore"].replace([float("inf"), float("-inf")], None)

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out[FEATURE_COLUMNS]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_transform.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 3.**

---

### Task 3: Feature storage (`storage.py`)

**Files:**
- Modify: `D:\news scrapper\Blockchain wallet metrics\storage.py` (already created by `plan.md`'s Task 5 — see this plan's Global Constraints on execution order)
- Modify: `D:\news scrapper\Blockchain wallet metrics\test_storage.py`

**Interfaces:**
- Consumes: `transform()`'s output record shape from Task 2 (`coin, date, metric, value, value_norm, rolling_avg, pct_change, zscore`), passed as `list[dict]` (e.g. via `transform(df).to_dict(orient="records")`).
- Produces: `upsert_features(conn: sqlite3.Connection, records: list[dict]) -> None`. `plan-pipeline.md`'s `pipeline.py` calls this after `transform()`.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_storage.py — also update the existing import line at the top from
#   from storage import get_connection, upsert_raw
# to:
from storage import get_connection, upsert_raw, upsert_features


def test_upsert_features_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
         "value_norm": 0.5, "rolling_avg": 700000.0, "pct_change": 0.1, "zscore": 0.2},
    ]

    upsert_features(conn, records)
    upsert_features(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_features_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_features(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
         "value_norm": 0.5, "rolling_avg": 700000.0, "pct_change": 0.1, "zscore": 0.2},
    ])
    upsert_features(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 720000,
         "value_norm": 0.9, "rolling_avg": 710000.0, "pct_change": 0.2, "zscore": 0.5},
    ])

    row = conn.execute("SELECT value, value_norm FROM wallet_metrics_features").fetchone()

    assert row == (720000, 0.9)
    conn.close()


def test_upsert_features_stores_multiple_metrics_for_same_coin_date():
    conn = get_connection(":memory:")

    upsert_features(
        conn,
        [
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
             "value_norm": 1.0, "rolling_avg": 700000.0, "pct_change": None, "zscore": None},
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses", "value": 497475,
             "value_norm": 1.0, "rolling_avg": 480000.0, "pct_change": None, "zscore": None},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    assert count == 2
    conn.close()


def test_upsert_features_handles_null_pct_change_and_zscore():
    conn = get_connection(":memory:")

    upsert_features(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
         "value_norm": 1.0, "rolling_avg": 700000.0, "pct_change": None, "zscore": None},
    ])

    row = conn.execute("SELECT pct_change, zscore FROM wallet_metrics_features").fetchone()

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
            INSERT INTO wallet_metrics_features (
                coin, date, metric, value, value_norm, rolling_avg,
                pct_change, zscore, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin, date, metric) DO UPDATE SET
                value=excluded.value,
                value_norm=excluded.value_norm,
                rolling_avg=excluded.rolling_avg,
                pct_change=excluded.pct_change,
                zscore=excluded.zscore,
                processed_at=excluded.processed_at
            """,
            (
                r["coin"],
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
Expected: PASS (all `upsert_raw`/schema tests from `plan.md`'s Task 5, plus these 4 new `upsert_features` tests)

- [ ] **Step 5: No git repo — skip commit. Implementation plan complete.**
