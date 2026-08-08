# Blockchain Wallet Metrics Pipeline — Member 11 (FundForge)

Tracks on-chain wallet activity (active addresses, transaction count,
transaction volume) for major blockchains, as a proxy for real
economic/ecosystem activity. Pairs with the GitHub pipeline's
developer-activity signal for the same blockchain theme. See
`design.md` for the full design rationale (why coverage isn't uniform
across coins, and why Ripple/Solana are deferred), `CLAUDE.md` for
project conventions, and `PHASES.md` for build status.

**Status:** fully built and deployed. `collect.py` + its 3 coin adapters,
`clean.py`, `transform.py`, `storage.py` (including `upsert_features()`
and `get_raw_records()`), `export_excel.py`, and `pipeline.py` (the
orchestration entry point) are all implemented, tested, and reviewed.
Verified against real live data with no bugs found, and running daily via
Windows Task Scheduler — see `PHASES.md` for the full build ledger.

**Coin coverage (not uniform — see `design.md`):**

| Coin | `active_addresses` | `tx_count` | `tx_volume` |
|---|---|---|---|
| Bitcoin | yes | yes | yes |
| Ethereum | yes | yes | no |
| BNB Chain | no | yes | no |

Ripple and Solana are not implemented yet — no confirmed free data
source (see `design.md`'s "Open items for later stages").

## Setup

```bash
pip install -r requirements.txt
```

No API keys or environment variables are needed — every source this
pipeline uses is free and unauthenticated.

## Running

**Daily run (what the scheduled task calls):**

```bash
python pipeline.py       # collect -> clean -> transform -> store -> export
```

Safe to run repeatedly — storage is upsert-based, never duplicates rows.
Already deployed via Windows Task Scheduler ("FundForge Wallet Metrics
Pipeline", daily at 8am) — see `PHASES.md`'s Phase 9 entry.

**One-time historical backfill (run this first, once, before daily runs
start — fetches each source's entire available history):**

```python
from sources import bitcoin, ethereum, bnb
from storage import get_connection, upsert_raw

conn = get_connection()
all_records = bitcoin.backfill() + ethereum.backfill() + bnb.backfill()
upsert_raw(conn, all_records)
conn.close()
```

## Testing

```bash
pytest -v
```

Runs all tests across every module (`collect.py`/adapters, `clean.py`,
`transform.py`, `storage.py`, `export_excel.py`, `pipeline.py`). No network
calls are made during tests — `requests.get` (or, for the CSV-based
adapters, `fetch_csv`) is mocked throughout.

## Output schema

Every adapter's `backfill()`/`collect()` returns the same shape, one
record per (coin, date, metric):

| Column | Type | Meaning |
|---|---|---|
| `coin` | text | `"bitcoin"`, `"ethereum"`, or `"bnb"` |
| `date` | text (YYYY-MM-DD) | the day this value applies to |
| `metric` | text | `"active_addresses"`, `"tx_count"`, or `"tx_volume"` (not all metrics exist for all coins — see the coverage table above) |
| `value` | number | the raw value for that metric that day |
| `is_partial` | bool | always `False` for this pipeline — see `design.md` |

## Common metadata schema

Every record collected by this pipeline's daily run is also mapped onto
FundForge's team-wide "Common Requirements (For Everyone)" metadata contract
(see `../PROJECT_OVERVIEW.md` section 2b) and stored in the
`wallet_metrics_common` table and Excel sheet, alongside this pipeline's own
native schema. See `common_schema.py` for the exact field mapping. One-time
historical backfills (each source's `backfill()`) write directly to
`wallet_metrics_raw` and are not retroactively mapped to the common schema.
