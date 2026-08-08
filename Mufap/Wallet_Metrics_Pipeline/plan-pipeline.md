# Blockchain Wallet Metrics Pipeline — pipeline.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the orchestration stage for the Blockchain Wallet Metrics pipeline — `storage.py`'s new `get_raw_records()`, `pipeline.py`'s `run_once()`, and `test_pipeline.py` — then verify the whole pipeline against real data and deploy it, per the approved design in `design.md`'s "`pipeline.py` — orchestration" and "Scheduling" sections.

**Architecture:** `run_once()` calls `collect()` for today's incremental slice, upserts it, then reads the ENTIRE `wallet_metrics_raw` table back via the new `get_raw_records()` and runs `clean()`/`transform()` over that full history — not just today's fresh slice — because `collect()`'s per-coin adapters (see `plan.md`) return their own full available window each time, and features need the full history to be meaningful. Features get upserted, then the workbook gets exported. Tasks 3-4 are operational, not code: running the pipeline for real against live data (this project's core lesson — see `..\PROJECT_OVERVIEW.md` section 4) and setting up the Windows Task Scheduler entry.

**Tech Stack:** Python 3.12, `sqlite3` (stdlib), `pandas` (via `clean`/`transform`), `pytest` + `unittest.mock` (Task 2's testing — `collect()` and `export_to_excel()` get mocked; no network calls, and no accidental writes to the real project's `wallet_metrics.db`/`wallet_metrics.xlsx`).

## Global Constraints

- Project lives at `D:\news scrapper\Blockchain wallet metrics` — **not a git repo** (verified the same way as the GitHub pipeline). Task 1-2 steps end with a "Commit" step in the standard template; skip that step entirely and just confirm tests pass. Do not run `git init` or any git command in this folder unless the user asks.
- This plan assumes `plan.md` (collect.py, 3 adapters, storage.py's base schema, export_excel.py) and `plan-clean-transform.md` (clean.py, transform.py, storage.py's `upsert_features`) are both already implemented — `run_once()` imports from all of them.
- Tests must not touch the real project's `wallet_metrics.db` or `wallet_metrics.xlsx` — use pytest's `tmp_path` fixture for a real temp-file SQLite database (NOT `:memory:` — `run_once()` opens its own connection internally via `get_connection(db_path)`, and `:memory:` databases aren't shared across the separate connection a test needs to pre-seed data through), and always mock `export_to_excel` so it never actually writes a file during tests.
- Follow the file/style conventions already established in this project's `collect.py`/`clean.py`/`transform.py`/`storage.py`/`export_excel.py`: a module-level docstring explaining the stage, `logging` (not `print`) for diagnostics, private helpers prefixed with `_`.
- Reference implementation for the orchestration shape: `..\GitHub\pipeline.py` (already read in full during design) — same `collect → upsert_raw → get_raw_records → clean → transform → upsert_features → export_to_excel` sequence, same early-return-on-empty-`collect()` pattern, same `finally: conn.close()`.
- Exact current signatures this plan builds against (from `plan.md` and `plan-clean-transform.md`): `collect.collect() -> list[dict]`; `clean.clean(records: list[dict]) -> pd.DataFrame`; `transform.transform(df: pd.DataFrame) -> pd.DataFrame`; `storage.get_connection(db_path: str = DB_PATH) -> sqlite3.Connection`; `storage.upsert_raw(conn, records: list[dict]) -> None`; `storage.upsert_features(conn, records: list[dict]) -> None`; `storage.DB_PATH = "wallet_metrics.db"`; `export_excel.export_to_excel(conn, excel_path: str = EXCEL_PATH) -> None`; `wallet_metrics_raw` columns `coin, date, metric, value, is_partial, fetched_at` (`PRIMARY KEY (coin, date, metric)`).
- No `scheduler.py` — same decision as both sibling pipelines: a real Windows Task Scheduler entry (Task 4) is used instead of an in-process scheduling loop.
- **No environment variables need to be set for this pipeline** (see `design.md`'s "Auth & rate limits") — this simplifies Task 4 relative to the GitHub pipeline's `GITHUB_TOKEN` deployment step.

---

### Task 1: Raw record read-back (`storage.py`)

**Files:**
- Modify: `D:\news scrapper\Blockchain wallet metrics\storage.py`
- Modify: `D:\news scrapper\Blockchain wallet metrics\test_storage.py`

**Interfaces:**
- Consumes: the existing `wallet_metrics_raw` table (columns `coin, date, metric, value, is_partial, fetched_at`) and `get_connection`/`upsert_raw` from this same file.
- Produces: `get_raw_records(conn: sqlite3.Connection) -> list[dict]`, with each dict shaped exactly like `clean.py`'s `RAW_COLUMNS` minus `is_partial`'s type coercion (`coin, date, metric, value, is_partial` — no `fetched_at`). Task 2's `pipeline.py` calls this directly.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_storage.py — also update the existing import line at the top from
#   from storage import get_connection, upsert_raw, upsert_features
# to:
from storage import get_connection, upsert_raw, upsert_features, get_raw_records


def test_get_raw_records_returns_all_rows():
    conn = get_connection(":memory:")
    upsert_raw(
        conn,
        [
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
            {"coin": "ethereum", "date": "2026-07-30", "metric": "active_addresses", "value": 497475, "is_partial": False},
        ],
    )

    records = get_raw_records(conn)

    assert len(records) == 2
    conn.close()


def test_get_raw_records_returns_expected_columns():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
    ])

    records = get_raw_records(conn)

    assert set(records[0].keys()) == {"coin", "date", "metric", "value", "is_partial"}
    conn.close()


def test_get_raw_records_preserves_is_partial_as_stored_int():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": True},
    ])

    records = get_raw_records(conn)

    # SQLite has no native boolean — upsert_raw stores int(True) == 1.
    # get_raw_records deliberately does NOT coerce this; clean.py's
    # existing "not df['is_partial']" check works fine against 0/1
    # ints directly, so no coercion layer is needed here (this pipeline
    # never actually stores is_partial=True on real data, but the
    # schema-consistency path is still tested).
    assert records[0]["is_partial"] == 1
    conn.close()


def test_get_raw_records_empty_table_returns_empty_list():
    conn = get_connection(":memory:")

    records = get_raw_records(conn)

    assert records == []
    conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_storage.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_raw_records' from 'storage'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to storage.py, after upsert_features

def get_raw_records(conn: sqlite3.Connection) -> "list[dict]":
    """
    Read everything out of wallet_metrics_raw as plain dicts shaped like
    clean.py's RAW_COLUMNS (coin, date, metric, value, is_partial) — no
    fetched_at, since nothing downstream uses it.

    pipeline.py needs the FULL raw history, not just a single day's
    fresh collect() output, to compute meaningful multi-week
    rolling/pct-change/z-score features.
    """
    cur = conn.execute(
        "SELECT coin, date, metric, value, is_partial FROM wallet_metrics_raw"
    )
    columns = [d[0] for d in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_storage.py -v`
Expected: PASS (all prior `upsert_raw`/`upsert_features`/schema tests, plus these 4 new `get_raw_records` tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 2.**

---

### Task 2: Orchestration (`pipeline.py`)

**Files:**
- Create: `D:\news scrapper\Blockchain wallet metrics\pipeline.py`
- Create: `D:\news scrapper\Blockchain wallet metrics\test_pipeline.py`

**Interfaces:**
- Consumes: `collect.collect()`, `clean.clean()`, `transform.transform()`, `storage.get_connection()`/`upsert_raw()`/`upsert_features()`/`get_raw_records()` from Task 1, `export_excel.export_to_excel()`.
- Produces: `run_once(db_path: str = "wallet_metrics.db") -> None`. Nothing further in this plan consumes this — it's the pipeline's entry point (Task 4's Task Scheduler deployment calls `python pipeline.py`, which runs `run_once()` via the `if __name__ == "__main__":` guard).

- [ ] **Step 1: Write the failing tests**

```python
# test_pipeline.py
"""
test_pipeline.py — Stage 8: Testing (pipeline.py)

Tests run_once()'s orchestration with collect() mocked — a unit test
shouldn't depend on live blockchain-explorer sites. Uses a real
temp-file SQLite database (via pytest's tmp_path fixture), not
:memory:, because run_once() opens its own connection internally via
get_connection(db_path). export_to_excel is always mocked so tests
never write a real file, and never touch this project's real
wallet_metrics.xlsx.

Run with: pytest test_pipeline.py
"""

from unittest.mock import patch

from storage import get_connection, upsert_raw

import pipeline


def test_run_once_stores_new_records_and_features(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    raw_count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone()[0]
    feature_count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    conn.close()

    assert raw_count == 1
    assert feature_count == 1


def test_run_once_computes_features_over_full_history_not_just_new_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    # Pre-seed 6 historical tx_count records for the same (coin, metric)
    # series, simulating data already sitting in the database from a
    # prior day's collect() run or the one-time backfill.
    conn = get_connection(db_path)
    upsert_raw(
        conn,
        [
            {"coin": "bitcoin", "date": f"2026-06-{d:02d}", "metric": "tx_count", "value": d * 10000, "is_partial": False}
            for d in [1, 8, 15, 22, 29]
        ]
        + [{"coin": "bitcoin", "date": "2026-07-06", "metric": "tx_count", "value": 600000, "is_partial": False}],
    )
    conn.close()

    with patch("pipeline.collect", return_value=[
        {"coin": "bitcoin", "date": "2026-07-13", "metric": "tx_count", "value": 700000, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    feature_count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    rolling_avg = conn.execute(
        "SELECT rolling_avg FROM wallet_metrics_features WHERE date = '2026-07-13'"
    ).fetchone()[0]
    conn.close()

    # 7 total raw records (6 pre-seeded + 1 fresh from collect()) means
    # 7 feature rows — if run_once() only transformed collect()'s fresh
    # output (1 record), this would be 1, not 7.
    assert feature_count == 7
    # A 7-point rolling average that only saw the single newest record
    # would equal that record's own value (700000.0). Seeing a
    # different value proves the full read-back history fed the
    # computation, not just today's fresh slice.
    assert rolling_avg != 700000.0


def test_run_once_returns_early_when_collect_returns_no_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[]), patch("pipeline.export_to_excel") as mock_export:
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    raw_count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone()[0]
    feature_count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    conn.close()

    assert raw_count == 0
    assert feature_count == 0
    mock_export.assert_not_called()


def test_run_once_exports_to_excel_after_a_successful_run(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
    ]), patch("pipeline.export_to_excel") as mock_export:
        pipeline.run_once(db_path=db_path)

    mock_export.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline.py
"""
pipeline.py — Orchestrator

Chains all stages together:
  collect -> upsert_raw -> get_raw_records -> clean -> transform ->
  upsert_features -> export_to_excel

run_once() reads the full wallet_metrics_raw table back via
get_raw_records() after storing today's fresh collect() output, and
computes features over that full history — not just what collect()
returned this run — because meaningful rolling/pct-change/z-score
features need more than one day's data point.

This is the one entry point both the Task Scheduler job (Task 4) and a
one-off manual run should call.
"""

import logging

from collect import collect
from clean import clean
from transform import transform
from storage import get_connection, upsert_raw, upsert_features, get_raw_records
from export_excel import export_to_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_once(db_path: str = "wallet_metrics.db") -> None:
    conn = get_connection(db_path)
    try:
        new_records = collect()
        if not new_records:
            logger.warning("No records collected from any source — check network/rate limits, or retry later.")
            return
        upsert_raw(conn, new_records)
        logger.info("Stored %d new raw records", len(new_records))

        all_records = get_raw_records(conn)
        cleaned = clean(all_records)
        featured = transform(cleaned)
        feature_records = featured.to_dict(orient="records")
        upsert_features(conn, feature_records)
        logger.info(
            "Stored %d feature records (from %d total raw records)",
            len(feature_records),
            len(all_records),
        )

        export_to_excel(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    run_once()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_pipeline.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 3.**

---

### Task 3: Real live run — hand verification (operational, not code)

This task has no test-first cycle — it's the step this project's own `PROJECT_OVERVIEW.md` identifies as the single most important habit in the whole project: **passing unit tests is not the same as the code actually working.** All 3 real bugs found in the GitHub pipeline passed every unit test and were only caught by running against real data and checking numbers by hand. Do not skip this or treat Task 1-2's green tests as "done" on their own.

**Interfaces:**
- Consumes: everything from Tasks 1-2, plus `plan.md`'s and `plan-clean-transform.md`'s modules — this is the first time all of them run together against the real network.
- Produces: a working `wallet_metrics.db` and `wallet_metrics.xlsx` in this folder, and (if any bug is found) a fix commit-worthy of documenting in `PHASES.md`'s ledger, mirroring how `..\GitHub\PROJECT_OVERVIEW.md` section 4 documents its 3 bugs.

- [ ] **Step 1: Run the one-time backfill for real, against the real network**

```python
# run interactively, e.g. `python -c "..."` or a scratch script
from sources import bitcoin, ethereum, bnb
from storage import get_connection, upsert_raw

conn = get_connection()
records = bitcoin.backfill() + ethereum.backfill() + bnb.backfill()
print(f"Collected {len(records)} raw records")
upsert_raw(conn, records)
conn.close()
```

Expected: no exceptions. Bitcoin should return ~2190 records (3 metrics x ~730 days for `years=2`); Ethereum ~7,300+ records (2 metrics x 11+ years of full history, since Etherscan's CSV always returns everything back to 2015 — see `plan.md`'s `backfill()` docstring); BNB fewer (1 metric x ~2000 days since its 2020 launch). If any adapter returns 0 records, stop and debug before continuing — check the live URL manually in a browser first (`https://etherscan.io/chart/tx?output=csv`, etc.) to rule out the source itself having changed shape since Phase 1's research.

- [ ] **Step 2: Spot-check the raw data by hand**

```python
import sqlite3
conn = sqlite3.connect("wallet_metrics.db")
for coin in ("bitcoin", "ethereum", "bnb"):
    row = conn.execute(
        "SELECT metric, date, value FROM wallet_metrics_raw WHERE coin = ? ORDER BY date DESC LIMIT 3", (coin,)
    ).fetchall()
    print(coin, row)
conn.close()
```

Compare a couple of the printed values against the live chart pages themselves (e.g. open `https://etherscan.io/chart/active-address` in a browser and check the most recent plotted value roughly matches what got stored). This is the same "check the real numbers by hand" discipline that caught all 3 GitHub pipeline bugs — don't skip it because the unit tests passed.

- [ ] **Step 3: Run the full pipeline (`pipeline.py`) for real**

Run: `python pipeline.py`
Expected: log lines showing `Stored N new raw records`, `Stored N feature records (from M total raw records)`, and `Exported N raw rows to wallet_metrics.xlsx`, with no exceptions or tracebacks.

- [ ] **Step 4: Verify idempotency — run it again immediately**

Run: `python pipeline.py` a second time, right after Step 3.
Expected: raw row count in `wallet_metrics_raw` does NOT roughly double — the upsert should update existing `(coin, date, metric)` rows, not duplicate them. Confirm with:

```python
import sqlite3
conn = sqlite3.connect("wallet_metrics.db")
print(conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone())
conn.close()
```

Run this both right after Step 3 and right after this second `pipeline.py` run — the count should be the same (give or take exactly the ~1-3 records/metric that would have newly published between the two runs, if any).

- [ ] **Step 5: Open `wallet_metrics.xlsx` and eyeball it**

Open the file in Excel (or any spreadsheet tool). Confirm: the `raw` sheet has rows for all 3 coins; the `features` sheet has `value_norm` values between 0 and 1, `pct_change` has no `inf`/`-inf` cells (search for "inf" in the sheet — if found, that's the same class of bug as the GitHub pipeline's Bug #3, and `transform.py`'s `.replace([float("inf"), float("-inf")], None)` needs re-checking against whatever real data triggered it), and `zscore` is blank for the first ~5-29 rows of each series (expected — `min_periods=5` on a 30-point window) rather than every row.

- [ ] **Step 6: Update `PHASES.md`**

Mark Phase 8 as ✅ Done in the status table, and add a ledger entry under a new "Phase 8" heading summarizing: record counts collected per coin, whether idempotency held, and — if any bug was found and fixed during this task — a short writeup in the same style as `..\GitHub\PROJECT_OVERVIEW.md` section 4's bug stories (what looked fine, why it wasn't, the fix). If nothing broke, say so plainly rather than omitting the entry.

---

### Task 4: Task Scheduler deployment (operational, not code)

**Interfaces:**
- Consumes: a working `pipeline.py` from Task 2, verified for real in Task 3.
- Produces: a daily-triggered Windows Task Scheduler entry, matching the shape of the `"FundForge Google Trend Pipeline"` and `"FundForge GitHub Alt-Data Pipeline"` tasks already set up for the sibling pipelines.

- [ ] **Step 1: Create the scheduled task**

Mirror the existing tasks' shape exactly (same trigger time, same account, `python.exe` pointed at this folder's `pipeline.py`):

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "pipeline.py" -WorkingDirectory "D:\news scrapper\Blockchain wallet metrics"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -TaskName "FundForge Wallet Metrics Pipeline" -Action $action -Trigger $trigger -Description "Daily blockchain wallet metrics collection (Bitcoin/Ethereum/BNB Chain)"
```

- [ ] **Step 2: Verify the task was created**

Run: `Get-ScheduledTask -TaskName "FundForge Wallet Metrics Pipeline" | Select-Object TaskName, State`
Expected: `State` shows `Ready`.

- [ ] **Step 3: Manually trigger it once and confirm it actually runs**

```powershell
Start-ScheduledTask -TaskName "FundForge Wallet Metrics Pipeline"
```

Wait a few seconds, then check `wallet_metrics.db`'s modified timestamp updated and, if `pipeline.py` is extended to write a `run.log` file (matching the GitHub pipeline's convention — not required by this plan, but worth doing consistently), confirm it shows fresh log lines. **If the task gets stuck in a `"Queued"` state and never runs** (the exact failure the GitHub pipeline hit — see `..\GitHub\PROJECT_OVERVIEW.md` section 6), the fix is the same: `Restart-Service -Name Schedule -Force` from an Administrator PowerShell window, or restart the machine if that's blocked too. Check whether the existing Google Trends/GitHub tasks still run fine first — if they do and only this new one is stuck, it's very likely the same Task Scheduler service quirk, not a problem with this pipeline's code.

- [ ] **Step 4: Update `PHASES.md`**

Mark Phase 9 as ✅ Done in the status table, with a ledger entry noting the task name, trigger time, and confirmation that a real triggered run succeeded. This is the final step of this plan — once done, the Blockchain Wallet Metrics pipeline is running automatically for Bitcoin, Ethereum, and BNB Chain, matching the other two pipelines' deployment state.
