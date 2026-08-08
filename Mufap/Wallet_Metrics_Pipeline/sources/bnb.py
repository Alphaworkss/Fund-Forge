"""
sources/bnb.py — BNB Chain adapter (BscScan chart CSV export)

No API key required — same free chart-CSV mechanism as
sources/ethereum.py (BscScan is the same platform family as
Etherscan). Live-verified 2026-07-31:
https://bscscan.com/chart/tx?output=csv works identically to
Etherscan's, data starting 2020-08-29 (BSC's effective launch).

Only tx_count is collected. BscScan has no active-address chart at
all (unlike Etherscan) and no tx_volume chart either — its chart index
(bscscan.com/charts) was enumerated directly and neither exists. Do
not add those metrics here without a real confirmed source first —
see design.md's "Sources tracked" for what was actually checked.
"""

import datetime
import logging

from sources._scan_csv import fetch_csv

logger = logging.getLogger(__name__)

TX_URL = "https://bscscan.com/chart/tx?output=csv"


def _parse_date(raw: str) -> str:
    return datetime.datetime.strptime(raw, "%m/%d/%Y").date().isoformat()


def _parse_tx_rows(rows: "list[dict]") -> "list[dict]":
    return [
        {
            "coin": "bnb",
            "date": _parse_date(row["Date(UTC)"]),
            "metric": "tx_count",
            "value": int(row["Value"]),
            "is_partial": False,
            "raw_response": row,
        }
        for row in rows
    ]


def backfill() -> "list[dict]":
    """
    One-time historical fetch: all available history for tx_count.
    BscScan's chart CSV always returns the complete history (back to
    2020-08-29) — no server-side "last N years" filter, same as
    Ethereum. As of 2026-08-01 this pipeline intentionally keeps all of
    it rather than locally trimming it (see design.md's "History depth"
    note).
    """
    rows = fetch_csv(TX_URL)
    if rows is None:
        logger.warning("Skipping tx_count for bnb: CSV fetch failed")
        return []
    return _parse_tx_rows(rows)


def collect() -> "list[dict]":
    """Same CSV endpoint as backfill() — re-downloads the full CSV; the storage layer's upsert absorbs the redundancy."""
    rows = fetch_csv(TX_URL)
    if rows is None:
        logger.warning("Skipping tx_count for bnb: CSV fetch failed")
        return []
    return _parse_tx_rows(rows)
