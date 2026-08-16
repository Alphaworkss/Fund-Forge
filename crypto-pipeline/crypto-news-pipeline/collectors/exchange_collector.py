"""
Exchange announcement collector: scrapes public announcement/news pages
for the 5 configured exchanges. All CSS selectors live in config.py
(EXCHANGE_SOURCES) so they can be fixed centrally when a site's HTML
changes.

Every raw record returned has at least:
    title, url, published_at, raw_content, source_name,
    source_type="exchange_announcement"
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    EXCHANGE_SOURCES,
    MAX_ITEMS_PER_SOURCE,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _absolute_url(href: str, base_url: str) -> str:
    """Turn a relative href into an absolute URL."""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return base_url.rstrip("/") + "/" + href


def _extract_date(item, date_selector) -> str:
    """Best-effort date extraction from an item element."""
    if not date_selector:
        return ""
    node = item.select_one(date_selector) if hasattr(item, "select_one") else None
    if node is None:
        return ""
    return (node.get("datetime") or node.get_text(strip=True) or "").strip()


def collect_exchange_source(exchange_name: str, source_cfg: dict) -> list[dict]:
    """Scrape one exchange's announcements listing page into raw records."""
    url = source_cfg["url"]
    selectors = source_cfg["selectors"]
    base_url = source_cfg["base_url"]

    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    records: list[dict] = []
    seen_urls: set[str] = set()

    for item in soup.select(selectors["item"]):
        if len(records) >= MAX_ITEMS_PER_SOURCE:
            break

        # The item selector targets anchors directly; title selector (if any)
        # points at a child node, otherwise the anchor text is the title.
        title_selector = selectors.get("title")
        if title_selector:
            title_node = item.select_one(title_selector)
            title = title_node.get_text(strip=True) if title_node else ""
        else:
            title = item.get_text(strip=True)

        href = item.get(selectors.get("link_attr", "href"), "") or ""
        href = href.strip()

        if not title or not href or len(title) < 10:
            continue

        link = _absolute_url(href, base_url)
        if link in seen_urls:
            continue
        seen_urls.add(link)

        published_at = _extract_date(item, selectors.get("date"))
        if not published_at:
            # Announcement listing pages often expose no date; they list
            # CURRENT items, so collection time is the honest best estimate.
            # Without this, every date-less announcement would be dropped in
            # cleaning (missing timestamp), losing all official sources.
            published_at = datetime.now(timezone.utc).isoformat()

        records.append(
            {
                "title": title,
                "url": link,
                "published_at": published_at,
                # Announcement listing pages rarely expose full body text;
                # the title is the best available summary at collect time.
                "raw_content": title,
                "source_name": exchange_name,
                "source_type": "exchange_announcement",
            }
        )

    return records


def collect_all_exchanges() -> list[dict]:
    """Collect from every configured exchange. One broken source never
    crashes the run — it is logged and skipped."""
    all_records: list[dict] = []
    for exchange_name, source_cfg in EXCHANGE_SOURCES.items():
        try:
            records = collect_exchange_source(exchange_name, source_cfg)
            logger.info("[%s] collected %d announcements", exchange_name, len(records))
            all_records.extend(records)
        except Exception as exc:
            logger.error("[%s] exchange collection failed: %s", exchange_name, exc)
    return all_records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    items = collect_all_exchanges()
    print(f"Collected {len(items)} exchange announcements")
