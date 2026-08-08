"""
test_collect.py — Stage 8: Testing (collect.py)

Mocks requests.get so these tests never touch the network or the real
GitHub API. Run with: pytest test_collect.py
"""

import datetime as dt
from datetime import date
from unittest.mock import Mock, patch

import pandas as pd

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


def test_week_windows_covers_full_range_with_no_gaps():
    today = date(2026, 7, 31)  # a Friday

    windows = collect._week_windows(years=1, today=today)

    # no gaps or overlaps between any consecutive windows
    for i in range(1, len(windows)):
        assert windows[i][0] == windows[i - 1][1]
    # every historical window (all but the last, still-growing one) is a
    # full, untruncated 7-day span
    for since, until in windows[:-1]:
        assert (until - since).days == 7
    # covers at least the requested `years` years of history
    assert windows[0][0] <= today - dt.timedelta(days=365)
    # the last window is the current, still-in-progress week
    assert windows[-1][1] == today + dt.timedelta(days=1)


def test_week_windows_last_window_since_stable_within_same_calendar_week():
    # Tuesday and Thursday of the same week (2026-07-27 is that week's Monday)
    tuesday = date(2026, 7, 28)
    thursday = date(2026, 7, 30)

    since_tue = collect._week_windows(years=1, today=tuesday)[-1][0]
    since_thu = collect._week_windows(years=1, today=thursday)[-1][0]

    assert since_tue == since_thu == date(2026, 7, 27)


def test_week_windows_last_window_since_advances_the_following_week():
    this_week_tuesday = date(2026, 7, 28)
    next_week_tuesday = date(2026, 8, 4)

    since_this_week = collect._week_windows(years=1, today=this_week_tuesday)[-1][0]
    since_next_week = collect._week_windows(years=1, today=next_week_tuesday)[-1][0]

    assert since_next_week == since_this_week + dt.timedelta(days=7)


def test_week_windows_last_window_until_grows_with_today():
    today = date(2026, 7, 30)

    windows = collect._week_windows(years=1, today=today)

    assert windows[-1][1] == today + dt.timedelta(days=1)


def test_week_windows_default_today_is_real_today():
    # no `today` kwarg -> behaves exactly as before (uses the real clock)
    windows = collect._week_windows(years=1)
    real_today = dt.date.today()
    current_week_start = real_today - dt.timedelta(days=real_today.weekday())

    assert windows[-1] == (current_week_start, real_today + dt.timedelta(days=1))


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
def test_backfill_returns_one_record_per_window_per_repo(mock_count, mock_sleep):
    mock_count.return_value = 5

    records = collect.backfill_commit_history(repos=["x/y"], years=1)

    assert len(records) == len(collect._week_windows(years=1))
    assert all(r["repo"] == "x/y" and r["metric"] == "commits" for r in records)


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
def test_backfill_marks_only_the_last_window_as_partial(mock_count, mock_sleep):
    mock_count.return_value = 5

    records = collect.backfill_commit_history(repos=["x/y"], years=1)

    assert [r["is_partial"] for r in records].count(True) == 1
    assert records[-1]["is_partial"] is True


@patch("collect.time.sleep")
@patch("collect._week_windows")
@patch("collect._count_commits_in_range")
def test_backfill_skips_failed_weeks_without_crashing(mock_count, mock_windows, mock_sleep):
    mock_windows.return_value = [
        (dt.date(2026, 7, 1), dt.date(2026, 7, 8)),
        (dt.date(2026, 7, 8), dt.date(2026, 7, 15)),
        (dt.date(2026, 7, 15), dt.date(2026, 7, 31)),
    ]
    mock_count.side_effect = [None, 5, 5]

    records = collect.backfill_commit_history(repos=["x/y"], years=1)

    assert len(records) == 2  # the None week is skipped, not recorded


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
def test_backfill_skips_one_bad_repo_without_losing_the_rest(mock_count, mock_sleep):
    def side_effect(repo, since, until):
        return None if repo == "bad/repo" else 3

    mock_count.side_effect = side_effect

    records = collect.backfill_commit_history(repos=["bad/repo", "good/repo"], years=1)

    assert {r["repo"] for r in records} == {"good/repo"}


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
def test_backfill_sleeps_once_per_window_request(mock_count, mock_sleep):
    # backfill fires up to ~525 requests (104 weeks x 5 repos) - unlike
    # collect()'s ~10 requests/day, this is the run that actually needs
    # pacing against GitHub's unauthenticated 60 req/hr rate limit.
    mock_count.return_value = 5

    records = collect.backfill_commit_history(repos=["x/y"], years=1)

    assert mock_sleep.call_count == len(records)
    mock_sleep.assert_called_with(1)


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
def test_backfill_sleeps_even_when_a_window_request_fails(mock_count, mock_sleep):
    mock_count.return_value = None

    collect.backfill_commit_history(repos=["x/y"], years=1)

    assert mock_sleep.call_count == len(collect._week_windows(years=1))


@patch("collect.requests.get")
def test_snapshot_returns_stars_and_forks(mock_get):
    mock_get.return_value = _fake_response(json_data={"stargazers_count": 100, "forks_count": 20})

    snap = collect._snapshot("x/y")

    assert snap["stars"] == 100
    assert snap["forks"] == 20


@patch("collect.requests.get")
def test_snapshot_includes_raw_response_for_debugging(mock_get):
    mock_get.return_value = _fake_response(json_data={"stargazers_count": 100, "forks_count": 20})

    snap = collect._snapshot("x/y")

    assert snap["raw"] == {"stargazers_count": 100, "forks_count": 20}


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
    assert snap_row["is_partial"] is False
    commit_row = next(r for r in records if r["metric"] == "commits")
    assert commit_row["commits"] == 4
    assert commit_row["is_partial"] is True


@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_attaches_raw_response_to_snapshot_and_commit_rows(mock_snapshot, mock_count):
    mock_snapshot.return_value = {"stars": 100, "forks": 20, "raw": {"stargazers_count": 100, "forks_count": 20}}
    mock_count.return_value = 4

    records = collect.collect(repos=["x/y"])

    snapshot_record = next(r for r in records if r["metric"] == "snapshot")
    commit_records = [r for r in records if r["metric"] == "commits"]

    assert snapshot_record["raw_response"] == {"stargazers_count": 100, "forks_count": 20}
    assert all("raw_response" in r and "endpoint" in r["raw_response"] for r in commit_records)


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


@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_records_survive_clean_pys_drop_partial_rows_filter(mock_snapshot, mock_count):
    # design.md: clean.py drops partial rows via `df[~df["is_partial"]]`
    # across the *combined* snapshot+commit records. That blows up with
    # a TypeError if any record (e.g. a snapshot row) is missing the
    # "is_partial" key, since the column then comes out as NaN/object
    # dtype instead of a clean boolean column.
    mock_snapshot.return_value = {"stars": 100, "forks": 20}
    mock_count.return_value = 4

    records = collect.collect(repos=["x/y"])

    df = pd.DataFrame.from_records(records)
    assert df["is_partial"].dtype == bool
    kept = df[~df["is_partial"]]
    assert (kept["metric"] == "snapshot").any()


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_includes_finalized_previous_week_commit_row(mock_snapshot, mock_count, mock_sleep):
    mock_snapshot.return_value = {"stars": 1, "forks": 1}
    windows = collect._week_windows(collect.HISTORY_YEARS)
    current_since, current_until = windows[-1]
    prev_since, prev_until = windows[-2]

    def side_effect(repo, since, until):
        if (since, until) == (current_since, current_until):
            return 4
        if (since, until) == (prev_since, prev_until):
            return 9
        return None

    mock_count.side_effect = side_effect

    records = collect.collect(repos=["x/y"])

    commit_rows = [r for r in records if r["metric"] == "commits"]
    assert len(commit_rows) == 2
    prev_row = next(r for r in commit_rows if r["date"] == prev_since.isoformat())
    assert prev_row["commits"] == 9
    assert prev_row["is_partial"] is False
    current_row = next(r for r in commit_rows if r["date"] == current_since.isoformat())
    assert current_row["is_partial"] is True


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_previous_week_date_matches_backfills_second_to_last_window(mock_snapshot, mock_count, mock_sleep):
    mock_snapshot.return_value = {"stars": 1, "forks": 1}
    mock_count.return_value = 1

    records = collect.collect(repos=["x/y"])

    prev_row = next(r for r in records if r["metric"] == "commits" and r["is_partial"] is False)
    expected_since = collect._week_windows(collect.HISTORY_YEARS)[-2][0]
    assert prev_row["date"] == expected_since.isoformat()


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_skips_previous_week_row_when_its_fetch_fails_but_keeps_the_rest(
    mock_snapshot, mock_count, mock_sleep, caplog
):
    mock_snapshot.return_value = {"stars": 1, "forks": 1}
    windows = collect._week_windows(collect.HISTORY_YEARS)
    current_since, current_until = windows[-1]
    prev_since, prev_until = windows[-2]

    def side_effect(repo, since, until):
        if (since, until) == (current_since, current_until):
            return 4
        if (since, until) == (prev_since, prev_until):
            return None
        return 999

    mock_count.side_effect = side_effect

    with caplog.at_level("WARNING"):
        records = collect.collect(repos=["x/y"])

    assert any(r["metric"] == "snapshot" for r in records)
    current_rows = [r for r in records if r["metric"] == "commits" and r["is_partial"] is True]
    assert len(current_rows) == 1
    assert not any(r["metric"] == "commits" and r["is_partial"] is False for r in records)
    assert "warning" in caplog.text.lower()


@patch("collect.time.sleep")
@patch("collect._count_commits_in_range")
@patch("collect._snapshot")
def test_collect_previous_week_row_finalizes_existing_row_via_storage_upsert(mock_snapshot, mock_count, mock_sleep):
    import storage

    mock_snapshot.return_value = {"stars": 1, "forks": 1}
    mock_count.return_value = 7

    conn = storage.get_connection(":memory:")
    prev_since = collect._week_windows(collect.HISTORY_YEARS)[-2][0]

    # Simulate what backfill_commit_history() or a prior day's collect() run
    # already wrote for that same week: a partial row.
    storage.upsert_raw(
        conn,
        [{"repo": "x/y", "date": prev_since.isoformat(), "metric": "commits", "commits": 7, "is_partial": True}],
    )

    records = collect.collect(repos=["x/y"])
    storage.upsert_raw(conn, records)

    rows = conn.execute(
        "SELECT date, commits, is_partial FROM github_raw WHERE metric = 'commits' AND date = ?",
        (prev_since.isoformat(),),
    ).fetchall()

    assert len(rows) == 1  # same row updated in place, not duplicated
    assert rows[0][2] == 0  # is_partial flipped to False
    conn.close()
