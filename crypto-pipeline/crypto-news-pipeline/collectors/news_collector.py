"""
News collector: pulls crypto news from RSS feeds, with a homepage-scrape
fallback for sources whose feed is unavailable, and full-article text
extraction when the feed only carries a summary.

Every raw record returned has at least:
    title, url, published_at, raw_content, source_name, source_type="news"
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    MAX_ITEMS_PER_SOURCE,
    NEWS_SOURCES,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Full-text extraction: prefer newspaper3k when importable, otherwise use
# trafilatura (newspaper3k is broken on Python 3.13 due to lxml.html.clean).
try:  # pragma: no cover - environment dependent
    from newspaper import Article as _NewspaperArticle

    _HAS_NEWSPAPER = True
except Exception:  # pragma: no cover
    _HAS_NEWSPAPER = False

try:
    import trafilatura as _trafilatura

    _HAS_TRAFILATURA = True
except Exception:  # pragma: no cover
    _HAS_TRAFILATURA = False

# Feed summaries shorter than this trigger a full-article fetch.
MIN_SUMMARY_LENGTH = 400


def fetch_full_article_text(url: str) -> Optional[str]:
    """Extract the full article body from a URL. Returns None on failure."""
    if _HAS_NEWSPAPER:
        try:
            article = _NewspaperArticle(url)
            article.download()
            article.parse()
            if article.text and len(article.text.strip()) > 100:
                return article.text.strip()
        except Exception as exc:
            logger.debug("newspaper3k failed for %s: %s", url, exc)

    if _HAS_TRAFILATURA:
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            text = _trafilatura.extract(resp.text)
            if text and len(text.strip()) > 100:
                return text.strip()
        except Exception as exc:
            logger.debug("trafilatura failed for %s: %s", url, exc)

    return None


def _collect_from_rss(source_name: str, rss_url: str) -> list[dict]:
    """Parse an RSS feed into raw record dicts."""
    records: list[dict] = []
    feed = feedparser.parse(rss_url, request_headers=REQUEST_HEADERS)

    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError(f"RSS feed unusable: {rss_url} ({feed.get('bozo_exception')})")

    for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
        title = (entry.get("title") or "").strip()
        url = (entry.get("link") or "").strip()
        if not title or not url:
            continue

        published_at = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("pubDate")
            or ""
        )

        summary = entry.get("summary", "") or ""
        content_list = entry.get("content") or []
        if content_list:
            summary = max(
                [summary] + [c.get("value", "") for c in content_list],
                key=len,
            )

        raw_content = summary
        # If the feed only gives a short summary, try full-article extraction.
        if len(BeautifulSoup(summary, "html.parser").get_text()) < MIN_SUMMARY_LENGTH:
            full_text = fetch_full_article_text(url)
            if full_text:
                raw_content = full_text

        records.append(
            {
                "title": title,
                "url": url,
                "published_at": published_at,
                "raw_content": raw_content,
                "source_name": source_name,
                "source_type": "news",
            }
        )

    return records


def _collect_from_homepage(source_name: str, source_cfg: dict) -> list[dict]:
    """Fallback: scrape article links from the source homepage."""
    homepage = source_cfg["homepage"]
    selector = source_cfg["fallback_selectors"]["article_link"]

    resp = requests.get(homepage, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    records: list[dict] = []
    seen_urls: set[str] = set()

    for anchor in soup.select(selector):
        if len(records) >= MAX_ITEMS_PER_SOURCE:
            break
        url = anchor.get("href", "").strip()
        title = anchor.get_text(strip=True)
        if not url or not title or len(title) < 15:
            continue
        if url.startswith("/"):
            url = homepage.rstrip("/") + url
        if url in seen_urls:
            continue
        seen_urls.add(url)

        full_text = fetch_full_article_text(url) or title

        records.append(
            {
                "title": title,
                "url": url,
                "published_at": "",  # unknown from listing page; cleaning drops if unrecoverable
                "raw_content": full_text,
                "source_name": source_name,
                "source_type": "news",
            }
        )

    return records


def collect_news_source(source_name: str, source_cfg: dict) -> list[dict]:
    """Collect one news source: RSS first, homepage scrape as fallback."""
    rss_url = source_cfg.get("rss")
    if rss_url:
        try:
            return _collect_from_rss(source_name, rss_url)
        except Exception as exc:
            logger.warning("[%s] RSS failed (%s); falling back to homepage scrape", source_name, exc)
    return _collect_from_homepage(source_name, source_cfg)


def collect_all_news() -> list[dict]:
    """Collect from every configured news source. One broken source never
    crashes the run — it is logged and skipped."""
    all_records: list[dict] = []
    for source_name, source_cfg in NEWS_SOURCES.items():
        try:
            records = collect_news_source(source_name, source_cfg)
            logger.info("[%s] collected %d news items", source_name, len(records))
            all_records.extend(records)
        except Exception as exc:
            logger.error("[%s] news collection failed: %s", source_name, exc)
    return all_records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    items = collect_all_news()
    print(f"Collected {len(items)} news items")
