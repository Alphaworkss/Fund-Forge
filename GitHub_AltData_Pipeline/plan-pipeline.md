# GitHub Alt-Data Pipeline — pipeline.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the orchestration stage for the GitHub alt-data pipeline — `storage.py`'s new `get_raw_records()`, `pipeline.py`'s `run_once()`, and `test_pipeline.py` — per the approved design in `design.md`'s "`storage.py` addition: `get_raw_records`", "`pipeline.py` — orchestration", and "Testing" sections.

**Architecture:** `run_once()` calls `collect()` for today's incremental slice (~15 records), upserts it, then reads the ENTIRE `github_raw` table back via the new `get_raw_records()` and runs `clean()`/`transform()` over that full history — not just today's fresh slice — because `collect()` deliberately never re-pulls the full multi-week history itself. Features get upserted, then the workbook gets exported. `backfill_commit_history()` is never called from `pipeline.py` — it stays a separate, manually-run operation.

**Tech Stack:** Python 3.12, `sqlite3` (stdlib), `pandas` (via `clean`/`transform`), `pytest` + `unittest.mock` (testing — `collect()` and `export_to_excel()` get mocked; no network calls, and no accidental writes to the real project's `github_data.db`/`github_data.xlsx`).

## Global Constraints

- Project lives at `D:\news scrapper\GitHub` — **not a git repo** (verified repeatedly this session). Every task below ends with a "Commit" step in the standard template; skip that step entirely here and just confirm tests pass. Do not run `git init` or any git command in this folder.
- `backfill_commit_history()` is NEVER called from `pipeline.py` — it stays a strictly separate, manually-run, one-time operation. This is a binding design decision, not an oversight to "complete."
- No `scheduler.py` in this plan — explicitly out of scope, decided against in favor of a Windows Task Scheduler entry set up as a deployment step after this plan is done.
- Tests must not touch the real project's `github_data.db` or `github_data.xlsx` — use pytest's `tmp_path` fixture for a real temp-file SQLite database (NOT `:memory:` — `:memory:` databases are per-connection and aren't shared across the two separate connections a test would need: one to pre-seed data, one that `run_once()` opens internally via `get_connection(db_path)`), and always mock `export_to_excel` so it never actually writes a file during tests.
- Follow the file/style conventions already established in this project's `collect.py`/`clean.py`/`transform.py`/`storage.py`/`export_excel.py`: a module-level docstring explaining the stage, `logging` (not `print`) for diagnostics, private helpers prefixed with `_`.
- Reference implementation for the orchestration shape: `../Google trends/pipeline.py` (already read in full this session) — same `collect → upsert_raw → clean → transform → upsert_features → export_to_excel` sequence, same early-return-on-empty-`collect()` pattern, same `finally: conn.close()`. Note: `../Google trends/test_pipeline.py` does NOT test `pipeline.py`'s orchestration at all (it only tests `clean`/`transform`/`storage`, despite its filename) — this project's `test_pipeline.py` is new territory, not a port.
- Exact current signatures this plan builds against (verified against the real files this session): `collect.collect(repos: list[str] | None = None) -> list[dict]`; `clean.clean(records: list[dict]) -> pd.DataFrame`; `transform.transform(df: pd.DataFrame) -> pd.DataFrame`; `storage.get_connection(db_path: str = DB_PATH) -> sqlite3.Connection`; `storage.upsert_raw(conn, records: list[dict]) -> None`; `storage.upsert_features(conn, records: list[dict]) -> None`; `storage.DB_PATH = "github_data.db"`; `export_excel.export_to_excel(conn, excel_path: str = EXCEL_PATH) -> None`; `github_raw` columns `repo, date, metric, stars, forks, commits, is_partial, fetched_at` (`PRIMARY KEY (repo, date, metric)`).

---

### Task 1: Raw record read-back (`storage.py`)

**Files:**
- Modify: `D:\news scrapper\GitHub\storage.py`
- Modify: `D:\news scrapper\GitHub\test_storage.py`

**Interfaces:**
- Consumes: the existing `github_raw` table (columns `repo, date, metric, stars, forks, commits, is_partial, fetched_at`) and `get_connection`/`upsert_raw` from this same file.
- Produces: `get_raw_records(conn: sqlite3.Connection) -> list[dict]`, with each dict shaped exactly like `clean.py`'s `RAW_COLUMNS` (`repo, date, metric, stars, forks, commits, is_partial` — no `fetched_at`). Task 2's `pipeline.py` calls this directly.

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
            {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
            {"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20, "is_partial": False},
        ],
    )

    records = get_raw_records(conn)

    assert len(records) == 2
    conn.close()


def test_get_raw_records_returns_expected_columns():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
    ])

    records = get_raw_records(conn)

    assert set(records[0].keys()) == {"repo", "date", "metric", "stars", "forks", "commits", "is_partial"}
    conn.close()


def test_get_raw_records_preserves_is_partial_as_stored_int():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": True},
    ])

    records = get_raw_records(conn)

    # SQLite has no native boolean — upsert_raw stores int(True) == 1.
    # get_raw_records deliberately does NOT coerce this; clean.py's
    # existing is_partial coercion (added specifically for this
    # database-read-back path) is what handles it downstream.
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
    Read everything out of github_raw as plain dicts shaped like
    clean.py's RAW_COLUMNS (repo, date, metric, stars, forks, commits,
    is_partial) — no fetched_at, since nothing downstream uses it.

    Deliberately does no is_partial coercion here: it passes through
    whatever SQLite naturally returns (int 0/1), relying on clean.py's
    existing coercion (added specifically to make records read back
    out of the database safe to clean) to handle it. This is the
    integration path that fix was built for — pipeline.py needs the
    FULL raw history, not just a single day's fresh collect() output,
    to compute meaningful multi-week rolling/pct-change/z-score
    features.
    """
    cur = conn.execute(
        "SELECT repo, date, metric, stars, forks, commits, is_partial FROM github_raw"
    )
    columns = [d[0] for d in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_storage.py -v`
Expected: PASS (12 tests — 8 existing + 4 new)

- [ ] **Step 5: No git repo — skip commit. Confirm the files are saved and move to Task 2.**

---

### Task 2: Orchestration (`pipeline.py`)

**Files:**
- Create: `D:\news scrapper\GitHub\pipeline.py`
- Create: `D:\news scrapper\GitHub\test_pipeline.py`

**Interfaces:**
- Consumes: `collect.collect()`, `clean.clean()`, `transform.transform()`, `storage.get_connection()`/`upsert_raw()`/`upsert_features()`/`get_raw_records()` from Task 1, `export_excel.export_to_excel()`.
- Produces: `run_once(db_path: str = "github_data.db") -> None`. Nothing further in this plan consumes this — it's the pipeline's entry point (a future Task Scheduler deployment step calls `python pipeline.py`, which runs `run_once()` via the `if __name__ == "__main__":` guard).

- [ ] **Step 1: Write the failing tests**

```python
# test_pipeline.py
"""
test_pipeline.py — Stage 8: Testing (pipeline.py)

Tests run_once()'s orchestration with collect() mocked — a unit test
shouldn't depend on the live GitHub API. Uses a real temp-file SQLite
database (via pytest's tmp_path fixture), not :memory:, because
run_once() opens its own connection internally via
get_connection(db_path), and :memory: databases are per-connection —
not shared across the separate connection a test needs to pre-seed
data through. export_to_excel is always mocked so tests never write a
real file, and never touch this project's real github_data.xlsx.

Run with: pytest test_pipeline.py
"""

from unittest.mock import patch

from storage import get_connection, upsert_raw

import pipeline


def test_run_once_stores_new_records_and_features(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-27", "commits": 5, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    raw_count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    feature_count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    conn.close()

    assert raw_count == 1
    assert feature_count == 1


def test_run_once_computes_features_over_full_history_not_just_new_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    # Pre-seed 6 historical commit records for the same (repo, metric)
    # series, simulating data already sitting in the database from a
    # prior day's collect() run or the one-time backfill.
    conn = get_connection(db_path)
    upsert_raw(
        conn,
        [
            {"repo": "x/y", "metric": "commits", "date": f"2026-06-{d:02d}", "commits": d, "is_partial": False}
            for d in [1, 8, 15, 22, 29]
        ]
        + [{"repo": "x/y", "metric": "commits", "date": "2026-07-06", "commits": 6, "is_partial": False}],
    )
    conn.close()

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-13", "commits": 7, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    feature_count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    rolling_avg = conn.execute(
        "SELECT rolling_avg FROM github_features WHERE date = '2026-07-13'"
    ).fetchone()[0]
    conn.close()

    # 7 total raw records (6 pre-seeded + 1 fresh from collect()) means
    # 7 feature rows — if run_once() only transformed collect()'s fresh
    # output (1 record), this would be 1, not 7.
    assert feature_count == 7
    # A 7-point rolling average that only saw the single newest record
    # would equal that record's own value (7.0). Seeing a different
    # value proves the full read-back history fed the computation, not
    # just today's fresh slice.
    assert rolling_avg != 7.0


def test_run_once_returns_early_when_collect_returns_no_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[]), patch("pipeline.export_to_excel") as mock_export:
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    raw_count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    feature_count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    conn.close()

    assert raw_count == 0
    assert feature_count == 0
    mock_export.assert_not_called()


def test_run_once_exports_to_excel_after_a_successful_run(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-27", "commits": 5, "is_partial": False},
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

Google Trends' pipeline.py does transform(clean(collect())) directly —
that works there because its collect() always re-pulls its entire
window every run. This project's collect() deliberately does not (see
design.md): it only returns today's incremental slice (~15 records).
So run_once() reads the full github_raw table back via
get_raw_records() after storing today's slice, and computes features
over that full history — not just what collect() returned this run.

backfill_commit_history() is never called from here. It stays a
strictly separate, manually-run, one-time operation (see design.md).

This is the one entry point both a future Task Scheduler job and a
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


def run_once(db_path: str = "github_data.db") -> None:
    conn = get_connection(db_path)
    try:
        new_records = collect()
        if not new_records:
            logger.warning("No records collected — check GITHUB_TOKEN/rate limit, or retry later.")
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

- [ ] **Step 5: No git repo — skip commit. Implementation plan complete.**
