"""
sources/_scan_csv.py — shared CSV-chart fetch helper for Etherscan-
family block explorers (Etherscan, BscScan — same underlying platform,
same free, unauthenticated `?output=csv` chart-export mechanism).

Not a coin adapter itself — sources/ethereum.py and sources/bnb.py
both import fetch_csv() from here to avoid duplicating this logic.
"""

import csv
import io
import logging

import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (FundForge alt-data pipeline)"}


def fetch_csv(url: str) -> "list[dict] | None":
    """
    GETs `url` (a chart page's ?output=csv export) and parses it into a
    list of dicts keyed by the CSV's header row. Returns None on any
    failure (network error or non-200) after logging why.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException:
        logger.exception("Request failed: %s", url)
        return None

    if resp.status_code != 200:
        logger.warning("Request to %s failed: HTTP %s", url, resp.status_code)
        return None

    return list(csv.DictReader(io.StringIO(resp.text)))
