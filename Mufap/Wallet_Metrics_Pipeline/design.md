# Blockchain Wallet Metrics Pipeline — Design

Part of Member 11's Alternative Data Pipeline (FundForge). Same 6-stage
shape as the Google Trends and GitHub pipelines in `../Google trends`
and `../GitHub`; this document covers the pieces that differ from that
precedent. Pairs directly with the GitHub pipeline's same 5-coin
blockchain-ecosystem theme (development activity vs. on-chain wallet
activity).

## Sources tracked

Five major blockchains, same set as the GitHub pipeline, used as a
proxy for on-chain economic activity / ecosystem health.

**Phase 1 research spike (completed 2026-08-01) replaced every
assumption below with a verified fact.** The original plan assumed
Etherscan/BscScan's paid-gating was the only open question and that
all three metrics would be available everywhere. Neither held up:
Etherscan's/BscScan's paid gating was confirmed, but a *different*,
genuinely free path (chart CSV export) was found for those two chains
— while Blockchair (the planned fallback) turned out to have no
historical time-series endpoint at all, for any chain. **Net result:
metric coverage is not uniform across coins** — see the per-coin table
below. This is a real, permanent constraint of what's freely available
today, not a placeholder to fill in later.

| Coin | Source | Auth | `active_addresses` | `tx_count` | `tx_volume` | In Phase 2 plan? |
|---|---|---|---|---|---|---|
| Bitcoin | blockchain.com Charts API | none | ✅ | ✅ | ✅ | ✅ yes |
| Ethereum | Etherscan chart CSV export | none | ✅ | ✅ | ❌ not available free | ✅ yes |
| BNB Chain | BscScan chart CSV export | none | ❌ not available free | ✅ | ❌ not available free | ✅ yes |
| Ripple (XRP) | XRPScan metrics API (endpoint confirmed, exact ID not) | none expected | unconfirmed | unconfirmed | unconfirmed | ❌ deferred |
| Solana | none confirmed free | — | ❌ blocked | ❌ blocked | ❌ blocked | ❌ deferred |

**Ripple moved from "in scope" to "deferred" during this pass, alongside
Solana** — see the Ripple write-up below for why: the endpoint shape is
confirmed but the exact metric-ID string that makes it return real data
isn't, and this plan does not write test/implementation code against
guessed API shapes. **Phase 2, as written in `plan.md`, covers 3 coins:
Bitcoin, Ethereum, BNB Chain** — all three fully live-tested this
session, real response shapes captured, ready to build against.

**Bitcoin — blockchain.com Charts API.** Confirmed as originally
planned: `GET https://blockchain.info/charts/{chart-name}?format=json`,
no key, no login. Relevant charts: `n-unique-addresses`
(active_addresses), `n-transactions` (tx_count),
`estimated-transaction-volume` (tx_volume, in BTC). Supports a
`timespan` param (e.g. `2years`, `all`) for backfill depth.

**Ethereum — Etherscan, via chart CSV export, NOT the Stats API.**
Live-verified two things:
1. The documented Stats API (`module=stats&action=dailytx` /
   `dailynewaddress`) is Pro-only — confirmed via
   `docs.etherscan.io/api-reference/endpoint/dailytx.md`, which states
   outright: *"This is a PRO endpoint, available to the Standard Plan
   and above."* Same for `dailynewaddress`. Free tier does not include
   it.
2. Etherscan's public chart pages support an undocumented-but-longstanding
   `?output=csv` query param that returns the full historical daily
   series with no key and no login — confirmed by directly downloading
   both:
   - `https://etherscan.io/chart/tx?output=csv` → daily tx count, back
     to 2015-07-30 (Ethereum genesis). Columns: `Date(UTC),
     UnixTimeStamp, Value`.
   - `https://etherscan.io/chart/active-address?output=csv` → daily
     active addresses (sender+receiver), same date range. Columns:
     `Date(UTC), Unique Address Total Count, Unique Address Receive
     Count, Unique Address Sent Count`.
   This covers `active_addresses` and `tx_count` for free, with more
   history than the original 2-year target. **No `tx_volume` chart
   exists** in Etherscan's chart index (`etherscan.io/charts` was
   enumerated directly — no "ETH transferred" or volume chart is
   listed) — this metric is not available for Ethereum for free, full
   stop. Not attempted via the Stats API either (also Pro-gated).

**BNB Chain — BscScan, same chart-CSV mechanism, narrower coverage.**
BscScan is the same platform family as Etherscan (same UI/API shape).
Confirmed: `https://bscscan.com/chart/tx?output=csv` works identically
(daily tx count, back to 2020-08-29, BSC's effective start). **However
BscScan's chart index (`bscscan.com/charts`, enumerated directly) has
no `active-address` chart at all** — only `/chart/address`, whose
values (starting at 35, 51, ... on BSC's first days) don't match the
"cumulative total addresses" pattern Ethereum's equivalent chart shows
and are not confirmed to mean daily active addresses either. Rather
than guess at an unconfirmed metric's meaning, `active_addresses` is
**out of scope for BNB Chain** until a real source is found. No
`tx_volume` chart exists here either, same as Ethereum. BNB Chain's
adapter therefore only collects `tx_count`.

**Ripple (XRP) — deferred, not included in Phase 2's plan.**
`docs.xrpscan.com` documents `GET
https://api.xrpscan.com/api/v1/metrics/{METRIC_ID}` — no auth,
response described as a historical daily array (`date`, and a `metric`
object with fields including `transaction_count`, `accounts_created`,
`payments_count`, `ledger_count`) going back to 2013. The *base API* is
confirmed live (`api.xrpscan.com/api/v1/account/...` responds
correctly with real JSON), but the exact `METRIC_ID` string was not
found this session — 9 guessed values (`transaction_count`,
`accounts_created`, `tx`, `transactions`, `accounts`,
`activeAccounts`, `txCount`, `daily_metrics`, `ledger_metrics`, plus a
few more) all returned 404. The deprecated Ripple Data API v2
(`data.ripple.com`) was also checked as a backup and returns `403
Missing Authentication Token` — dead end, not usable.
**Decision: rather than write adapter code and tests against a guessed
response shape, Ripple is excluded from `plan.md` entirely.** Whoever
picks up the Ripple adapter next should start by opening
`docs.xrpscan.com/api-documentation/metrics` in an actual browser (not
a scraper — that page likely renders its examples client-side, which
is why fetching the raw doc route only returned navigation chrome both
times it was tried here) to read the real metric ID(s) directly, or
try Bithomp's API (`bithomp.com` — confirmed free, no registration
required) as an alternative. This is a 5-15 minute lookup for whoever
does it with a real browser, not a fundamentally hard problem — it
just isn't something to guess at in a plan document.

**Solana — no free path confirmed; adapter deferred, not
fabricated.** Three options were checked and none work under this
project's "free, and either no key or a trivial free-tier key" bar:
- Solscan's public endpoint (`public-api.solscan.io`) returned
  `{"error_message":"Token is missing"}` live — it requires an API
  token even at its most basic tier, contrary to the original
  assumption.
- Solscan's `api-v2` (used by the solscan.io web app) is behind
  Cloudflare bot-protection and returned a challenge page, not JSON —
  not viable to call directly.
- Solana's own public RPC has no aggregate daily-stats endpoint;
  computing `active_addresses`/`tx_count`/`tx_volume` would mean
  scanning every block for the day (~200,000+ blocks/day at Solana's
  block rate) and aggregating client-side — not feasible on any free
  budget, let alone for a 2-year backfill.
- Third-party historical APIs exist (e.g. Helius) but require account
  signup and an API key, which is a real decision (which provider,
  what free-tier limits) rather than a research question — **deferred
  to whoever picks this up next as an explicit go/no-go choice**, not
  resolved unilaterally here. See `PHASES.md` Phase 1 ledger entry.
- **Consequence for this plan:** the Solana adapter is not included in
  Phase 2's implementation plan below. Combined with Ripple's deferral
  (above), the pipeline ships with 3 of 5 coins initially — Bitcoin,
  Ethereum, BNB Chain; Ripple and Solana are added in follow-up phases
  once their data sources are pinned down for real.

## Metrics collected

Three core metrics, per coin, per day — **coverage varies by coin, see
the table above; this is not uniform**:

- **`active_addresses`** — count of unique addresses active that day.
- **`tx_count`** — number of transactions that day.
- **`tx_volume`** — total value transacted that day, in native coin
  units (not USD — avoids needing a separate price-conversion
  dependency; USD conversion, if ever needed, is a job for the
  downstream prediction engine, not this pipeline). Confirmed available
  for Bitcoin only; not available free for Ethereum or BNB Chain.
  Ripple and Solana are both deferred entirely (see below), so their
  `tx_volume` status is moot for now.

## `collect.py` — two entry points, dispatching to per-coin adapters

Mirrors the GitHub pipeline's `backfill_commit_history()` /
`collect()` split, generalized across 5 heterogeneous data sources via
one adapter module per coin under `sources/`:

```python
# sources/<coin>.py — common interface, one module per coin
def backfill() -> list[dict]:
    """One-time historical fetch, daily granularity, the source's
    entire available history (see per-coin notes, filled in during
    Phase 1)."""

def collect() -> list[dict]:
    """Daily run: yesterday's finalized values (re-checked in case they
    moved) + today's still-in-progress partial snapshot."""
```

**History depth: full history everywhere (decided 2026-08-01).** An
early version of this design had `backfill()` locally filter to
`years=2` for Ethereum/BNB while `collect()` (which re-downloads the
full chart CSV every day, since these sources don't offer an
incremental export) did not — so the 2-year window was already being
silently defeated for those two coins after the first daily run, just
inconsistently with Bitcoin's genuinely 2-year-bounded backfill. Rather
than reconcile by adding a matching filter to Bitcoin and to
Ethereum/BNB's `collect()`, the decision was to go full-history
everywhere: it's more data, `value_norm` (a per-series min-max) is then
computed against the same basis for all 3 coins instead of three
different windows, and it removes a parameter (`years`) that no longer
did anything reliable.

Both return the same flat, long-format record shape, one row per
`(coin, date, metric)`:

```python
{"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses",
 "value": 987654, "is_partial": False}
```

**`is_partial` is always `False` for all 3 in-scope sources (Bitcoin,
Ethereum, BNB Chain) — verified live, not assumed.** All three chart
data sources (blockchain.com, Etherscan, BscScan) were checked on
2026-07-31 and none published a data point for that day yet — the most
recent row in every case was for 2026-07-30, the prior day. These
sources only ever publish a day once it's fully finalized; there is no
"today, still accumulating" row to mark partial the way Google Trends'
`isPartial` or GitHub's current-week commit count needs to. `clean.py`'s
existing "drop `is_partial=True` rows" logic still applies unmodified
(it's just a no-op for this pipeline's data) — kept for schema
consistency with the sibling pipelines, not because this pipeline needs
it. This also shapes `collect()`'s design directly, per-source:
- **Bitcoin** (blockchain.com's `timespan` param supports a short
  window): `collect()` requests the last 10 days, to pick up whichever
  day most recently finished publishing plus catch any late revisions.
- **Ethereum/BNB Chain** (Etherscan/BscScan's CSV export has no
  server-side date filter — it always returns the complete history):
  `collect()` re-downloads the same full CSV `backfill()` uses. This
  is one cheap HTTP request either way (a few hundred KB even with 10+
  years of daily rows), so there's no efficiency reason to do
  otherwise, and the storage layer's upsert absorbs the redundancy for
  free — same principle as GitHub's daily re-check of its current week,
  just simpler here since there's no per-request cost to economize.

`collect.py` itself is a thin dispatcher: it loops over all 5
adapters, calling each one's `collect()`. **Per-coin isolation**: a
failing adapter (network error, unexpected response, rate limit) logs
a warning and is skipped — it does not abort the run for the other
four coins. Directly mirrors the GitHub pipeline's per-repo isolation.

`backfill()` is never called automatically from `pipeline.py` — same
reasoning as GitHub's `backfill_commit_history()`: a scheduled daily
job unexpectedly taking minutes and firing hundreds of requests the
first time it runs against an empty table would be a surprising
failure mode. It's run once, by hand, per coin (so a slow/blocked coin
doesn't hold up backfilling the other four).

## Auth & rate limits

**No API keys are needed for any of the 4 coins included in this
plan** — this is a change from the original design. Etherscan and
BscScan's chart-CSV export requires no key at all (it's the same
mechanism a signed-out browser uses), so `ETHERSCAN_API_KEY` and
`BSCSCAN_API_KEY` are **not needed** and are not part of this plan.
(They'd only become relevant if a future need requires the real Stats
API, which is Pro-only regardless of key.)

- Bitcoin (blockchain.com), Ethereum (Etherscan chart CSV), BNB Chain
  (BscScan chart CSV), Ripple (XRPScan): no auth required.
- Each adapter sends a real browser-like `User-Agent` header on chart
  CSV requests — live testing showed Etherscan/BscScan serve the CSV
  normally either way, but omitting it is more likely to trip
  bot-detection over time (this is the same reasoning as the Cloudflare
  block hit on Solscan's api-v2 above).
- No formal rate limits are published for the chart-CSV mechanism
  (it's a public webpage feature, not a documented API product) — each
  adapter's `backfill()` makes exactly 1-3 requests total (one per
  metric chart), so this isn't a practical concern. `collect()`'s daily
  re-fetch is similarly 1-3 requests.
- XRPScan: no published rate limit found during Phase 1; treated
  conservatively (no more than 1 request/sec) pending real use.

## Error handling

- Per-coin isolation in `collect.py` (see above) — one coin's failure
  never blocks the others.
- Rate-limit/throttling responses for a given coin are logged and that
  coin's fetch stops early rather than continuing to hammer a
  throttled endpoint; other coins are unaffected.

## Storage & export

Same architecture as both sibling pipelines:

- `storage.py` — SQLite source of truth. Two tables, long-format,
  mirroring the GitHub pattern exactly: `wallet_metrics_raw` and
  `wallet_metrics_features`, both keyed on
  `PRIMARY KEY (coin, date, metric)` with `ON CONFLICT ... DO UPDATE`
  upserts, so re-runs never duplicate rows.
- `export_excel.py` — dumps both tables to `.xlsx`, matching the
  siblings' export shape.

## `clean.py` — cleaning

Stays in the raw shape, no reshaping (that's `transform.py`'s job).
`clean(records: list[dict]) -> pd.DataFrame` returns the same columns
as `wallet_metrics_raw` (`coin, date, metric, value, is_partial`),
just fewer rows:

- Drop rows where `is_partial` is `True`.
- Drop duplicate `(coin, date, metric)` triples, keep last.
- **No zero-fill/forward-fill.** A `0` (e.g. zero transactions
  recorded for a low-activity day/coin) is a real data point, not
  evidence of a reporting gap — same reasoning as the GitHub pipeline's
  commit counts.

## `transform.py` — normalization + feature extraction

Grouped by `(coin, metric)` — same 2-key grouping as GitHub's
`(repo, metric)`. Same math as both siblings: min-max `value_norm`
within that series' own history; `rolling_avg` (7 data points,
`min_periods=1`); `pct_change` (vs. 7 data points prior, `inf` treated
as unknown/blank per the GitHub pipeline's Bug #3 lesson); `zscore`
(30-data-point trailing mean/std, `min_periods=5`).

Output columns match `wallet_metrics_features` exactly: `coin, date,
metric, value, value_norm, rolling_avg, pct_change, zscore`.

## Testing (TDD)

Every function is written test-first (red → green → refactor), no
exceptions. Following the GitHub pipeline's convention of one test
file per module:

- `test_collect_bitcoin.py`, `test_collect_ethereum.py`,
  `test_collect_bnb.py` — one per adapter (3, not 5 — Ripple and Solana
  are both deferred, see "Sources tracked" above), all mocking HTTP
  calls (no real network access in tests). `test_collect_ripple.py` and
  `test_collect_solana.py` get added whenever those adapters are built,
  in follow-up phases.
- `test_clean.py`, `test_transform.py` — operate on in-memory
  records/DataFrames.
- `test_storage.py` — `:memory:` SQLite, tests upserts for both
  tables.
- `test_export.py` — tests the Excel export shape.
- `test_pipeline.py` — mocks `collect()` directly to verify
  orchestration logic (early-return on empty, correct call sequence,
  DB read-back happening before `transform()` runs on full history)
  without any real network calls.

## `pipeline.py` — orchestration

Same shape as GitHub's `run_once()`: store today's incremental slice,
read the full table back, run `transform(clean(...))` over the full
history (not just today's slice), upsert features, export to Excel.
Logs record counts at each step. `finally: conn.close()`.

```python
def run_once(db_path: str = "wallet_metrics.db") -> None:
    conn = get_connection(db_path)
    try:
        new_records = collect()
        if not new_records:
            logger.warning("No records collected from any source — check API keys/rate limits, or retry later.")
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

## Scheduling

Same mechanism as both siblings: a Windows Task Scheduler entry
running `python.exe pipeline.py` directly, set up once the code exists
and is verified against real data. No environment variables are needed
for this pipeline (see "Auth & rate limits" — none of the 4 in-scope
coins require a key), which removes one whole category of thing that
could go wrong in the scheduled task's process versus the other two
pipelines.

## Implementation phases

Tracked in `PHASES.md` (status table + ledger). High-level shape:

| Phase | What |
|---|---|
| 0 | Design doc, `CLAUDE.md`, `PHASES.md` scaffold |
| 1 | ✅ Done — API research spike. Findings above: no API keys needed; Bitcoin/Ethereum/BNB/Ripple confirmed buildable free; Solana deferred (no viable free source found) |
| 2 | `collect.py` + adapters, TDD, **3 coins** (Bitcoin, Ethereum, BNB Chain — Ripple and Solana excluded, see above) |
| 3 | `clean.py` (TDD) |
| 4 | `transform.py` (TDD) |
| 5 | `storage.py` (TDD, `:memory:` SQLite) |
| 6 | `export_excel.py` |
| 7 | `pipeline.py` orchestration (mocked-`collect()` tests) |
| 8 | Real live run — backfill + daily, hand-verified against real data (this project's core lesson from the GitHub pipeline's 3 real bugs, all invisible to unit tests) |
| 9 | Task Scheduler deployment + verification |

## Open items for later stages

Two genuinely open items remain, both deliberately deferred rather
than guessed at:

1. **Solana.** No free data source was confirmed during Phase 1 (see
   "Sources tracked" above). Adding Solana is a follow-up phase, gated
   on a human decision about which provider to sign up with (e.g.
   Helius's free tier) — not a code task this plan covers.
2. **Ripple (XRP).** The XRPScan metrics endpoint's shape is
   documented, but the exact `METRIC_ID` string wasn't found through
   scripted fetches this session (its docs page likely renders
   examples client-side). Needs a real-browser look at
   `docs.xrpscan.com/api-documentation/metrics`, or a check of
   Bithomp's API as an alternative, before an adapter can be written —
   this is a follow-up phase, not part of `plan.md`.

Everything else (schema, cleaning rules, feature math, orchestration,
testing strategy, and now the real per-coin metric/auth picture) is
fully specified above, following the two sibling pipelines' already-
proven pattern.
