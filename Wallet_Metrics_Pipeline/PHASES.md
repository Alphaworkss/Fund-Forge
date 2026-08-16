# Blockchain Wallet Metrics — Phase Status

Status table first (scan this), detailed ledger below (append to as work
happens). See `design.md` for the full design and `CLAUDE.md` for
conventions.

## Status

| Phase | Status | Notes |
|---|---|---|
| 0. Design doc, CLAUDE.md, PHASES.md scaffold | ✅ Done | design.md, CLAUDE.md, PHASES.md written 2026-08-01 |
| 1. API research spike | ✅ Done | No keys needed. BTC/ETH/BNB buildable free now (uneven metric coverage); Ripple deferred (endpoint shape known, exact metric ID not); Solana blocked — no free source found |
| 2. `collect.py` + adapters (TDD) | ✅ Done | plan.md fully complete (7/7 tasks): 3 coin adapters, dispatcher, storage.py base, export_excel.py, README. 3 coins (Bitcoin, Ethereum, BNB Chain) — Ripple and Solana excluded, see design.md |
| 3. `clean.py` (TDD) | ✅ Done | plan-clean-transform.md Task 1 — implemented, tested, reviewed/approved |
| 4. `transform.py` (TDD) | ✅ Done | plan-clean-transform.md Task 2 — implemented, tested, reviewed/approved (after a redo — see ledger) |
| 5. `storage.py` (TDD) | ✅ Done | Base schema + `upsert_raw` (plan.md Task 5), `upsert_features` (plan-clean-transform.md Task 3), `get_raw_records` (plan-pipeline.md Task 1) — all done, approved |
| 6. `export_excel.py` | ✅ Done | plan.md Task 6 — implemented, tested, reviewed/approved |
| 7. `pipeline.py` orchestration | ✅ Done | plan-pipeline.md Task 2 — implemented, tested (57/57 full suite pristine), reviewed/approved |
| 8. Real live run / hand verification | ✅ Done | plan-pipeline.md Task 3 — ran for real 2026-08-01, no bugs found, all hand-checks matched live sources exactly. See ledger |
| 9. Task Scheduler deployment | ✅ Done | plan-pipeline.md Task 4 — "FundForge Wallet Metrics Pipeline" task registered, daily 8am, manually triggered and confirmed working 2026-08-01 |

Legend: ⬜ Not started · 🔄 In progress · ✅ Done · ⚠️ Blocked

## Ledger

### Phase 0 — Design doc, CLAUDE.md, PHASES.md scaffold (2026-08-01)

- Brainstormed design through `superpowers:brainstorming` skill: scope
  (same 5 coins as GitHub pipeline), metrics (active_addresses, tx_count,
  tx_volume), backfill depth (2 years), API key plan (Etherscan + BscScan
  free keys needed, not yet obtained), phase-state format (this file).
- Wrote `design.md`, `CLAUDE.md`, `PHASES.md`. Folder created at
  `D:\news scrapper\Blockchain wallet metrics\`.
- Flagged open risk: Etherscan/BscScan historical stats endpoints may be
  gated behind a paid tier — deferred to Phase 1 for real verification
  rather than assumed either way.
- Next: Phase 1 research spike, then hand off to `writing-plans` skill for
  a detailed step-by-step implementation plan per phase.

### Phase 1 — API research spike (2026-08-01)

Live-verified against real endpoints (not just docs) — full detail in
`design.md`'s "Sources tracked" section. Summary per coin:

- **Bitcoin**: confirmed as planned. blockchain.com Charts API, no key,
  all 3 metrics (`active_addresses`, `tx_count`, `tx_volume`) available.
- **Ethereum**: original plan (Etherscan Stats API) confirmed
  Pro-only/paid — verified via official docs stating "PRO endpoint,
  available to the Standard Plan and above" for both `dailytx` and
  `dailynewaddress`. Found a working free alternative instead: Etherscan's
  public chart pages support `?output=csv` with no key/login — live-tested
  `etherscan.io/chart/tx?output=csv` and `.../chart/active-address?output=csv`,
  both return full daily history back to 2015. Gives `active_addresses` +
  `tx_count` free. No `tx_volume` chart exists — not available free.
- **BNB Chain**: same chart-CSV mechanism works for `tx_count`
  (`bscscan.com/chart/tx?output=csv`, live-tested, data back to
  2020-08-29). BUT BscScan has no `active-address` chart at all (only an
  unclear `/chart/address`, values don't match Ethereum's cumulative
  pattern) — `active_addresses` out of scope for BNB Chain. No
  `tx_volume` chart either.
- **Ripple (XRP)**: XRPScan's `/api/v1/metrics/{METRIC_ID}` endpoint
  confirmed to exist and be unauthenticated (base API responds correctly
  to other calls), historical daily data per docs back to 2013. Exact
  metric ID string not identified this session — 9 guessed IDs across
  two rounds all 404'd, and the docs page appears to render its examples
  client-side (scripted fetches only returned nav chrome). Backup
  option (deprecated Ripple Data API v2, `data.ripple.com`) also
  checked and confirmed dead (`403 Missing Authentication Token`).
  **Decision: deferred, same as Solana** — not included in `plan.md`.
  Needs a real-browser look at the docs page (or Bithomp's API as an
  alternative) before an adapter can be written for real. No
  `tx_volume` source found either way.
- **Solana**: no free path found. Solscan's public endpoint requires a
  token despite being labeled public (live-tested, got
  `{"error_message":"Token is missing"}`); its api-v2 is behind
  Cloudflare bot-protection; Solana's own RPC has no aggregate
  daily-stats endpoint and scanning ~200k+ blocks/day client-side isn't
  feasible for free. Third-party options (Helius etc.) need a real
  signup decision. **Solana adapter deferred** — not included in Phase 2.
- Applied design.md's original fallback priority where relevant:
  fallback (a) (manual aggregation) ruled infeasible for Ethereum/BNB at
  request-volume scale; fallback (b) (Blockchair) turned out not to have
  *any* historical time-series endpoint for *any* chain (confirmed via
  Blockchair's own API_DOCUMENTATION_EN.md — stats endpoints are
  current-snapshot only), so it wasn't usable regardless of chain
  coverage; fallback (c) (reduced scope) applied for BNB's
  `active_addresses`/`tx_volume`, Ethereum's `tx_volume`, and Solana
  entirely.
- Rewrote `design.md`'s "Sources tracked", "Metrics collected", "Auth &
  rate limits", "Scheduling", and "Open items" sections with these
  confirmed facts, replacing the original speculation.
- Next: Phase 2 implementation plan (`plan.md`), covering 3 coins
  (Bitcoin, Ethereum, BNB Chain).

### Phase 2 — `collect.py` + adapters (in progress, started 2026-08-01)

Executing via `superpowers:subagent-driven-development` (no git repo, so
review packages are built from file snapshots instead of git diffs).

- **plan.md Task 1 (Bitcoin adapter): complete.** Implementer: DONE, 9/9
  tests passing, pristine output. Reviewer: Approved, no Critical/Important
  issues. 3 Minor findings logged (uncaught `json.JSONDecodeError`/`KeyError`
  in `_fetch_chart`, `backfill`/`collect` near-duplicate loops, no test for
  the `RequestException` log branch) — all trace to the plan's own reference
  code, not implementer deviation; deferred to the final whole-branch review
  for triage.
- **plan.md Task 2 (CSV helper + Ethereum adapter): complete.** Implementer:
  DONE, 7/7 tests passing, pristine output. Reviewer: Approved, no
  Critical/Important issues — specifically confirmed `sources/_scan_csv.py`'s
  `fetch_csv()` is genuinely coin-agnostic (no Ethereum-specific assumptions),
  satisfying the forward requirement that Task 3's BNB adapter will reuse it
  unmodified. 4 Minor findings logged (near-duplicate fetch/parse loops in
  `ethereum.py`, no `KeyError` guard if a CSV column gets renamed upstream,
  `365 * years` ignores leap years, hardcoded `HEADERS`/timeout in the shared
  helper) — deferred to final whole-branch review.
- **plan.md Task 3 (BNB Chain adapter): complete.** Implementer: DONE, 5/5
  tests passing, pristine output. Reviewer: Approved, no Critical/Important
  issues — confirmed it reuses `fetch_csv` (no reimplemented fetch logic),
  produces `tx_count` only (no scope creep into `active_addresses`/
  `tx_volume`), `is_partial` always `False`. 3 Minor findings logged
  (byte-identical `_parse_date`/`_parse_tx_rows` duplicated from
  `ethereum.py`, intra-file fetch/log duplication between `backfill()`/
  `collect()`, unused `import csv` in the test file) — all traced to the
  brief's own provided code, not implementer deviation; deferred to final
  whole-branch review.
- **plan.md Task 4 (`collect.py` dispatcher): complete.** Implementer: DONE,
  5/5 tests passing, pristine output. Reviewer: Approved, no
  Critical/Important issues — independently re-ran the tests (confirmed
  clean) and verified the isolation logic directly (try/except around each
  adapter call + separate empty-return check, both `continue` without
  propagating). `ADAPTERS` confirmed to contain exactly `{bitcoin, ethereum,
  bnb}`. 2 Minor findings logged (string-literal return-type annotation
  matching the GitHub sibling's style, no test for "every adapter raises"
  as a distinct case from "every adapter empty") — deferred to final
  whole-branch review. **plan.md's `collect.py`/adapter family (Tasks 1-4)
  is now fully complete.**
- **plan.md Task 5 (`storage.py` base schema + `upsert_raw`): complete.**
  Implementer: DONE, 4/4 tests passing, pristine output. Reviewer: Approved,
  no Critical/Important issues — confirmed genuine `ON CONFLICT ... DO
  UPDATE` upsert (not insert-only), exact schema match, `is_partial`
  int-coercion correct, and scope respected (no premature
  `upsert_features()`/`get_raw_records()`). 2 Minor findings logged
  (per-record loop instead of `executemany`, no `conn.close()` guidance in
  docstring) — deferred to final whole-branch review.
- **plan.md Task 6 (`export_excel.py`): complete.** Implementer: DONE, 1/1
  test passing, pristine output. Reviewer: Approved, no Critical/Important
  issues — confirmed two correctly-named sheets ("raw"/"features"),
  `PermissionError` handling correctly scoped to just the write (read
  queries stay outside the try block, so a real DB/schema bug wouldn't be
  masked as a permission error), full regeneration each call. 3 Minor
  findings logged (success log omits features-row count, prescribed test
  checks row counts not column values, `EXCEL_PATH` is a relative path) —
  deferred to final whole-branch review.
- **plan.md Task 7 (requirements.txt + README.md): complete.** Implementer:
  DONE, `pip install -r requirements.txt` clean. Reviewer: Approved — fact-
  checked every README claim (coin coverage table, test file list, build
  status) directly against the real files on disk, all accurate, no
  overstated claims. **`plan.md` is now 7/7 complete.** Next:
  `plan-clean-transform.md` (3 tasks: clean.py, transform.py,
  upsert_features).

### Phase 3-4 — `clean.py` / `transform.py` (in progress)

- **plan-clean-transform.md Task 1 (`clean.py`): complete.** Implementer:
  DONE, 7/7 tests passing, pristine output. Reviewer: Approved, no
  Critical/Important issues — confirmed correct 3-column `(coin, date,
  metric)` dedup key (not collapsed to 2 columns), real `is_partial` boolean
  filtering, zero-values preserved unchanged, `date` genuinely a
  `pd.Timestamp`. 1 Minor finding logged (dedup runs before the is_partial
  filter — a latent edge case that's a no-op on all current real data since
  no in-scope coin ever emits `is_partial=True`, untested but explicitly
  scoped out) — deferred to final whole-branch review.
- **plan-clean-transform.md Task 2 (`transform.py`): complete, after a
  redo.** First implementer attempt got confused mid-task and produced only
  a bogus "status summary" with no files created — treated as a failed
  dispatch, re-dispatched fresh with a clearer autonomous-execution prompt.
  Retry: DONE, 7/7 tests passing, pristine output. Reviewer (briefed on the
  prior failure, told to verify extra carefully): independently re-ran the
  full suite plus a strict-warnings check on the infinity-handling test —
  confirmed uniform 7/30-point windows with no metric-specific branching,
  `value_norm` correctly isolated per `(coin, metric)` with no
  cross-contamination, `inf`/`-inf` correctly replaced with null for BOTH
  `pct_change` and `zscore` (the safety-critical requirement mirroring the
  GitHub pipeline's Bug #3), and `date` genuinely converted to a string.
  Approved, no Critical/Important issues. 2 Minor findings logged (no
  dedicated zscore-infinity test, 4 separate groupby passes instead of one
  combined pass) — deferred to final whole-branch review.
- **plan-clean-transform.md Task 3 (`upsert_features()` in `storage.py`):
  complete.** Executed via `superpowers:subagent-driven-development` with
  file-snapshot review packages (still no git repo — snapshot diffs via
  `diff -u` in place of `git diff`). Implementer: DONE, 8/8 tests passing
  (4 pre-existing `upsert_raw`/schema + 4 new), pristine output. Reviewer:
  Approved, no Critical/Important issues — confirmed genuine `INSERT ...
  ON CONFLICT DO UPDATE` upsert matching `upsert_raw()`'s conventions
  exactly, no modification to protected functions/schemas, all 4 mandated
  edge cases covered (idempotency, conflict-overwrite, multi-metric
  same coin/date, null pct_change/zscore) against real SQLite (no mocks).
  2 Minor findings logged (no docstring on `upsert_features` — consistent
  with `upsert_raw()` also lacking one, so not a new inconsistency; all 4
  new tests reuse the same coin/date, only varying metric, so the
  composite key's coin/date dimensions aren't separately exercised) —
  deferred to final whole-branch review. **`plan-clean-transform.md` is
  now 3/3 complete.** Next: `plan-pipeline.md` (4 tasks: `get_raw_records`,
  `pipeline.py`, real live run, Task Scheduler deployment).

### Phase 5-9 — `plan-pipeline.md` (in progress)

- **plan-pipeline.md Task 1 (`get_raw_records()` in `storage.py`):
  complete.** Implementer: DONE, 12/12 tests passing (8 pre-existing +
  4 new), pristine output. Reviewer: Approved, zero findings (no
  Critical/Important/Minor) — confirmed full-table read with no `WHERE`
  filter, exact column set (explicit `SELECT` list, no `fetched_at`
  leak), `is_partial` deliberately left uncoerced per brief, and
  `get_connection`/`upsert_raw`/`upsert_features` byte-for-byte
  unchanged. **`storage.py` is now fully complete** (base schema,
  `upsert_raw`, `upsert_features`, `get_raw_records` — Phase 5 done).
- **plan-pipeline.md Task 2 (`pipeline.py` orchestration): complete.**
  Implementer's connection dropped right after confirming all tests
  passed but before it could write its own report — controller
  independently re-ran `test_pipeline.py` (4/4 pass) and the full suite
  (57/57 pass, pristine) against the on-disk files, confirmed both files
  are verbatim matches to the plan's code, and reconstructed the report
  documenting this. Reviewer: Approved, no Critical/Important issues —
  independently verified the orchestration sequence
  (`collect→upsert_raw→get_raw_records→clean→transform→upsert_features→
  export_to_excel`), confirmed the full-history read happens (not just
  transforming the fresh `collect()` slice) and that
  `test_run_once_computes_features_over_full_history_not_just_new_records`
  would genuinely fail under that bug, confirmed the early-return-before-
  any-upsert ordering, `finally: conn.close()`, correct mock targets
  (`pipeline.collect`/`pipeline.export_to_excel`, matching the `from x
  import y` binding), real temp-file SQLite (never `:memory:` or the real
  project DB), and no scope creep (no `scheduler.py` on disk). Also cross-
  checked pipeline.py's calls against every dependency's actual current
  signature, not just the brief's sample code. 1 Minor finding logged
  (`export_to_excel(conn)` called with no explicit `excel_path`, relying
  on the default relative to cwd — worth double-checking once Task 4
  wires up the real Task Scheduler invocation, not a defect in this task)
  — deferred to final whole-branch review. **`plan-pipeline.md`'s code
  tasks (1-2) are now complete** — `pipeline.py` exists and is the
  project's entry point. Remaining: Task 3 (real live run + hand
  verification) and Task 4 (Task Scheduler deployment), both operational.

### Phase 8 — Real live run / hand verification (2026-08-01)

Done directly by the controller (operational task, no subagent dispatch —
involves live network calls and judgment on real results), per
plan-pipeline.md Task 3's checklist.

- **Backfill (Step 1):** ran for real against live sources. Bitcoin 2181
  records, Ethereum 1460, BNB 730 — total 4371, all spanning
  2024-08-01..2026-07-31 (the `years=2` default window, consistent across
  all three adapters). No exceptions, no empty-adapter returns.
- **Found and resolved one discrepancy — documentation, not a code bug:**
  this plan's Step 1 comment predicted "Ethereum ~7,300+ records (2
  metrics x 11+ years of full history)", but the actual reviewed/approved
  `sources/ethereum.py` `backfill()` defaults `years=2` and locally
  filters the full CSV to that window — exactly like `bitcoin.py` and
  `bnb.py`. Verified via direct date-range query
  (`MIN(date)`/`MAX(date)` per coin/metric): all three coins consistently
  span the same 2-year window. The plan's comment was written
  speculatively before `plan.md`'s Task 2 (Ethereum adapter) finalized
  the local-filter design and was never reconciled — the code itself is
  correct and internally consistent; only the plan's illustrative comment
  was wrong. No fix needed.
- **Hand-verification (Step 2):** compared stored values directly against
  live sources, not just docs:
  - Bitcoin `active_addresses` 2026-07-30/07-31 (497475 / 620856) and
    `tx_count` 2026-07-30/07-31 (712078 / 610890) — matched exactly
    against `api.blockchain.info/charts/...` fetched live.
  - Ethereum `tx_count` 2026-07-29..07-31 (1734060 / 1766208 / 1756645) —
    matched exactly against `etherscan.io/chart/tx?output=csv` fetched
    live via `curl`.
  - BNB `tx_count` 2026-07-27..07-31 (15150518 / 14885518 / 15520165 /
    16323969 / 16934247) — matched exactly against
    `bscscan.com/chart/tx?output=csv` fetched live via `curl`.
  - All values matched to the exact integer — no bugs found.
- **Full pipeline run (Step 3):** `python pipeline.py` — no exceptions.
  Logged `Stored 10233 new raw records`, `Stored 12384 feature records
  (from 12384 total raw records)`, `Exported 12384 raw rows to
  wallet_metrics.xlsx`. The 10233→12384 growth is expected: `collect()`
  re-downloads Ethereum/BNB's full CSV history every run (by design, see
  those adapters' docstrings), so its first run pulled years of data
  older than the 2-year backfill window, upserted in as new rows.
- **Idempotency (Step 4):** ran `python pipeline.py` a second time
  immediately after. Raw and feature row counts were identical before and
  after (12384 / 12384 both times) despite `collect()` re-fetching the
  same 10233 records — confirms the upsert path updates in place and
  never duplicates.
- **Excel eyeball (Step 5):** opened `wallet_metrics.xlsx` programmatically
  (`pandas.read_excel`). `raw` sheet: 12384 rows, all 3 coins present.
  `features` sheet: `value_norm` bounded exactly `[0.0, 1.0]`; zero
  `inf`/`-inf` cells in either `pct_change` or `zscore` (the exact class
  of bug that was the GitHub pipeline's Bug #3 — explicitly checked and
  clean here); `zscore` null for exactly the first 4 rows of a spot-
  checked series (bitcoin/tx_count) before the 5-point `min_periods`
  window fills, then populated for the rest — matches the expected
  pattern exactly.
- **Bottom line: no bugs found.** Every hand-check matched live data
  exactly, idempotency held, and the Excel output was clean on the first
  real run — unlike the GitHub pipeline's 3 real bugs, nothing broke here.
  Stating this plainly per the plan's instruction, rather than omitting
  the entry because nothing needed fixing.

### Phase 9 — Task Scheduler deployment (2026-08-01)

Done directly by the controller (operational task). Inspected the two
existing sibling tasks first (`FundForge GitHub Alt-Data Pipeline`,
`FundForge Google Trend Pipeline`) rather than trusting the plan's
simplified example command — both actually run via `cmd.exe /c "<full
python.exe path> pipeline.py >> run.log 2>&1"`, daily at 8am, not a bare
`python.exe` action as the plan's Step 1 snippet showed. Mirrored that
real shape exactly instead:

- **Task created:** `FundForge Wallet Metrics Pipeline`, action =
  `cmd.exe /c ""C:\Users\Chaudhry Fezan\AppData\Local\Programs\Python\Python312\python.exe" pipeline.py >> run.log 2>&1"`,
  working directory `D:\news scrapper\Blockchain wallet metrics`, daily
  trigger at 8:00 AM — matching both sibling tasks' pattern (including
  the `run.log` convention CLAUDE.md flagged as "worth doing
  consistently").
- **Verified created:** `Get-ScheduledTask` showed `State: Ready`.
- **Manually triggered:** `Start-ScheduledTask`. `LastTaskResult` was
  `267009` (SCHED_S_TASK_RUNNING) immediately after, then `0` (success)
  ~10s later — no Task Scheduler stuck-in-"Queued" issue like the one
  documented in the GitHub pipeline's history. `wallet_metrics.db`'s
  mtime updated to match the run, and `run.log` shows fresh matching log
  lines (`Stored 10233 new raw records`, `Stored 12384 feature records
  (from 12384 total raw records)`, `Exported 12384 raw rows to
  wallet_metrics.xlsx`).
- **This is the final step of `plan-pipeline.md`.** The Blockchain Wallet
  Metrics pipeline is now fully built and running automatically for
  Bitcoin, Ethereum, and BNB Chain — matching the other two pipelines'
  deployment state. All 9 phases in the status table are ✅ Done. Next:
  the final whole-branch review, to triage the running list of Minor
  findings logged throughout this ledger.

### Final whole-branch review (2026-08-01)

Dispatched on the most capable available model (Opus), per
`superpowers:subagent-driven-development`'s guidance for this step. Given
a full-project file-snapshot (no git range exists) plus a compiled ledger
of every Minor finding deferred by every task-level reviewer across this
build, and asked to (1) triage each deferred finding and (2) do a fresh
whole-project pass looking for anything only visible now that every
piece exists together.

**Verdict: Ready to merge, with fixes.** No Critical issues. Architecture,
error isolation, feature math (independently re-verified the inf-handling
against the installed pandas version — confirmed real, not cargo-culted),
and SQL parameterization all held up. 57/57 tests confirmed non-tautological.

**Ledger triage — 23 items, resolved:**
- **FIX NOW (7):** uncaught `JSONDecodeError`/`KeyError` in
  `bitcoin.py::_fetch_chart` (breaks all 3 Bitcoin metrics on one bad
  response, contradicting its own docstring); same class of gap in
  `ethereum.py::_collect_all` (a column rename takes down both metrics
  together); unused `import csv` in `test_collect_bnb.py`; missing test
  distinguishing "adapter raises" from "adapter returns empty" in
  `test_collect.py` (a test name currently misdescribes what it covers);
  `export_excel.py`'s success log omitting the features-row count;
  `EXCEL_PATH`/`DB_PATH` being cwd-relative (merged with a new finding,
  see below); `clean.py`'s dedup-before-partial-filter ordering (one-line
  reorder, closes a silent-data-loss edge case, matches the docstring's
  own stated order).
- **WON'T FIX / ACCEPT AS-IS (16):** near-duplicate loops in
  `bitcoin.py`/`bnb.py`/`ethereum.py` (real cost is 1-2 duplicated lines,
  not worth the indirection); `365 * years` leap-year drift (moot once
  the FIX NOW window decision below is made); hardcoded `HEADERS`/timeout
  in `_scan_csv.py` (2 callers, textbook YAGNI); `upsert_raw`'s
  per-record loop instead of `executemany` (measured: 12,384 rows upsert
  in 237ms on the real run — no problem to solve); `upsert_features`
  lacking a docstring (consistent with `upsert_raw`); the multi-metric
  test coverage gaps on `upsert_features`/`get_raw_records` (the
  composite key is a declared SQLite `PRIMARY KEY`, not hand-rolled
  logic — one dimension proves the mechanism); `transform.py`'s 4
  separate groupby passes (~0.2s over 12,384 rows); the zscore-infinity
  test gap (worked the math — `roll_std==0` forces the numerator to 0
  too, so it's `0/0→NaN`, never `±inf` — the branch is genuinely
  unreachable, confirmed by proof not assumption).
- **Cross-cutting duplication verdict (the ledger's main open
  question):** judged **WON'T FIX** — the parts with real complexity
  (network/retry/CSV-parsing) were already extracted to
  `sources/_scan_csv.py`; what remains duplicated between `bitcoin.py`/
  `ethereum.py`/`bnb.py` is a 1-line date parse and a small dict
  comprehension per adapter, and the adapter count is frozen at 3
  (Solana/Ripple deferred in Phase 1, design.md). Explicit trigger
  recorded for revisiting: extract to `_scan_csv.py` if a 4th
  Etherscan-family chain is ever added — three call sites is where the
  math flips.

**New findings** (not in the original ledger — visible only from a
whole-project/whole-system view):
- **Important — history-depth inconsistency defeats the `years=2`
  design intent:** `ethereum.py`/`bnb.py`'s `backfill()` correctly
  post-filters to 2 years, but their `collect()` returns the full
  unfiltered CSV every day — so the very first daily run reinstates
  everything the backfill excluded. Live DB confirmed: Bitcoin 2yr
  window, BNB ~6yr, Ethereum ~11yr — three different history depths,
  which matters because `value_norm` is a per-series min-max, so it's
  now computed against three incomparable baselines despite being the
  one feature meant for cross-series comparison. **This is a genuine
  design fork requiring a human decision** (apply the 2yr cutoff
  everywhere + one-time cleanup delete, vs. deliberately go full-history
  everywhere and remove the now-misleading `years` parameter) — not
  something to silently pick a side on.
- **Important — Task Scheduler will silently drop runs on battery power,
  with no catch-up:** `Register-ScheduledTask` was called without
  `-Settings`, so PowerShell's defaults applied
  (`DisallowStartIfOnBatteries=True`, `StartWhenAvailable=False`). Phase
  9's manual `Start-ScheduledTask` verification bypasses these
  conditions entirely, so the real 8am trigger path was never actually
  exercised. Bounded impact: Ethereum/BNB self-heal next run (full
  history re-fetch), Bitcoin self-heals within its 10-day window — a
  miss only becomes permanent after 10+ consecutive skipped days. Same
  registration pattern likely affects both sibling pipelines' tasks.
- **Important — `CLAUDE.md` and `README.md` are now materially wrong**
  and actively misleading for the next maintainer: `CLAUDE.md` still
  claims 5 tracked chains, `ripple.py`/`solana.py` in the layout, a
  nonexistent `pipeline.py::backfill()`, and — most costly — a
  "Required environment variables" section demanding
  `ETHERSCAN_API_KEY`/`BSCSCAN_API_KEY`, directly contradicting
  `design.md`'s explicit "not needed" finding from Phase 1. `README.md`
  still describes `clean.py`/`transform.py`/`upsert_features`/
  `pipeline.py` as "not yet built" and its pytest instructions omit 3 of
  the 9 test files (would run 40/57 tests and look complete).
- **Minor — `test_storage.py`'s `is_partial` comment is factually
  inverted:** claims `get_raw_records` "deliberately does NOT coerce"
  `is_partial`, but `storage.py` actually does coerce to `bool`, and
  that coercion is load-bearing (verified: without it, `clean.py`'s
  `~df['is_partial']` does int-bitwise-NOT instead of boolean negation
  and raises `KeyError`). The test's assertion passes either way
  (`True == 1` in Python) so provides no real protection.
- **Minor — a failed Excel export is invisible to the scheduler:** a
  `PermissionError` (file open in Excel) is caught, logged, and
  swallowed; `run_once()` returns normally either way, so a stale
  `.xlsx` produces a green `LastTaskResult` with the failure buried in
  `run.log`.
- **Minor — no test drives an `is_partial=True` record through the full
  `upsert_raw → get_raw_records → clean` path** — the exact seam where
  the bool-coercion dependency and the dedup-ordering fix both live.

**Decision + fixes applied (2026-08-01):** human partner chose
**full history everywhere** for the history-depth fork (deeper data over
a uniform 2-year window; recorded in `design.md`'s new "History depth"
subsection) and approved fixing everything else in one pass.

- **Consolidated fix pass** (one subagent dispatch per
  `superpowers:subagent-driven-development`'s guidance to batch
  review-driven fixes rather than one per finding): `bitcoin.py`'s
  `backfill()` now fetches `timespan="all"` (no `years` param);
  `ethereum.py`/`bnb.py`'s `backfill()` now return unfiltered full
  history, matching what `collect()` already did; per-source error
  isolation added to `bitcoin.py::_fetch_chart` (malformed/missing-JSON
  no longer crashes all 3 metrics) and `ethereum.py::_collect_all`
  (a broken CSV column no longer takes down the other metric too);
  `clean.py`'s dedup/partial-filter order swapped (closes the silent-
  data-loss edge case); `export_excel.py` now logs both raw and feature
  counts and returns a bool so `pipeline.py` can surface (not swallow) a
  failed export; `storage.DB_PATH`/`export_excel.EXCEL_PATH` anchored to
  `Path(__file__).resolve().parent` instead of cwd; unused import and a
  misleadingly-named test fixed; `test_storage.py`'s factually-wrong
  `is_partial`-coercion comment corrected (the coercion is real and
  load-bearing) plus a new cross-module integration test. Full suite
  went from 57 → 65 tests, all passing, pristine. Fix-verification
  reviewer: **Approved, zero findings** — confirmed all 4 groups match
  the brief exactly, no scope creep across any of the 16 touched files.
- **Docs reconciled directly by the controller:** `CLAUDE.md` and
  `README.md` rewritten to reflect the actual finished state — 3 coins
  (not 5), no `ripple.py`/`solana.py` in the layout, no
  `ETHERSCAN_API_KEY`/`BSCSCAN_API_KEY` requirement (that section
  directly contradicted `design.md`'s own Phase 1 finding), `pipeline.py`
  as the real entry point, full test suite (`pytest -v`, not a partial
  file list), and the Task Scheduler deployment noted.
- **Task Scheduler settings fixed directly by the controller:**
  `Set-ScheduledTask` applied `-StartWhenAvailable
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries` to "FundForge
  Wallet Metrics Pipeline" — verified via `Get-ScheduledTask`'s
  `.Settings` (`StartWhenAvailable=True`,
  `DisallowStartIfOnBatteries=False`, `StopIfGoingOnBatteries=False`).
  Only this pipeline's task was touched — the same registration pattern
  likely affects both sibling pipelines' tasks, flagged for awareness
  but out of scope to fix here without being asked.
- **Real re-verification after the fix pass:** re-ran Bitcoin's backfill
  with the new full-history behavior against the real DB — 4648 records
  (up from 2181). Full per-coin/metric date ranges now: Bitcoin
  2009-01-03..2026-07-31, Ethereum 2015-07-30..2026-07-31, BNB
  2020-08-29..2026-07-31 — each starting at its own real data-
  availability date, exactly as intended. Ran `python pipeline.py` twice
  in a row: raw/feature counts identical both times (16,486/16,486) —
  idempotency still holds after the fix. Excel re-checked: `value_norm`
  still bounded exactly `[0.0, 1.0]`, zero `inf`/`-inf` in `pct_change`/
  `zscore`, export log line now correctly reports both raw and feature
  counts, and the logged export path is now a full absolute path
  (`D:\news scrapper\Blockchain wallet metrics\wallet_metrics.xlsx`),
  confirming the `__file__`-anchor fix works as intended.

**This closes out the Blockchain Wallet Metrics pipeline build.** All 9
phases done, final whole-branch review complete, every actioned finding
fixed and re-verified against real data, deployment settings hardened.
