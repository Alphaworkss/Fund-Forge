"""
sources/ethereum.py — Ethereum adapter (Etherscan chart CSV export)

No API key required. Etherscan's documented Stats API
(module=stats&action=dailytx/dailynewaddress) is Pro-only — confirmed
via docs.etherscan.io: "This is a PRO endpoint, available to the
Standard Plan and above." Instead, this uses Etherscan's public chart
pages' free, unauthenticated `?output=csv` export (the same mechanism
a signed-out browser uses) — live-verified 2026-07-31.

Only active_addresses and tx_count are collected. No tx_volume chart
exists on Etherscan (its chart index was enumerated directly — no
"ETH transferred"/volume chart is listed) — see design.md.
"""

import datetime
import logging

from sources._scan_csv import fetch_csv

logger = logging.getLogger(__name__)

TX_URL = "https://etherscan.io/chart/tx?output=csv"
ACTIVE_ADDRESS_URL = "https://etherscan.io/chart/active-address?output=csv"


def _parse_date(raw: str) -> str:
    return datetime.datetime.strptime(raw, "%m/%d/%Y").date().isoformat()


def _parse_tx_rows(rows: "list[dict]") -> "list[dict]":
    return [
        {
            "coin": "ethereum",
            "date": _parse_date(row["Date(UTC)"]),
            "metric": "tx_count",
            "value": int(row["Value"]),
            "is_partial": False,
            "raw_response": row,
        }
        for row in rows
    ]


def _parse_active_address_rows(rows: "list[dict]") -> "list[dict]":
    return [
        {
            "coin": "ethereum",
            "date": _parse_date(row["Date(UTC)"]),
            "metric": "active_addresses",
            "value": int(row["Unique Address Total Count"]),
            "is_partial": False,
            "raw_response": row,
        }
        for row in rows
    ]


def _collect_all() -> "list[dict]":
    records = []

    tx_rows = fetch_csv(TX_URL)
    if tx_rows is None:
        logger.warning("Skipping tx_count for ethereum: CSV fetch failed")
    else:
        try:
            records.extend(_parse_tx_rows(tx_rows))
        except (KeyError, ValueError):
            logger.exception("Skipping tx_count for ethereum: CSV parse failed (column shape may have changed)")

    addr_rows = fetch_csv(ACTIVE_ADDRESS_URL)
    if addr_rows is None:
        logger.warning("Skipping active_addresses for ethereum: CSV fetch failed")
    else:
        try:
            records.extend(_parse_active_address_rows(addr_rows))
        except (KeyError, ValueError):
            logger.exception("Skipping active_addresses for ethereum: CSV parse failed (column shape may have changed)")

    return records


def backfill() -> "list[dict]":
    """
    One-time historical fetch: all available history for both metrics.
    Etherscan's chart CSV always returns the complete history (back to
    2015-07-30, verified live) — there's no server-side "last N years"
    filter, and as of 2026-08-01 this pipeline intentionally keeps all
    of it (see design.md's "History depth" note) rather than locally
    trimming it, so backfill() and collect() are now identical in
    behavior — kept as two functions for interface consistency with the
    other adapters and the sibling pipelines.
    """
    return _collect_all()


def collect() -> "list[dict]":
    """
    Same CSV endpoints as backfill() — Etherscan doesn't offer a
    filtered "just the last N days" export, so this re-downloads the
    full CSV every day. One cheap request per metric either way; the
    storage layer's upsert absorbs the redundancy for free.
    """
    return _collect_all()
