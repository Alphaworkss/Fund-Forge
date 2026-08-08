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

import datetime
import logging
import os
import time
from urllib.parse import parse_qs, urlparse

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


REPOS = [
    "bitcoin/bitcoin",
    "ethereum/go-ethereum",
    "bnb-chain/bsc",
    "ripple/rippled",
    "solana-labs/solana",
]

HISTORY_YEARS = 2


def _week_windows(
    years: int = HISTORY_YEARS, *, today: "datetime.date | None" = None
) -> "list[tuple[datetime.date, datetime.date]]":
    """
    [since, until) week-long windows covering (at least) the last
    `years` years, oldest first.

    The grid is anchored to the Monday of the CURRENT calendar week
    (`current_week_start`), not to `today` directly, so the whole grid
    stays fixed across every day of the same week — only the last
    window's `until` moves. This matters because storage.py upserts on
    (repo, date, metric): if the grid shifted daily (as a naive
    `today`-anchored version would), the "current week" row collect()
    writes would land on a different date every day and would never
    accumulate into a single upserted row — it would just keep creating
    new partial rows, none of which ever accumulate into a usable,
    non-partial row.

    Every historical window (all but the last) is a full, untruncated
    7-day span: the total historical span is rounded UP to the nearest
    whole number of weeks, so coverage is `years` years or a few days
    more — never a truncated, sub-7-day window (which would happen if
    365 * years were used directly, since that's not a multiple of 7).

    The last window is the current, still-in-progress week: its
    `since` is `current_week_start` (stable all week), and its `until`
    is `today + 1 day` (the bound is exclusive), which grows by one day
    at a time as the week progresses.

    `today` is exposed as a keyword-only override purely for testing
    grid stability/advancement across specific dates; all real callers
    omit it and get `datetime.date.today()`.
    """
    today = today or datetime.date.today()
    current_week_start = today - datetime.timedelta(days=today.weekday())

    total_days = 365 * years
    weeks_count = -(-total_days // 7)  # ceil division: round up to whole weeks
    start = current_week_start - datetime.timedelta(days=7 * weeks_count)

    windows = []
    cursor = start
    while cursor < current_week_start:
        windows.append((cursor, cursor + datetime.timedelta(days=7)))
        cursor += datetime.timedelta(days=7)
    windows.append((current_week_start, today + datetime.timedelta(days=1)))
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
                time.sleep(1)  # be polite: this loop can fire hundreds of requests
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


def _snapshot(repo: str) -> "dict | None":
    resp = _get(f"{API_ROOT}/repos/{repo}")
    if resp is None:
        return None
    data = resp.json()
    return {"stars": data["stargazers_count"], "forks": data["forks_count"], "raw": data}


def collect(repos: "list[str] | None" = None) -> "list[dict]":
    """
    Daily run: a star/fork snapshot dated today, a re-check of the
    current week's commit count, and a finalization re-fetch of the
    immediately-preceding, now-fully-completed week's commit count.

    Reuses _week_windows()'s last two windows (rather than
    independently-computed date ranges) so both dates line up exactly
    with whatever backfill_commit_history() — or a prior day's
    collect() run — already wrote for those same weeks: [-1] is the
    still-accumulating current week (already handled before this fix),
    [-2] is the week immediately before it, which is now fully over.
    Re-fetching [-2] and writing it with is_partial=False upserts onto
    the existing (repo, date, metric) row from backfill/a prior run
    (which was written with is_partial=True), flipping it in place
    instead of creating a new row. Without this, no week's commit
    count — other than the one-time backfill's rows — would ever end
    up with is_partial=False, and a future clean.py that drops all
    is_partial=True rows before computing features would never see any
    of collect()'s daily commit data.
    """
    repos = repos or REPOS
    today = datetime.date.today()
    windows = _week_windows(HISTORY_YEARS)
    current_since, current_until = windows[-1]
    prev_window = windows[-2] if len(windows) >= 2 else None
    records = []

    try:
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
                        "is_partial": False,
                        "raw_response": snap.get("raw"),
                    }
                )
            else:
                logger.warning("Skipping snapshot for %s: request failed", repo)

            count = _count_commits_in_range(repo, current_since, current_until)
            if count is not None:
                records.append(
                    {
                        "repo": repo,
                        "metric": "commits",
                        "date": current_since.isoformat(),
                        "commits": count,
                        "is_partial": True,
                        "raw_response": {
                            "endpoint": f"{API_ROOT}/repos/{repo}/commits",
                            "since": current_since.isoformat() + "T00:00:00Z",
                            "until": current_until.isoformat() + "T00:00:00Z",
                            "per_page": 1,
                            "counted_via": "pagination Link header page count",
                        },
                    }
                )
            else:
                logger.warning("Skipping commit count for %s (week %s): request failed", repo, current_since)

            if prev_window is not None:
                prev_since, prev_until = prev_window
                prev_count = _count_commits_in_range(repo, prev_since, prev_until)
                if prev_count is not None:
                    records.append(
                        {
                            "repo": repo,
                            "metric": "commits",
                            "date": prev_since.isoformat(),
                            "commits": prev_count,
                            "is_partial": False,
                            "raw_response": {
                                "endpoint": f"{API_ROOT}/repos/{repo}/commits",
                                "since": prev_since.isoformat() + "T00:00:00Z",
                                "until": prev_until.isoformat() + "T00:00:00Z",
                                "per_page": 1,
                                "counted_via": "pagination Link header page count",
                            },
                        }
                    )
                else:
                    logger.warning(
                        "Skipping previous-week finalization for %s (week %s): request failed", repo, prev_since
                    )

            time.sleep(1)  # be polite between repos
    except RuntimeError:
        logger.error("Aborting collect early: rate limit exhausted.")

    return records
