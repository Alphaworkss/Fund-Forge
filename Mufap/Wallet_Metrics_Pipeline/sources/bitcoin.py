"""
sources/bitcoin.py — Bitcoin adapter (blockchain.com Charts API)

No API key required. Live-verified 2026-07-31:
  GET https://api.blockchain.info/charts/{chart}?timespan=...&format=json
returns {"status": "ok", ..., "values": [{"x": unix_ts, "y": value}, ...]}.

The API never publishes an in-progress "today" row — the most recent
value is always for the prior, fully-finalized day (verified live by
comparing the latest returned date against the actual current date) —
so every record this module returns has is_partial=False. See
design.md's "collect.py — two entry points" section.
"""

import datetime
import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.blockchain.info/charts"

CHARTS = {
    "active_addresses": "n-unique-addresses",
    "tx_count": "n-transactions",
    "tx_volume": "estimated-transaction-volume",
}


def _fetch_chart(chart: str, timespan: str) -> "list[dict] | None":
    """
    Returns the chart's `values` list ([{"x": unix_ts, "y": value}, ...])
    on success, or None on any failure (network error, non-200, or a
    non-"ok" status in the response body) after logging why — lets
    callers skip a single failed metric without crashing the whole run.
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/{chart}",
            params={"timespan": timespan, "format": "json"},
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Request failed for chart %s", chart)
        return None

    if resp.status_code != 200:
        logger.warning("Chart %s request failed: HTTP %s", chart, resp.status_code)
        return None

    try:
        data = resp.json()
    except ValueError:
        logger.exception("Chart %s returned unparseable JSON", chart)
        return None

    if data.get("status") != "ok":
        logger.warning("Chart %s returned non-ok status: %s", chart, data.get("status"))
        return None

    try:
        return data["values"]
    except KeyError:
        logger.exception("Chart %s response missing 'values' key", chart)
        return None


def _values_to_records(metric: str, values: "list[dict]") -> "list[dict]":
    records = []
    for point in values:
        date = datetime.datetime.fromtimestamp(point["x"], tz=datetime.timezone.utc).date().isoformat()
        records.append(
            {
                "coin": "bitcoin", "date": date, "metric": metric, "value": point["y"],
                "is_partial": False, "raw_response": point,
            }
        )
    return records


def backfill() -> "list[dict]":
    """One-time historical fetch: all 3 metrics, entire available history."""
    records = []
    for metric, chart in CHARTS.items():
        values = _fetch_chart(chart, "all")
        if values is None:
            logger.warning("Skipping metric %s for bitcoin: chart fetch failed", metric)
            continue
        records.extend(_values_to_records(metric, values))
    return records


def collect() -> "list[dict]":
    """
    Daily run: last 10 days for all 3 metrics, to pick up whichever day
    most recently finished publishing plus catch any late revisions.
    """
    records = []
    for metric, chart in CHARTS.items():
        values = _fetch_chart(chart, "10days")
        if values is None:
            logger.warning("Skipping metric %s for bitcoin: chart fetch failed", metric)
            continue
        records.extend(_values_to_records(metric, values))
    return records
