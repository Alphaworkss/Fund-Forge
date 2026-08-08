"""
Historical backfill: collect as much genuinely retrievable history as each
source allows (target: up to 24 months back), feeding every record through
the SAME processing modules as the live pipeline (cleaning -> normalization
-> feature_extraction -> storage/db -> storage/csv_export), so backfilled
rows land in the same schema, same SQLite DB, and same CSV.

Strategy per source type:
  * News (CoinDesk, Cointelegraph, Decrypt, Bitcoin Magazine, The Block):
    enumerate historical article URLs from each site's XML sitemap index
    (all five were verified to expose real article sitemaps), filter by
    <lastmod> date where present, then fetch + extract full article text.
  * Exchanges (Kraken, OKX, Bybit, Binance, Coinbase): paginate the public
    announcements listing as far back as it really goes. Binance/Coinbase
    are bot-protected (see # VERIFY in config.py) and will likely yield 0.
    NO data is fabricated: a record only exists if the page really served it,
    and the published date comes from the page/sitemap, never estimated.

Politeness: fixed delay between requests per source, exponential-backoff
retries, realistic User-Agent (config.REQUEST_HEADERS).

Resumability: progress is checkpointed to data/backfill_state.json after
every completed sitemap / listing page and every stored batch. Re-running
resumes where it left off; articles already in the DB are never re-fetched.

Usage:
    python backfill.py                     # all sources, 24 months
    python backfill.py --months 12
    python backfill.py --sources "CoinDesk,Kraken"
    python backfill.py --max-per-source 500   # cap articles per source
    python backfill.py --reset             # discard checkpoint, start over

Coverage report: data/backfill_report.json (also printed) lists, per source,
records collected/stored, the earliest date actually reached, and whether
the target window was hit or the source's own history ran out first.
"""

import argparse
import json
import logging
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    BACKFILL_ARTICLE_SITEMAP_FILTERS,
    BACKFILL_BACKOFF_BASE_SECONDS,
    BACKFILL_BATCH_SIZE,
    BACKFILL_EXCHANGE_PAGINATION,
    BACKFILL_MAX_PAGES_SAFETY,
    BACKFILL_MAX_RETRIES,
    BACKFILL_NEWS_SITEMAPS,
    BACKFILL_REPORT_PATH,
    BACKFILL_REQUEST_DELAY_SECONDS,
    BACKFILL_STATE_PATH,
    BACKFILL_TARGET_MONTHS,
    EXCHANGE_SOURCES,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
)
from collectors.exchange_collector import _absolute_url, _extract_date  # noqa: E402
from processing.cleaning import clean_records, to_utc_iso  # noqa: E402
from processing.feature_extraction import extract_features_batch  # noqa: E402
from processing.normalization import normalize_records  # noqa: E402
from storage.csv_export import export_to_csv  # noqa: E402
from storage.db import get_engine, records_table, save_batch  # noqa: E402

from sqlalchemy import select  # noqa: E402

logger = logging.getLogger("backfill")

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

try:
    import trafilatura as _trafilatura

    _HAS_TRAFILATURA = True
except Exception:  # pragma: no cover
    _HAS_TRAFILATURA = False


# ---------------------------------------------------------------------------
# Polite HTTP with retries
# ---------------------------------------------------------------------------

class PoliteFetcher:
    """requests wrapper: per-instance delay between requests + exponential
    backoff retries. One instance per source keeps pacing per-source."""

    def __init__(self, delay: float = BACKFILL_REQUEST_DELAY_SECONDS):
        self.delay = delay
        self._session = requests.Session()
        self._session.headers.update(REQUEST_HEADERS)
        self._last_request = 0.0

    def get(self, url: str) -> Optional[requests.Response]:
        """GET with politeness delay and retries. Returns None after all
        retries fail (never raises for HTTP/network errors)."""
        for attempt in range(BACKFILL_MAX_RETRIES):
            wait = self.delay - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                self._last_request = time.monotonic()
                resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    return resp
                # 4xx other than 429 will not improve with retries.
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    logger.warning("GET %s -> %d (not retrying)", url, resp.status_code)
                    return None
                logger.warning(
                    "GET %s -> %d (attempt %d/%d)",
                    url, resp.status_code, attempt + 1, BACKFILL_MAX_RETRIES,
                )
            except requests.RequestException as exc:
                logger.warning(
                    "GET %s failed: %s (attempt %d/%d)",
                    url, exc, attempt + 1, BACKFILL_MAX_RETRIES,
                )
            if attempt < BACKFILL_MAX_RETRIES - 1:
                time.sleep(BACKFILL_BACKOFF_BASE_SECONDS * (2 ** attempt))
        return None


# ---------------------------------------------------------------------------
# Checkpoint state
# ---------------------------------------------------------------------------

def load_state(path: Path = BACKFILL_STATE_PATH) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Checkpoint unreadable (%s); starting fresh", exc)
    return {"sources": {}}


def save_state(state: dict, path: Path = BACKFILL_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(path)  # atomic on POSIX


def _source_state(state: dict, source: str) -> dict:
    return state["sources"].setdefault(
        source,
        {
            "completed_sitemaps": [],
            "last_completed_page": 0,
            "oldest_date_reached": None,
            "done": False,
        },
    )


# ---------------------------------------------------------------------------
# Article fetching (full text + published date from the page itself)
# ---------------------------------------------------------------------------

def fetch_article(fetcher: PoliteFetcher, url: str) -> tuple[Optional[str], Optional[str]]:
    """Fetch a URL and return (full_text, published_date_iso_or_none).
    The date comes from trafilatura's metadata extraction (meta tags /
    JSON-LD on the page) — never invented."""
    resp = fetcher.get(url)
    if resp is None or not _HAS_TRAFILATURA:
        return None, None
    try:
        raw = _trafilatura.extract(
            resp.text, output_format="json", with_metadata=True, url=url
        )
        if not raw:
            return None, None
        data = json.loads(raw)
        text = (data.get("text") or "").strip()
        date = (data.get("date") or "").strip() or None
        return (text if len(text) > 100 else None), date
    except Exception as exc:
        logger.debug("extraction failed for %s: %s", url, exc)
        return None, None


# ---------------------------------------------------------------------------
# Batch processing through the EXISTING pipeline modules
# ---------------------------------------------------------------------------

class BatchProcessor:
    """Accumulates raw records and flushes them through cleaning ->
    normalization -> feature extraction -> DB, exactly like pipeline.py."""

    def __init__(self, engine, batch_size: int = BACKFILL_BATCH_SIZE):
        self.engine = engine
        self.batch_size = batch_size
        self._buffer: list[dict] = []
        self.collected = 0
        self.stored = 0

    def add(self, record: dict) -> None:
        self._buffer.append(record)
        self.collected += 1
        if len(self._buffer) >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        cleaned = clean_records(self._buffer)
        normalized = normalize_records(cleaned)
        enriched = extract_features_batch(normalized)
        self.stored += save_batch(self.engine, enriched)
        self._buffer = []


def load_existing_urls(engine) -> set[str]:
    """URLs already in the DB — skipped without any network fetch."""
    with engine.connect() as conn:
        rows = conn.execute(select(records_table.c.url)).all()
    return {row[0] for row in rows}


# ---------------------------------------------------------------------------
# News backfill via sitemaps
# ---------------------------------------------------------------------------

def parse_sitemap_xml(xml_text: str) -> tuple[list[dict], list[dict]]:
    """Parse sitemap XML. Returns (child_sitemaps, url_entries); each entry
    is {"loc": ..., "lastmod": ...(or None)}. Handles both <sitemapindex>
    and <urlset> documents."""
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except ET.ParseError:
        return [], []

    def entries(tag: str) -> list[dict]:
        out = []
        for node in root.findall(f"sm:{tag}", _SITEMAP_NS):
            loc = node.find("sm:loc", _SITEMAP_NS)
            lastmod = node.find("sm:lastmod", _SITEMAP_NS)
            if loc is not None and (loc.text or "").strip():
                out.append({
                    "loc": loc.text.strip(),
                    "lastmod": (lastmod.text or "").strip() if lastmod is not None else None,
                })
        return out

    return entries("sitemap"), entries("url")


def _lastmod_dt(entry: dict) -> Optional[datetime]:
    iso = to_utc_iso(entry.get("lastmod") or "")
    return datetime.fromisoformat(iso) if iso else None


def backfill_news_source(
    source_name: str,
    sitemap_index_url: str,
    cutoff: datetime,
    engine,
    state: dict,
    existing_urls: set[str],
    max_records: int = 0,
    delay: float = BACKFILL_REQUEST_DELAY_SECONDS,
) -> dict:
    """Backfill one news source from its sitemap. Returns a report dict."""
    fetcher = PoliteFetcher(delay)
    processor = BatchProcessor(engine)
    src_state = _source_state(state, source_name)
    filters = BACKFILL_ARTICLE_SITEMAP_FILTERS.get(source_name, [])
    notes: list[str] = []
    oldest: Optional[str] = src_state.get("oldest_date_reached")
    history_exhausted = False

    resp = fetcher.get(sitemap_index_url)
    if resp is None:
        notes.append("sitemap index unreachable")
        return _make_report(source_name, processor, oldest, cutoff, notes, False)

    child_sitemaps, direct_urls = parse_sitemap_xml(resp.text)

    # Some sites might serve a urlset directly; treat it as one "sitemap".
    sitemap_queue: list[dict]
    if child_sitemaps:
        sitemap_queue = [
            s for s in child_sitemaps
            if not filters or any(f in s["loc"] for f in filters)
        ]
        # Newest-first so a capped/interrupted run still prioritizes
        # recent history. Entries without lastmod sort last (unknown age).
        sitemap_queue.sort(
            key=lambda s: _lastmod_dt(s) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    else:
        sitemap_queue = [{"loc": sitemap_index_url, "lastmod": None, "_urls": direct_urls}]

    stop = False
    for child in sitemap_queue:
        if stop:
            break
        loc = child["loc"]
        if loc in src_state["completed_sitemaps"]:
            continue

        # Skip whole child sitemaps that are entirely older than the cutoff
        # (only safe when the index carries a lastmod for them).
        child_dt = _lastmod_dt(child)
        if child_dt and child_dt < cutoff:
            history_exhausted = False  # older history EXISTS; we chose to stop
            src_state["completed_sitemaps"].append(loc)
            stop = True
            notes.append(f"stopped at {loc} (older than cutoff)")
            continue

        if "_urls" in child:
            url_entries = child["_urls"]
        else:
            child_resp = fetcher.get(loc)
            if child_resp is None:
                notes.append(f"child sitemap unreachable: {loc}")
                continue
            _, url_entries = parse_sitemap_xml(child_resp.text)

        for entry in url_entries:
            if max_records and processor.collected >= max_records:
                stop = True
                notes.append("per-source cap reached")
                break
            url = entry["loc"]
            if url in existing_urls:
                continue
            entry_dt = _lastmod_dt(entry)
            if entry_dt and entry_dt < cutoff:
                continue  # older than target window

            text, page_date = fetch_article(fetcher, url)
            if text is None:
                continue
            published = entry.get("lastmod") or page_date or ""
            if not published:
                continue  # no genuine date -> unusable for training, drop

            # Prefer the real headline (first line of extracted text);
            # fall back to a slug-derived title.
            title = (
                _extract_title_from_text(text)
                or url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").strip()
            )
            processor.add({
                "title": title,
                "url": url,
                "published_at": published,
                "raw_content": text,
                "source_name": source_name,
                "source_type": "news",
            })
            existing_urls.add(url)
            iso = to_utc_iso(published)
            if iso and (oldest is None or iso < oldest):
                oldest = iso

            if processor.collected % BACKFILL_BATCH_SIZE == 0:
                src_state["oldest_date_reached"] = oldest
                save_state(state)

        if not stop:
            src_state["completed_sitemaps"].append(loc)
        src_state["oldest_date_reached"] = oldest
        save_state(state)

    # Ran through every article sitemap without an early stop (cap or
    # cutoff): the site's own sitemap history ran out first.
    if not stop:
        history_exhausted = True

    processor.flush()
    src_state["oldest_date_reached"] = oldest
    src_state["done"] = True
    save_state(state)
    return _make_report(source_name, processor, oldest, cutoff, notes, history_exhausted)


def _extract_title_from_text(text: str) -> Optional[str]:
    """First line of extracted text is usually the headline; use it only
    when it looks like one."""
    first = text.strip().splitlines()[0].strip()
    if 15 <= len(first) <= 200:
        return first
    return None


# ---------------------------------------------------------------------------
# Exchange backfill via listing pagination
# ---------------------------------------------------------------------------

def backfill_exchange_source(
    exchange_name: str,
    pagination_cfg: dict,
    cutoff: datetime,
    engine,
    state: dict,
    existing_urls: set[str],
    max_records: int = 0,
    delay: float = BACKFILL_REQUEST_DELAY_SECONDS,
) -> dict:
    """Paginate one exchange's announcements listing as far back as it
    genuinely allows. Stops on: empty page, page with no NEW links,
    cutoff reached, safety page cap, or per-source record cap."""
    fetcher = PoliteFetcher(delay)
    processor = BatchProcessor(engine)
    src_state = _source_state(state, exchange_name)
    source_cfg = EXCHANGE_SOURCES[exchange_name]
    selectors = source_cfg["selectors"]
    base_url = source_cfg["base_url"]
    notes: list[str] = []
    oldest: Optional[str] = src_state.get("oldest_date_reached")
    history_exhausted = False

    page = max(1, src_state.get("last_completed_page", 0) + 1)
    prev_page_links: set[str] = set()
    while page <= BACKFILL_MAX_PAGES_SAFETY:
        if page == 1:
            page_url = pagination_cfg.get("first_page_url") or pagination_cfg["page_url"].format(n=1)
        else:
            page_url = pagination_cfg["page_url"].format(n=page)

        resp = fetcher.get(page_url)
        if resp is None or not resp.text.strip():
            history_exhausted = True
            notes.append(f"pagination ended at page {page} (unreachable/empty)")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        page_links: list[tuple[str, str, str]] = []  # (title, url, listing_date)
        seen_on_page: set[str] = set()
        for item in soup.select(selectors["item"]):
            title = item.get_text(strip=True)
            href = (item.get(selectors.get("link_attr", "href"), "") or "").strip()
            if not title or not href or len(title) < 10:
                continue
            link = _absolute_url(href, base_url)
            if link in seen_on_page:
                continue
            seen_on_page.add(link)
            page_links.append((title, link, _extract_date(item, selectors.get("date"))))

        if not page_links:
            history_exhausted = True
            notes.append(f"pagination ended at page {page} (no items parsed)")
            break

        # Many sites silently serve the LAST real page for any page number
        # past their history. Detect that as "same links as previous page"
        # — NOT as "links already in the DB", because the live pipeline
        # legitimately pre-collected recent pages.
        current_links = {u for (_, u, _) in page_links}
        if current_links == prev_page_links:
            history_exhausted = True
            notes.append(f"pagination ended at page {page} (repeating previous page)")
            break
        prev_page_links = current_links

        new_links = [(t, u, d) for (t, u, d) in page_links if u not in existing_urls]

        page_cutoff_hit = False
        for title, link, listing_date in new_links:
            if max_records and processor.collected >= max_records:
                notes.append("per-source cap reached")
                page_cutoff_hit = True
                break

            # Fetch the announcement page itself for full text + real date.
            text, page_date = fetch_article(fetcher, link)
            published = listing_date or page_date or ""
            if not published:
                # No genuine date anywhere -> drop rather than fabricate.
                continue
            iso = to_utc_iso(published)
            if iso:
                if oldest is None or iso < oldest:
                    oldest = iso
                if datetime.fromisoformat(iso) < cutoff:
                    page_cutoff_hit = True
                    notes.append(f"cutoff reached on page {page}")
                    # Still keep this record: it has a real date, it is just
                    # the boundary. Records beyond it will not be fetched.
            processor.add({
                "title": title,
                "url": link,
                "published_at": published,
                "raw_content": text or title,
                "source_name": exchange_name,
                "source_type": "exchange_announcement",
            })
            existing_urls.add(link)

        src_state["last_completed_page"] = page
        src_state["oldest_date_reached"] = oldest
        save_state(state)

        if page_cutoff_hit:
            break
        page += 1
    else:
        notes.append(f"safety page cap ({BACKFILL_MAX_PAGES_SAFETY}) reached")

    processor.flush()
    src_state["oldest_date_reached"] = oldest
    src_state["done"] = True
    save_state(state)
    return _make_report(exchange_name, processor, oldest, cutoff, notes, history_exhausted)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _make_report(
    source_name: str,
    processor: BatchProcessor,
    oldest: Optional[str],
    cutoff: datetime,
    notes: list[str],
    history_exhausted: bool,
) -> dict:
    target_reached = False
    if oldest:
        # Consider the target hit if we got within 31 days of the cutoff.
        target_reached = datetime.fromisoformat(oldest) <= cutoff + timedelta(days=31)
    return {
        "source": source_name,
        "records_collected": processor.collected,
        "records_stored_new": processor.stored,
        "earliest_date_reached": oldest,
        "target_cutoff": cutoff.isoformat(),
        "target_reached": target_reached,
        "history_exhausted_before_target": history_exhausted and not target_reached,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_backfill(
    months: int = BACKFILL_TARGET_MONTHS,
    sources: Optional[list[str]] = None,
    max_per_source: int = 0,
    delay: float = BACKFILL_REQUEST_DELAY_SECONDS,
    reset: bool = False,
) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    logger.info("Backfill cutoff: %s (%d months)", cutoff.date(), months)

    if reset and BACKFILL_STATE_PATH.exists():
        BACKFILL_STATE_PATH.unlink()
        logger.info("Checkpoint reset")

    state = load_state()
    engine = get_engine()
    existing_urls = load_existing_urls(engine)
    logger.info("%d URLs already in DB (will be skipped)", len(existing_urls))

    reports: list[dict] = []

    for name, sitemap_url in BACKFILL_NEWS_SITEMAPS.items():
        if sources and name not in sources:
            continue
        if state["sources"].get(name, {}).get("done") and not reset:
            logger.info("[%s] already completed in checkpoint; skipping "
                        "(use --reset to redo)", name)
            continue
        logger.info("=== News backfill: %s ===", name)
        try:
            reports.append(backfill_news_source(
                name, sitemap_url, cutoff, engine, state, existing_urls,
                max_records=max_per_source, delay=delay,
            ))
        except Exception as exc:
            logger.error("[%s] backfill failed: %s", name, exc)
            reports.append({"source": name, "error": str(exc)})

    for name, pagination_cfg in BACKFILL_EXCHANGE_PAGINATION.items():
        if sources and name not in sources:
            continue
        if state["sources"].get(name, {}).get("done") and not reset:
            logger.info("[%s] already completed in checkpoint; skipping", name)
            continue
        logger.info("=== Exchange backfill: %s ===", name)
        try:
            reports.append(backfill_exchange_source(
                name, pagination_cfg, cutoff, engine, state, existing_urls,
                max_records=max_per_source, delay=delay,
            ))
        except Exception as exc:
            logger.error("[%s] backfill failed: %s", name, exc)
            reports.append({"source": name, "error": str(exc)})

    # Final CSV export of the full DB, same as the live pipeline.
    export_to_csv(engine)

    BACKFILL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKFILL_REPORT_PATH.write_text(json.dumps(reports, indent=2))
    logger.info("Coverage report written to %s", BACKFILL_REPORT_PATH)
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical backfill for the crypto news pipeline")
    parser.add_argument("--months", type=int, default=BACKFILL_TARGET_MONTHS,
                        help="How many months back to target (default: 24)")
    parser.add_argument("--sources", type=str, default="",
                        help="Comma-separated source names to limit to")
    parser.add_argument("--max-per-source", type=int, default=0,
                        help="Cap on records collected per source (0 = unlimited)")
    parser.add_argument("--delay", type=float, default=BACKFILL_REQUEST_DELAY_SECONDS,
                        help="Seconds between requests per source (default: 1.5)")
    parser.add_argument("--reset", action="store_true",
                        help="Discard the checkpoint and start from scratch")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    sources = [s.strip() for s in args.sources.split(",") if s.strip()] or None
    reports = run_backfill(
        months=args.months,
        sources=sources,
        max_per_source=args.max_per_source,
        delay=args.delay,
        reset=args.reset,
    )

    print("\n===== BACKFILL COVERAGE REPORT =====")
    for r in reports:
        if "error" in r:
            print(f"  {r['source']}: FAILED ({r['error']})")
            continue
        status = ("TARGET REACHED" if r["target_reached"]
                  else "history exhausted before target"
                  if r["history_exhausted_before_target"]
                  else "stopped before target")
        print(f"  {r['source']}: {r['records_collected']} collected, "
              f"{r['records_stored_new']} new, "
              f"earliest={r['earliest_date_reached'] or 'n/a'} [{status}]")


if __name__ == "__main__":
    main()
