"""
collect.py — Stage 1: Data Collection (dispatcher)

Loops over each in-scope coin's sources/ adapter, calling collect() on
each. Per-coin isolation: an adapter that raises, or returns no
records, logs a warning and is skipped — a failing coin never blocks
the others. Mirrors ../GitHub/collect.py's per-repo isolation.

Only collect() is dispatched here. backfill() is never called
automatically for any coin — same reasoning as GitHub's
backfill_commit_history(): a scheduled daily job unexpectedly making a
slow historical pull the first time it hits an empty table would be a
surprising failure mode. Each coin's backfill() is run once, by hand,
before daily runs start (see README.md).

Ripple and Solana are not in ADAPTERS — see design.md's "Sources
tracked" for why both are deferred to a follow-up phase.
"""

import logging

from sources import bitcoin, bnb, ethereum

logger = logging.getLogger(__name__)

ADAPTERS = {
    "bitcoin": bitcoin,
    "ethereum": ethereum,
    "bnb": bnb,
}


def collect() -> "list[dict]":
    records = []
    for coin, adapter in ADAPTERS.items():
        try:
            coin_records = adapter.collect()
        except Exception:
            logger.exception("Adapter for %s raised an unexpected error — skipping", coin)
            continue

        if not coin_records:
            logger.warning("No records collected for %s", coin)
            continue

        records.extend(coin_records)

    return records
