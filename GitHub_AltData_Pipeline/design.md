# GitHub Alt-Data Pipeline — Design

Part of Member 11's Alternative Data Pipeline (FundForge). Same 8-stage
shape as the Google Trends pipeline in `../Google trends`; this document
covers the pieces that differ from that precedent.

## Sources tracked

Five major blockchain/crypto-ecosystem repos, used as a proxy for
ecosystem development activity (pairs with the Blockchain Wallet Metrics
source):

- `bitcoin/bitcoin`
- `ethereum/go-ethereum`
- `bnb-chain/bsc`
- `ripple/rippled`
- `solana-labs/solana`

**Note on `solana-labs/solana`:** Active Solana Labs development has
moved to `anza-xyz/agave`. This repo shows negligible commit activity
(mean 0.019 commits/week, with 105 of 106 tracked weeks at zero
commits), so z-score anomalies should be interpreted cautiously—isolated
activity weeks are noise atop a near-constant baseline.

## Metrics collected

- **Stars** and **forks** — current totals only. GitHub's API has no
  historical count endpoint for either (`stargazers_count`/
  `forks_count` on `GET /repos/{owner}/{repo}` only ever reflect *today*).
  Reconstructing history would require enumerating every individual
  stargazer/fork with its timestamp — decided against (see Decisions
  below). These metrics start accumulating from the pipeline's first
  run forward, with no backfilled past.
- **Commits per week** — GitHub's `stats/commit_activity` endpoint only
  covers the last 52 weeks, insufficient for the required 2-year
  history. Instead: `GET /repos/{owner}/{repo}/commits?since=X&until=Y&per_page=1`
  per week-long window, reading the total commit count off the
  pagination `Link` header's `rel="last"` page number (since
  `per_page=1`, the last page number equals the total count). If no
  `Link` header is present, the count is just the length of the
  returned array (0 or 1 commit that week). This avoids paginating
  through every individual commit.

## `collect.py` — two entry points

```python
def backfill_commit_history(years: int = 2) -> list[dict]:
    """One-time historical fetch: commits only, ~104 weeks per repo."""

def collect() -> list[dict]:
    """Daily run: star/fork snapshot (1 API call per repo, since
    GET /repos/{owner}/{repo} returns both stargazers_count and
    forks_count together) + current week's commit count (1 API call
    per repo via the same Link-header trick, re-checked in case the
    in-progress week's count has moved since yesterday)."""
```

Both return the same flat record shape, tagged by `metric` so
`clean.py` can branch:

```python
# snapshot record (daily, no history)
{"repo": "bitcoin/bitcoin", "metric": "snapshot", "date": "2026-07-30",
 "stars": 83000, "forks": 37500}

# weekly commit record (2yr backfill + daily current-week refresh)
{"repo": "bitcoin/bitcoin", "metric": "commits", "date": "2026-07-27",
 "commits": 42, "is_partial": False}
```

`is_partial` is `True` only for the current, still-accumulating week —
same concept as Google Trends' `isPartial`, so `clean.py`'s existing
"drop partial rows" logic applies unmodified.

**Why `collect()` doesn't re-pull all 104 weeks daily** (unlike Google
Trends, which re-pulls its full window every run because Trends' own
normalization can shift retroactively): completed weekly commit counts
on GitHub are effectively immutable barring rare history rewrites, so
daily runs only re-check the current (partial) week. `backfill_commit_history()`
is called once, manually, before regular daily runs start.

## Auth & rate limits

Personal Access Token (public-read scope, no special permissions) via
an environment variable, sent as an `Authorization` header. Budget:
backfill is ~520 requests one-time (104 weeks x 5 repos); daily runs
are ~10 requests (5 star/fork snapshots + 5 current-week commit
checks) against a 5,000/hr authenticated limit — no throttling needed.

## Error handling

- Per-repo isolation: a failing repo (404, network error, unexpected
  response) logs a warning and is skipped; it doesn't abort the run
  for the other four repos.
- Rate-limit/abuse-detection responses are logged and the run stops
  early rather than continuing to hammer a throttled endpoint.

## Storage & export

Same architecture as Google Trends, unchanged:

- `storage.py` — SQLite is the source of truth. Two tables mirroring
  the Trends pattern: `github_raw` and `github_features`, both keyed
  on `PRIMARY KEY (repo, date, metric)` with `ON CONFLICT ... DO
  UPDATE` upserts, so re-runs never duplicate rows. `upsert_features()`
  (see below) is a direct 3-column-key adaptation of Google Trends'
  `upsert_features` — same `ON CONFLICT DO UPDATE` shape already used
  by `upsert_raw`.
- `export_excel.py` — a separate, manually-run script that dumps the
  SQLite tables to `.xlsx` for handoff to teammates, matching Google
  Trends' `alt_data.xlsx` exactly (not auto-wired into the scheduled
  run).

## `clean.py` — cleaning

Deliberately stays in the *raw* shape — no reshaping here, that's
`transform.py`'s job. `clean(records: list[dict]) -> pd.DataFrame`
returns the same columns as `github_raw` (`repo, date, metric, stars,
forks, commits, is_partial`), just fewer rows:

- Drop rows where `is_partial` is `True` — works cleanly now that
  every row (snapshot and commits alike) always carries a real
  boolean, per the `is_partial` fix made during `collect.py`'s final
  review.
- Drop duplicate `(repo, date, metric)` triples, keep last — the
  3-column analog of Google Trends' `(keyword, date)` dedup.
- **No zero-fill/forward-fill step**, unlike Google Trends' `clean.py`.
  A `0` here is a real data point (a quiet commit week), not evidence
  of a reporting gap the way Trends' interest score dropping to 0
  often is — GitHub's commit-count endpoint doesn't have that failure
  mode, and stars/forks realistically never hit 0 for these repos.

## `transform.py` — normalization + feature extraction

Two responsibilities, run in order:

1. **Melt.** `collect.py`'s raw taxonomy has 2 metrics (`snapshot`
   carrying both `stars` and `forks`; `commits` carrying one number)
   but `github_features` has one `value` column per `(repo, date,
   metric)` row — there's no schema room for two numbers on one row.
   So each `metric="snapshot"` row explodes into two rows
   (`metric="stars", value=stars` and `metric="forks", value=forks`);
   `metric="commits"` rows keep their row, `commits` renamed to
   `value`. Output is long-format: `repo, date, metric, value`, with
   `metric ∈ {stars, forks, commits}` — three fully independent
   series, since stars/forks/commits growth rates don't meaningfully
   correlate on any short window.
2. **Feature computation**, grouped by `(repo, metric)` — the 2-key
   analog of Google Trends' `groupby("keyword")`. Same math as the
   Trends sibling, same window sizes (7/30 data points) across all
   three metrics rather than metric-specific tuning: min-max
   `value_norm` within that series' own history; `rolling_avg` (7
   data points, `min_periods=1`); `pct_change` (vs. 7 data points
   prior); `zscore` (30-data-point trailing mean/std, `min_periods=5`).

   **Asymmetric history depth, by design, not a bug to fix later:**
   `commits` already has ~106 weeks of real backfilled history, so its
   features are meaningful immediately. `stars`/`forks` only
   accumulate one point per day going forward from whenever `collect()`
   first ran (no historical backfill exists or is possible for these —
   see "Metrics collected" above) — so `value_norm`/`rolling_avg` will
   be present but not very meaningful, and `zscore` will be `NaN`, for
   roughly the first 5-7 real days until enough points exist to fill
   `min_periods`. This mirrors how Google Trends' own `transform.py`
   already documents its "7d/30d means data points, not calendar
   days" ambiguity rather than hiding it — same spirit, applied to a
   sparser warm-up case.

Output columns match `github_features` exactly: `repo, date, metric,
value, value_norm, rolling_avg, pct_change, zscore` (no
`processed_at` — added at the storage layer by `upsert_features`,
same as Google Trends' `transform.py`/`storage.py` split).

## Testing

Following this project's own established convention (a separate test
file per module — `test_collect.py`, `test_storage.py`,
`test_export.py` — rather than Google Trends' single combined
`test_pipeline.py`): `test_clean.py` and `test_transform.py`, plus
extending `test_storage.py` with `upsert_features` tests. All operate
on in-memory records/DataFrames or `:memory:` SQLite — no network
calls, matching every other test in this project.

## `storage.py` addition: `get_raw_records`

One new function: `get_raw_records(conn: sqlite3.Connection) -> list[dict]`.
Reads everything out of `github_raw` and returns it as plain dicts
shaped exactly like `clean.py`'s `RAW_COLUMNS` (`repo, date, metric,
stars, forks, commits, is_partial`) — no `fetched_at`, since nothing
downstream uses it. Deliberately does no `is_partial` coercion at this
layer — it passes through whatever SQLite naturally returns (int
`0`/`1`), relying on `clean.py`'s existing coercion (added during that
stage's final review, specifically to make records read back out of
the database safe to clean) to handle it. This is the integration path
that fix was built for.

## `pipeline.py` — orchestration

Google Trends' `pipeline.py` does `transform(clean(collect()))`
directly — that works there because Trends' `collect()` always
re-pulls its entire 2-year window on every run. GitHub's `collect()`
deliberately does not do that (see `collect.py` — two entry points,
above): it only returns today's incremental slice (~15 records —
snapshot + current week + one newly-finalized week, per repo). Mirroring
the sibling literally would mean `transform()` only ever sees 1-3 data
points per run, producing degenerate rolling/pct-change/z-score
features instead of meaningful ones computed over full history.

So `run_once()` reads the full table back after storing today's slice:

```python
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
        featured = transform(clean(all_records))
        feature_records = featured.to_dict(orient="records")
        upsert_features(conn, feature_records)
        logger.info("Stored %d feature records (from %d total raw records)", len(feature_records), len(all_records))

        export_to_excel(conn)
    finally:
        conn.close()
```

Same early-return-on-empty-`collect()` behavior as the sibling, same
logging style, same `finally: conn.close()`.

**`backfill_commit_history()` is never called from here.** It stays a
strictly separate, manually-run, one-time operation — exactly as
documented in "`collect.py` — two entry points" above and as actually
exercised this session. `run_once()` only ever calls the daily
`collect()`. This was a deliberate choice over auto-triggering backfill
on an empty database: a scheduled daily job unexpectedly taking ~9
minutes and firing ~530 requests the first time it happens to run
against an empty table would be a surprising failure mode under
unattended automation.

## Scheduling

No `scheduler.py`. The Google Trends sibling has one (a `schedule`-
library foreground loop), but its own docstring already recommends
skipping it in favor of a real OS scheduler for a long-running setup —
and that's exactly what happened in practice: this session's actual
Google Trends deployment is a Windows Task Scheduler entry running
`python.exe pipeline.py` directly, not the `schedule`-loop file.
This project follows the mechanism that was actually used, not the one
that was merely documented: once `pipeline.py` is built and tested, a
Task Scheduler entry gets set up the same way (mirroring the "FundForge
Google Trend Pipeline" task's shape — same `python.exe` path, daily
trigger). `GITHUB_TOKEN` is already a persistent User-scope environment
variable, so it should inherit correctly into the scheduled task's
process, but this gets verified with a real triggered run once set up,
same as was done for the Google Trends task. This is a deployment step
that happens after the code exists, not part of the implementation
plan itself.

## Testing

One deviation from the sibling: Google Trends' `test_pipeline.py`
deliberately does not test `pipeline.py`'s orchestration, reasoning
that `collect()` hits the network. This project adds `test_pipeline.py`
that mocks `collect()` directly (patching the whole function, not just
`_get`) to verify the orchestration logic itself — early-return on
empty, correct call sequence, and specifically that the DB read-back
via `get_raw_records()` happens before `transform()` runs on the full
history rather than just the fresh slice. No real network calls
either way.

## Open items for later stages

This document now covers the full pipeline: `collect.py`, `clean.py`,
`transform.py`, `storage.py`, `export_excel.py`, and `pipeline.py`.
Nothing is deferred — the only remaining work is the deployment step
(the Task Scheduler entry) described above, which is operational, not
a design or code gap.
