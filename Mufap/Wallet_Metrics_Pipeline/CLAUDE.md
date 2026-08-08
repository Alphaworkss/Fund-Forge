# Blockchain Wallet Metrics Pipeline

Part of Member 11's FundForge Alternative Data Pipeline project. Sibling to
`../Google trends` and `../GitHub` — see `../PROJECT_OVERVIEW.md` for the
project-wide picture.

## What this is

Tracks on-chain wallet activity (active addresses, transaction count,
transaction volume) for 3 blockchains — Bitcoin, Ethereum, BNB Chain — as a
proxy for real economic/ecosystem activity. Pairs with the GitHub pipeline's
developer-activity signal for the same blockchain-ecosystem theme. Ripple and
Solana were researched and deliberately deferred — no confirmed free data
source for either as of this build (see `design.md`'s "Open items").

Full rationale and every design decision: `design.md`. Phase-by-phase build
status: `PHASES.md`.

## Layout

```
collect.py          # dispatches to sources/, per-coin isolation
sources/
  bitcoin.py         # blockchain.com Charts API (no key)
  ethereum.py        # Etherscan chart-CSV export (no key — see design.md)
  bnb.py              # BscScan chart-CSV export (no key)
  _scan_csv.py         # shared CSV-fetch helper for ethereum.py/bnb.py
clean.py
transform.py
storage.py
export_excel.py
pipeline.py           # run_once() — the pipeline's single entry point
```

## Running it

```bash
python pipeline.py       # daily run: collect -> clean -> transform -> store -> export
```

One-time historical backfill (run by hand, per coin, before daily runs start —
fetches each source's entire available history, see design.md's "History
depth" note):
```python
from sources.bitcoin import backfill
backfill()
```

Safe to run `pipeline.py` repeatedly — storage is upsert-based, never
duplicates rows. Deployed via Windows Task Scheduler as "FundForge Wallet
Metrics Pipeline", daily at 8am — see `PHASES.md`'s Phase 9 entry.

## Required environment variables

None. Every source this pipeline uses (blockchain.com, Etherscan's and
BscScan's chart-CSV exports) is free and unauthenticated — no API keys, no
signup, unlike the GitHub sibling pipeline.

## Conventions (match the sibling pipelines — don't deviate without reason)

- **TDD, no exceptions.** Every function gets a failing test before an
  implementation. One test file per module (`test_collect_bitcoin.py`,
  `test_clean.py`, etc.), all mocking HTTP — no real network calls in tests.
- **Long-format storage**, one row per `(coin, date, metric)`, upserted via
  `ON CONFLICT ... DO UPDATE` — never plain inserts.
- **Per-source isolation.** One coin's API failing must never take down the
  other four. Log a warning and skip.
- **`is_partial` handling.** Today's still-accumulating value is tagged
  `is_partial=True` and dropped in `clean.py` — never treated as final.
- **No zero-fill.** A real `0` (quiet day) is a valid data point, not a gap.
- **The project's core lesson:** passing unit tests is not the same as
  correct behavior. The GitHub pipeline had 3 real bugs that passed every
  unit test and were only caught by running against real data and checking
  numbers by hand (see `../PROJECT_OVERVIEW.md` section 4). Phase 8 of this
  pipeline's plan is a mandatory real-data verification pass — do not skip
  it or treat green tests alone as "done."

## Where to look for more detail

- `design.md` — the "why" behind every decision, including the known API
  research risk (Etherscan/BscScan historical stats possibly gated behind a
  paid tier) and its fallback plan.
- `PHASES.md` — current build status and detailed task ledger.
- `../PROJECT_OVERVIEW.md` — plain-English overview of the whole 3-pipeline
  project, written to be read cold.
