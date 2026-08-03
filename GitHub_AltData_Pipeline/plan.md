# GitHub Alt-Data Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `collect.py` for the GitHub alt-data pipeline (2-year commit-history backfill + daily star/fork/commit collection), plus the `storage.py` and `export_excel.py` it needs to land its output somewhere testable, per the approved design at `design.md`.

**Architecture:** A single `collect.py` module (mirroring `../Google trends/collect.py`'s "dumb collector, returns plain dicts" style) exposes two entry points — `backfill_commit_history()` (one-time, run manually) and `collect()` (daily). Both call a shared internal HTTP helper that handles GitHub token auth and per-repo error isolation. Output lands in a two-table SQLite database (`storage.py`) and can be dumped to `.xlsx` (`export_excel.py`) for handoff, exactly matching the Google Trends pipeline's storage/export shape.

**Tech Stack:** Python 3.12, `requests` (GitHub REST API calls), `sqlite3` (stdlib), `pandas` + `openpyxl` (Excel export), `pytest` + `unittest.mock` (testing, no real network calls).

## Global Constraints

- Project lives at `D:\news scrapper\GitHub` — **not a git repo** (verified: `git status` there returns "not a git repository"). Every task below ends with a "Commit" step in the standard template; skip that step entirely here and just confirm the tests pass. Do not run `git init` or any git command in this folder unless the user asks.
- `GITHUB_TOKEN` is read from an environment variable only (`os.environ`) — never hardcoded, never logged, never included in error messages.
- No real network calls in any test — mock `requests.get` (or the module's internal helper functions) per the design doc's testing section.
- Follow the file/style conventions already established in `../Google trends/*.py`: a module-level docstring explaining the stage, `logging` (not `print`) for diagnostics, private helpers prefixed with `_`.
- Reference implementation for patterns: `../Google trends/collect.py`, `storage.py`, `export_excel.py`, `test_pipeline.py` — already read in full during design; this plan's code mirrors their conventions.
- Scope: this plan covers `collect.py`, `storage.py`, `export_excel.py`, and their tests/docs only. `clean.py`/`transform.py`/`pipeline.py`/`scheduler.py` are explicitly deferred (see `design.md`'s "Open items for later stages") — do not create them in this plan.

---

### Task 1: HTTP helper — auth + error handling (`collect.py`)

**Files:**
- Create: `D:\news scrapper\GitHub\collect.py`
- Test: `D:\news scrapper\GitHub\test_collect.py`

**Interfaces:**
- Produces: `_auth_headers() -> dict`, `_get(url: str, params: dict = None) -> requests.Response | None` (raises `RuntimeError` if GitHub's rate limit is exhausted; returns `None` on any other failure; returns the `Response` on success). Later tasks call `_get()` for every GitHub API request.

- [ ] **Step 1: Write the failing tests**

```python
# test_collect.py
"""
test_collect.py — Stage 8: Testing (collect.py)

Mocks requests.get so these tests never touch the network or the real
GitHub API. Run with: pytest test_collect.py
"""

from unittest.mock import Mock, patch

import collect


def _fake_response(status_code=200, json_data=None, headers=None):
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else []
    resp.headers = headers or {}
    resp.text = ""
    return resp


@patch("collect.requests.get")
def test_get_returns_response_on_200(mock_get):
    mock_get.return_value = _fake_response(status_code=200, json_data={"ok": True})

    resp = collect._get("https://api.github.com/repos/x/y")

    assert resp.json() == {"ok": True}


@patch("collect.requests.get")
def test_get_returns_none_on_non_200(mock_get):
    mock_get.return_value = _fake_response(status_code=404)

    resp = collect._get("https://api.github.com/repos/x/y")

    assert resp is None


@patch("collect.requests.get")
def test_get_raises_runtime_error_when_rate_limit_exhausted(mock_get):
    mock_get.return_value = _fake_response(
        status_code=403, headers={"X-RateLimit-Remaining": "0"}
    )

    try:
        collect._get("https://api.github.com/repos/x/y")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_auth_headers_includes_token_when_env_var_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")

    headers = collect._auth_headers()

    assert headers["Authorization"] == "Bearer test-token-123"


def test_auth_headers_omits_authorization_when_no_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    headers = collect._auth_headers()

    assert "Authorization" not in headers
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'collect'` (file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

```python
# collect.py
"""
collect.py — Stage 1: Data Collection

Pulls GitHub metrics (commit history, star/fork snapshots) for a fixed
set of blockchain-ecosystem repos via the GitHub REST API.

Two entry points:
  - backfill_commit_history() : one-time, run manually before the daily
                                  pipeline starts. See design.md for why
                                  this can't cover stars/forks too (no
                                  historical count endpoint exists).
  - collect()                  : the daily run — star/fork snapshot plus
                                  a re-check of the current, still-
                                  accumulating week's commit count.

Returns plain dicts. No cleaning or transformation happens here — see
design.md's "Open items for later stages" for what clean.py/transform.py
will eventually do with this output.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

API_ROOT = "https://api.github.com"


def _auth_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, params: dict = None) -> "requests.Response | None":
    """
    GET url with auth headers.

    Returns the Response on 200. Returns None on any other failure
    (network error, 404, unexpected status) after logging why — this
    lets callers skip a single failed repo without crashing the whole
    run. Raises RuntimeError only when GitHub's rate limit is actually
    exhausted, since continuing to call a throttled endpoint just makes
    things worse.
    """
    try:
        resp = requests.get(url, headers=_auth_headers(), params=params, timeout=10)
    except requests.RequestException:
        logger.exception("Request failed: %s", url)
        return None

    if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        logger.error("GitHub rate limit exhausted on %s", url)
        raise RuntimeError("GitHub rate limit exhausted")

    if resp.status_code != 200:
        logger.warning("Request to %s failed: %s %s", url, resp.status_code, resp.text[:200])
        return None

    return resp
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: No git repo — skip commit (see Global Constraints). Confirm the file is saved and move to Task 2.**

---

### Task 2: Commit-count Link-header trick (`collect.py`)

**Files:**
- Modify: `D:\news scrapper\GitHub\collect.py`
- Modify: `D:\news scrapper\GitHub\test_collect.py`

**Interfaces:**
- Consumes: `_get(url, params) -> requests.Response | None` from Task 1.
- Produces: `_count_commits_in_range(repo: str, since: datetime.date, until: datetime.date) -> int | None`. Later tasks (backfill, collect) call this per week window.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_collect.py
from datetime import date


@patch("collect.requests.get")
def test_count_commits_uses_link_header_last_page(mock_get):
    link = (
        '<https://api.github.com/repos/x/y/commits?page=2>; rel="next", '
        '<https://api.github.com/repos/x/y/commits?page=37>; rel="last"'
    )
    mock_get.return_value = _fake_response(json_data=[{"sha": "abc"}], headers={"Link": link})

    count = collect._count_commits_in_range("x/y", date(2026, 1, 1), date(2026, 1, 8))

    assert count == 37


@patch("collect.requests.get")
def test_count_commits_no_link_header_uses_result_length(mock_get):
    mock_get.return_value = _fake_response(json_data=[{"sha": "abc"}])

    count = collect._count_commits_in_range("x/y", date(2026, 1, 1), date(2026, 1, 8))

    assert count == 1


@patch("collect.requests.get")
def test_count_commits_zero_commits_in_range(mock_get):
    mock_get.return_value = _fake_response(json_data=[])

    count = collect._count_commits_in_range("x/y", date(2026, 1, 1), date(2026, 1, 8))

    assert count == 0


@patch("collect.requests.get")
def test_count_commits_returns_none_when_request_fails(mock_get):
    mock_get.return_value = _fake_response(status_code=404)

    count = collect._count_commits_in_range("x/y", date(2026, 1, 1), date(2026, 1, 8))

    assert count is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect.py -v`
Expected: FAIL — `AttributeError: module 'collect' has no attribute '_count_commits_in_range'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to collect.py, near the top
import datetime
from urllib.parse import parse_qs, urlparse

# ... (after _get)

def _count_commits_in_range(repo: str, since: datetime.date, until: datetime.date) -> "int | None":
    """
    Count commits to `repo` in [since, until) without paginating through
    every commit: request per_page=1 and read the total off the
    pagination Link header's rel="last" page number (since per_page=1,
    that page number equals the total count). If GitHub returns no Link
    header at all — true whenever the range has 0 or 1 commits, since
    there's nothing to paginate — fall back to len() of the one page we
    got.
    """
    resp = _get(
        f"{API_ROOT}/repos/{repo}/commits",
        params={
            "since": since.isoformat() + "T00:00:00Z",
            "until": until.isoformat() + "T00:00:00Z",
            "per_page": 1,
        },
    )
    if resp is None:
        return None

    link = resp.headers.get("Link")
    if not link:
        return len(resp.json())

    for part in link.split(","):
        if 'rel="last"' in part:
            last_url = part[part.index("<") + 1 : part.index(">")]
            page = parse_qs(urlparse(last_url).query).get("page", ["1"])[0]
            return int(page)

    return len(resp.json())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 3.**

---

### Task 3: Weekly windows + 2-year commit backfill (`collect.py`)

**Files:**
- Modify: `D:\news scrapper\GitHub\collect.py`
- Modify: `D:\news scrapper\GitHub\test_collect.py`

**Interfaces:**
- Consumes: `_count_commits_in_range(repo, since, until) -> int | None` from Task 2.
- Produces: `_week_windows(years: int) -> list[tuple[datetime.date, datetime.date]]`, `REPOS: list[str]`, `HISTORY_YEARS: int`, `backfill_commit_history(repos: list[str] = None, years: int = HISTORY_YEARS) -> list[dict]`. Task 4's `collect()` reuses `_week_windows` and `REPOS`; `storage.py`'s tests (Task 5) consume the record shape this produces.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_collect.py
import datetime as dt


def test_week_windows_covers_full_range_with_no_gaps():
    windows = collect._week_windows(years=1)

    for i in range(1, len(windows)):
        assert windows[i][0] == windows[i - 1][1]
    assert windows[0][0] == dt.date.today() - dt.timedelta(days=365)
    assert windows[-1][1] == dt.date.today()


@patch("collect._count_commits_in_range")
def test_backfill_returns_one_record_per_window_per_repo(mock_count):
    mock_count.return_value = 5

    records = collect.backfill_commit_history(repos=["x/y"], years=1)

    assert len(records) == len(collect._week_windows(years=1))
    assert all(r["repo"] == "x/y" and r["metric"] == "commits" for r in records)


@patch("collect._count_commits_in_range")
def test_backfill_marks_only_the_last_window_as_partial(mock_count):
    mock_count.return_value = 5

    records = collect.backfill_commit_history(repos=["x/y"], years=1)

    assert [r["is_partial"] for r in records].count(True) == 1
    assert records[-1]["is_partial"] is True


@patch("collect._count_commits_in_range")
def test_backfill_skips_failed_weeks_without_crashing(mock_count):
    mock_count.side_effect = [None, 5, 5]

    records = collect.backfill_commit_history(repos=["x/y"], years=1)[:3]

    assert len(records) == 2  # the None week is skipped, not recorded


@patch("collect._count_commits_in_range")
def test_backfill_skips_one_bad_repo_without_losing_the_rest(mock_count):
    def side_effect(repo, since, until):
        return None if repo == "bad/repo" else 3

    mock_count.side_effect = side_effect

    records = collect.backfill_commit_history(repos=["bad/repo", "good/repo"], years=1)

    assert {r["repo"] for r in records} == {"good/repo"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect.py -v`
Expected: FAIL — `AttributeError: module 'collect' has no attribute '_week_windows'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to collect.py

REPOS = [
    "bitcoin/bitcoin",
    "ethereum/go-ethereum",
    "bnb-chain/bsc",
    "ripple/rippled",
    "solana-labs/solana",
]

HISTORY_YEARS = 2


def _week_windows(years: int = HISTORY_YEARS) -> "list[tuple[datetime.date, datetime.date]]":
    """
    [since, until) week-long windows covering the last `years` years,
    oldest first, ending today. The last window is the current,
    still-in-progress week.
    """
    end = datetime.date.today()
    start = end - datetime.timedelta(days=365 * years)
    windows = []
    cursor = start
    while cursor < end:
        window_end = min(cursor + datetime.timedelta(days=7), end)
        windows.append((cursor, window_end))
        cursor = window_end
    return windows


def backfill_commit_history(repos: "list[str] | None" = None, years: int = HISTORY_YEARS) -> "list[dict]":
    """
    One-time historical fetch: commits only, ~104 weekly records per
    repo. Run this manually once before the daily pipeline starts —
    star/fork history can't be backfilled at all (see design.md), and
    collect() only re-checks the current week going forward to avoid
    re-fetching ~104 unchanging weeks every day.
    """
    repos = repos or REPOS
    windows = _week_windows(years)
    records = []

    for repo in repos:
        try:
            for since, until in windows:
                count = _count_commits_in_range(repo, since, until)
                if count is None:
                    logger.warning("Skipping week %s for %s: request failed", since, repo)
                    continue
                records.append(
                    {
                        "repo": repo,
                        "metric": "commits",
                        "date": since.isoformat(),
                        "commits": count,
                        "is_partial": until == windows[-1][1],
                    }
                )
        except RuntimeError:
            logger.error("Aborting backfill early: rate limit exhausted.")
            break

    return records
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect.py -v`
Expected: PASS (14 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 4.**

---

### Task 4: Star/fork snapshot + daily `collect()` (`collect.py`)

**Files:**
- Modify: `D:\news scrapper\GitHub\collect.py`
- Modify: `D:\news scrapper\GitHub\test_collect.py`

**Interfaces:**
- Consumes: `_get`, `_count_commits_in_range`, `_week_windows`, `REPOS` from Tasks 1–3.
- Produces: `_snapshot(repo: str) -> dict | None`, `collect(repos: list[str] = None) -> list[dict]`. `storage.py` (Task 5) and `export_excel.py` (Task 6) consume this record shape; `README.md` (Task 7) documents calling this daily.

- [ ] **Step 1: Write the failing tests**

```python
# add to test_collect.py

@patch("collect.requests.get")
def test_snapshot_returns_stars_and_forks(mock_get):
    mock_get.return_value = _fake_response(json_data={"stargazers_count": 100, "forks_count": 20})

    snap = collect._snapshot("x/y")

    assert snap == {"stars": 100, "forks": 20}


@patch("collect.requests.get")
def test_snapshot_returns_none_on_failure(mock_get):
    mock_get.return_value = _fake_response(status_code=404)

    snap = collect._snapshot("x/y")

    assert snap is None


@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_returns_snapshot_and_commit_rows_per_repo(mock_snapshot, mock_count):
    mock_snapshot.return_value = {"stars": 100, "forks": 20}
    mock_count.return_value = 4

    records = collect.collect(repos=["x/y"])

    metrics = {r["metric"] for r in records}
    assert metrics == {"snapshot", "commits"}
    snap_row = next(r for r in records if r["metric"] == "snapshot")
    assert snap_row["stars"] == 100 and snap_row["forks"] == 20
    commit_row = next(r for r in records if r["metric"] == "commits")
    assert commit_row["commits"] == 4
    assert commit_row["is_partial"] is True


@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_skips_snapshot_when_it_fails_but_keeps_commits(mock_snapshot, mock_count):
    mock_snapshot.return_value = None
    mock_count.return_value = 4

    records = collect.collect(repos=["x/y"])

    assert all(r["metric"] != "snapshot" for r in records)
    assert any(r["metric"] == "commits" for r in records)


@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_current_week_date_matches_backfills_last_window(mock_snapshot, mock_count):
    mock_snapshot.return_value = {"stars": 1, "forks": 1}
    mock_count.return_value = 1

    records = collect.collect(repos=["x/y"])

    commit_row = next(r for r in records if r["metric"] == "commits")
    expected_since = collect._week_windows(collect.HISTORY_YEARS)[-1][0]
    assert commit_row["date"] == expected_since.isoformat()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_collect.py -v`
Expected: FAIL — `AttributeError: module 'collect' has no attribute '_snapshot'`

- [ ] **Step 3: Write minimal implementation**

```python
# add to collect.py
import time


def _snapshot(repo: str) -> "dict | None":
    resp = _get(f"{API_ROOT}/repos/{repo}")
    if resp is None:
        return None
    data = resp.json()
    return {"stars": data["stargazers_count"], "forks": data["forks_count"]}


def collect(repos: "list[str] | None" = None) -> "list[dict]":
    """
    Daily run: a star/fork snapshot dated today, plus a re-check of the
    current week's commit count. Reuses _week_windows()'s last window
    (rather than an independently-computed "last 7 days") so the date
    lines up exactly with whatever backfill_commit_history() wrote for
    that same week — otherwise the two would produce adjacent rows
    instead of the storage layer correctly upserting the same row.
    """
    repos = repos or REPOS
    today = datetime.date.today()
    current_since, current_until = _week_windows(HISTORY_YEARS)[-1]
    records = []

    for repo in repos:
        snap = _snapshot(repo)
        if snap is not None:
            records.append(
                {
                    "repo": repo,
                    "metric": "snapshot",
                    "date": today.isoformat(),
                    "stars": snap["stars"],
                    "forks": snap["forks"],
                }
            )

        count = _count_commits_in_range(repo, current_since, current_until)
        if count is not None:
            records.append(
                {
                    "repo": repo,
                    "metric": "commits",
                    "date": current_since.isoformat(),
                    "commits": count,
                    "is_partial": True,
                }
            )

        time.sleep(1)  # be polite between repos

    return records
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_collect.py -v`
Expected: PASS (19 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 5.**

---

### Task 5: SQLite storage (`storage.py`)

**Files:**
- Create: `D:\news scrapper\GitHub\storage.py`
- Create: `D:\news scrapper\GitHub\test_storage.py`

**Interfaces:**
- Consumes: record dicts shaped like Task 3/4's output (`repo`, `date`, `metric`, plus `stars`/`forks` or `commits`/`is_partial` depending on `metric`).
- Produces: `get_connection(db_path: str = DB_PATH) -> sqlite3.Connection`, `upsert_raw(conn, records: list[dict]) -> None`. `export_excel.py` (Task 6) and `README.md` (Task 7) both read from the `github_raw`/`github_features` tables this creates.

- [ ] **Step 1: Write the failing tests**

```python
# test_storage.py
"""
test_storage.py — Stage 8: Testing (storage.py)

Run with: pytest test_storage.py
"""

from storage import get_connection, upsert_raw


def test_upsert_raw_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False}
    ]

    upsert_raw(conn, records)
    upsert_raw(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_raw_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_raw(conn, [{"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": True}])
    upsert_raw(conn, [{"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 9, "is_partial": False}])

    row = conn.execute("SELECT commits, is_partial FROM github_raw").fetchone()

    assert row == (9, 0)
    conn.close()


def test_upsert_raw_stores_snapshot_and_commit_rows_together():
    conn = get_connection(":memory:")

    upsert_raw(
        conn,
        [
            {"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20},
            {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    assert count == 2
    conn.close()


def test_features_table_exists_but_starts_empty():
    conn = get_connection(":memory:")

    count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]

    assert count == 0
    conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'storage'`

- [ ] **Step 3: Write minimal implementation**

```python
# storage.py
"""
storage.py — Stage 5: Data Storage

SQLite storage layer for the GitHub alt-data pipeline. Two tables:
  - github_raw      : what collect.py returned, one row per (repo, date,
                       metric). Whichever columns don't apply to a given
                       metric (e.g. stars/forks on a "commits" row) stay
                       NULL.
  - github_features : reserved for transform.py's output (rolling avg,
                       pct change, z-score). Schema only for now —
                       transform.py doesn't exist yet (see design.md's
                       "Open items for later stages"), so this table
                       stays empty until that stage is implemented.

Mirrors ../Google trends/storage.py's upsert-on-conflict pattern so
repeated pipeline runs never duplicate rows.
"""

import sqlite3
from datetime import datetime, timezone

DB_PATH = "github_data.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS github_raw (
            repo       TEXT NOT NULL,
            date       TEXT NOT NULL,
            metric     TEXT NOT NULL,
            stars      INTEGER,
            forks      INTEGER,
            commits    INTEGER,
            is_partial INTEGER,
            fetched_at TEXT,
            PRIMARY KEY (repo, date, metric)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS github_features (
            repo         TEXT NOT NULL,
            date         TEXT NOT NULL,
            metric       TEXT NOT NULL,
            value        REAL,
            value_norm   REAL,
            rolling_avg  REAL,
            pct_change   REAL,
            zscore       REAL,
            processed_at TEXT,
            PRIMARY KEY (repo, date, metric)
        )
        """
    )
    conn.commit()
    return conn


def upsert_raw(conn: sqlite3.Connection, records: "list[dict]") -> None:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO github_raw (repo, date, metric, stars, forks, commits, is_partial, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo, date, metric) DO UPDATE SET
                stars=excluded.stars,
                forks=excluded.forks,
                commits=excluded.commits,
                is_partial=excluded.is_partial,
                fetched_at=excluded.fetched_at
            """,
            (
                r["repo"],
                r["date"],
                r["metric"],
                r.get("stars"),
                r.get("forks"),
                r.get("commits"),
                int(r["is_partial"]) if "is_partial" in r else None,
                now,
            ),
        )
    conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_storage.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 6.**

---

### Task 6: Excel export (`export_excel.py`)

**Files:**
- Create: `D:\news scrapper\GitHub\export_excel.py`
- Create: `D:\news scrapper\GitHub\test_export.py`

**Interfaces:**
- Consumes: `get_connection`, `upsert_raw` from Task 5.
- Produces: `export_to_excel(conn: sqlite3.Connection, excel_path: str = EXCEL_PATH) -> None`. `README.md` (Task 7) documents running this after a collection run.

- [ ] **Step 1: Write the failing test**

```python
# test_export.py
"""
test_export.py — Stage 8: Testing (export_excel.py)

Run with: pytest test_export.py
"""

import pandas as pd

from storage import get_connection, upsert_raw
from export_excel import export_to_excel


def test_export_writes_raw_and_features_sheets(tmp_path):
    conn = get_connection(":memory:")
    upsert_raw(
        conn,
        [{"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20}],
    )
    out_path = tmp_path / "out.xlsx"

    export_to_excel(conn, excel_path=str(out_path))

    assert out_path.exists()
    raw = pd.read_excel(out_path, sheet_name="raw")
    assert len(raw) == 1
    features = pd.read_excel(out_path, sheet_name="features")
    assert len(features) == 0
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest test_export.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'export_excel'`

- [ ] **Step 3: Write minimal implementation**

```python
# export_excel.py
"""
export_excel.py — Excel export

Exports the current contents of the GitHub alt-data database to an
Excel workbook (github_data.xlsx by default) — one sheet per table —
for anyone on the team who'd rather look at a spreadsheet than query
SQLite directly.

Same design choice as ../Google trends/export_excel.py: regenerates the
whole file from SQLite on every run rather than merging into an
existing .xlsx — SQLite already handles dedup/upserts (see storage.py).

IMPORTANT: close github_data.xlsx in Excel before running this — Excel
locks the file while it's open, and writing to it will raise
PermissionError.
"""

import logging
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)

EXCEL_PATH = "github_data.xlsx"


def export_to_excel(conn: sqlite3.Connection, excel_path: str = EXCEL_PATH) -> None:
    raw_df = pd.read_sql_query("SELECT * FROM github_raw ORDER BY repo, date, metric", conn)
    features_df = pd.read_sql_query(
        "SELECT * FROM github_features ORDER BY repo, date, metric", conn
    )

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            raw_df.to_excel(writer, sheet_name="raw", index=False)
            features_df.to_excel(writer, sheet_name="features", index=False)
        logger.info("Exported %d raw rows to %s", len(raw_df), excel_path)
    except PermissionError:
        logger.error(
            "Could not write %s — it's probably still open in Excel. Close it and re-run.",
            excel_path,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest test_export.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: No git repo — skip commit. Confirm the file is saved and move to Task 7.**

---

### Task 7: Dependencies + README

**Files:**
- Create: `D:\news scrapper\GitHub\requirements.txt`
- Create: `D:\news scrapper\GitHub\README.md`

**Interfaces:**
- Consumes: everything from Tasks 1–6 (documents how to install, set `GITHUB_TOKEN`, and run backfill/collect/export manually).
- Produces: nothing further consumes this — it's the last task in this plan.

- [ ] **Step 1: Create `requirements.txt`**

```
requests
pandas
openpyxl
pytest
```

- [ ] **Step 2: Verify dependencies install cleanly**

Run: `pip install -r requirements.txt`
Expected: all four packages install (or report already satisfied) with no errors.

- [ ] **Step 3: Write `README.md`**

```markdown
# GitHub Alt-Data Pipeline — Member 11 (FundForge)

Tracks commit activity, stars, and forks for five major blockchain
ecosystem repos, as a developer-activity signal pairing with the
Blockchain Wallet Metrics source. See `design.md` for the full design
rationale (why stars/forks can't be backfilled, the commit-counting
trick, etc.).

**Status:** `collect.py`, `storage.py`, and `export_excel.py` are
implemented and tested. `clean.py`, `transform.py`, `pipeline.py`, and
`scheduler.py` are not yet built — see `design.md`'s "Open items for
later stages".

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

**Daily collection (what the eventual `scheduler.py` will call):**

```python
from collect import collect
from storage import get_connection, upsert_raw

conn = get_connection()
upsert_raw(conn, collect())
conn.close()
```

**Export to Excel for handoff:**

```python
from storage import get_connection
from export_excel import export_to_excel

conn = get_connection()
export_to_excel(conn)  # writes github_data.xlsx
conn.close()
```

## Testing

```bash
pytest test_collect.py test_storage.py test_export.py -v
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
| `is_partial` | int (0/1), nullable | `commits` rows only — true for the current, still-accumulating week |
| `fetched_at` | text (ISO timestamp) | when this row was last written |

`github_features` exists (same key) but stays empty until `transform.py`
is built.
```

- [ ] **Step 4: No git repo — skip commit. Implementation plan complete.**
