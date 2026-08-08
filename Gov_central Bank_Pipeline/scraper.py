"""
Member 5 - Government & Central Bank Pipeline (Excel storage version)
------------------------------------------------------------------------
Three modes:
    python scraper.py --mode seed90       -> ONE-TIME real 90-day seed (run this first)
    python scraper.py --mode daily        -> normal daily run (default, use after seeding)
"""

import argparse
import hashlib
import re
import time
from datetime import datetime, timezone, timedelta
from calendar import timegm

import feedparser
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from excel_storage import append_records, load_existing_ids

OUTPUT_FILE = "govt_centralbank.xlsx"
YEARS_OF_HISTORY = 3
REQUEST_DELAY_SECONDS = 1.5  

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

RSS_SOURCES = {
    "FED": {"url": "https://www.federalreserve.gov/feeds/press_all.xml", "country": "US"},
    "ECB": {"url": "https://www.ecb.europa.eu/rss/press.html", "country": "EU"},
    "BOE": {"url": "https://www.bankofengland.co.uk/rss/news", "country": "GB"},
}

EVENT_KEYWORDS = {
    "Interest Rate Decision": ["interest rate", "policy rate", "basis points", "bps", "rate decision"],
    "Monetary Policy Report": ["monetary policy report", "monetary policy statement"],
    "Meeting Minutes": ["minutes of the meeting", "meeting minutes"],
    "Forward Guidance": ["forward guidance", "future path", "outlook for policy"],
    "Inflation Report": ["inflation report", "cpi", "consumer price index"],
    "GDP Report": ["gdp", "gross domestic product"],
    "Employment Report": ["employment", "non-farm payroll", "unemployment"],
    "Reserve Requirement Change": ["reserve requirement", "cash reserve ratio", "crr"],
    "Quantitative Easing/Tightening": ["quantitative easing", "quantitative tightening", "asset purchase"],
    "Currency Intervention": ["currency intervention", "foreign exchange intervention"],
    "Governor Speech": ["governor", "speech", "remarks by"],
}

analyzer = SentimentIntensityAnalyzer()

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = BeautifulSoup(text, "html.parser").get_text()
    return re.sub(r"\s+", " ", text).strip()


def make_id(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode("utf-8")).hexdigest()


def classify_event(text: str) -> str:
    lowered = text.lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return event_type
    return "Press Release"


def score_sentiment(text: str) -> float:
    if not text:
        return 0.0
    return analyzer.polarity_scores(text)["compound"]


def score_importance(event_type: str) -> float:
    weights = {
        "Interest Rate Decision": 1.0,
        "Quantitative Easing/Tightening": 1.0,
        "Currency Intervention": 0.9,
        "Reserve Requirement Change": 0.85,
        "Monetary Policy Report": 0.8,
        "Forward Guidance": 0.75,
        "Inflation Report": 0.7,
        "GDP Report": 0.7,
        "Employment Report": 0.6,
        "Meeting Minutes": 0.6,
        "Governor Speech": 0.4,
        "Press Release": 0.3,
    }
    return weights.get(event_type, 0.3)


def build_record(source, source_type, country, region, title, description,
                  full_text, url, published_time):
    event_type = classify_event(f"{title} {description}")
    now_utc = datetime.now(timezone.utc)
    return {
        "id": make_id(url, title),
        "source": source,
        "source_type": source_type,
        "url": url,
        "title": title,
        "description": description,
        "full_text": full_text,
        "published_time": published_time,
        "fetched_date": now_utc.strftime("%Y-%m-%d"),   
        "fetched_time": now_utc.strftime("%H:%M:%S UTC"),  
        "ingestion_time": now_utc.isoformat(),
        "country": country,
        "region": region,
        "language": "en",
        "sector": "Government/Central Bank",
        "event_type": event_type,
        "importance_score": score_importance(event_type),
        "sentiment_score": score_sentiment(full_text or description),
        "confidence_score": 0.9 if source_type == "RSS" else 0.7,
        "keywords": [],
    }


# DAILY COLLECTION (RSS feed)

def collect_rss_daily(source_name, config):
    records = []

    try:
        resp = requests.get(config["url"], headers=HEADERS, timeout=15)
        status = resp.status_code
        content_type = resp.headers.get("Content-Type", "unknown")
        feed = feedparser.parse(resp.content)
    except requests.RequestException as e:
        print(f"  [FAIL] {source_name}: request error - {e}")
        return records

    print(f"  [{source_name}] HTTP {status}, Content-Type: {content_type}, "
          f"entries found: {len(feed.entries)}")

    if feed.bozo:
        print(f"  [warning] {source_name} feed parse issue: {feed.bozo_exception}")

    if not feed.entries:
        print(f"  [DIAGNOSTIC] {source_name} returned 0 entries. Likely causes: "
              f"(1) URL is an HTML index page, not the actual .xml feed - "
              f"open {config['url']} in your browser and look for the real feed link; "
              f"(2) site is blocking the request entirely - check status code above; "
              f"(3) feed structure changed. This source will need manual URL verification.")

    for entry in feed.entries:
        title = clean_text(entry.get("title", ""))
        description = clean_text(entry.get("summary", ""))
        url = entry.get("link", "")
        published = entry.get("published", "") or entry.get("updated", "")
        records.append(build_record(
            source=source_name, source_type="RSS", country=config["country"],
            region="Global", title=title, description=description,
            full_text=description, url=url, published_time=published,
        ))
    return records


def _published_datetime(entry):
    """Extract a real datetime from a feedparser entry, if available."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc)


def collect_rss_seed(source_name, config, days=90):

    records = []
    try:
        resp = requests.get(config["url"], headers=HEADERS, timeout=15)
        status = resp.status_code
        content_type = resp.headers.get("Content-Type", "unknown")
        feed = feedparser.parse(resp.content)
    except requests.RequestException as e:
        print(f"  [FAIL] {source_name}: request error - {e}")
        return records

    print(f"  [{source_name}] HTTP {status}, Content-Type: {content_type}, "
          f"total entries in feed: {len(feed.entries)}")

    if not feed.entries:
        print(f"  [DIAGNOSTIC] {source_name} returned 0 entries - see earlier "
              f"notes on verifying this feed URL in your browser.")
        return records

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    kept, skipped_no_date, skipped_too_old = 0, 0, 0

    for entry in feed.entries:
        entry_dt = _published_datetime(entry)

        if entry_dt is None:
            skipped_no_date += 1
            published_str = entry.get("published", "") or entry.get("updated", "")
        elif entry_dt < cutoff:
            skipped_too_old += 1
            continue
        else:
            published_str = entry_dt.isoformat()

        title = clean_text(entry.get("title", ""))
        description = clean_text(entry.get("summary", ""))
        url = entry.get("link", "")

        records.append(build_record(
            source=source_name, source_type="RSS-Seed", country=config["country"],
            region="Global", title=title, description=description,
            full_text=description, url=url, published_time=published_str,
        ))
        kept += 1

    print(f"  [{source_name}] kept {kept} entries within last {days} days "
          f"(skipped {skipped_too_old} too old, {skipped_no_date} had no date but were kept anyway)")
    return records


# HISTORICAL COLLECTION (site archives)

def collect_fed_historical(years=YEARS_OF_HISTORY):
    records = []
    current_year = datetime.now().year
    for year in range(current_year - years, current_year + 1):
        archive_url = f"https://www.federalreserve.gov/newsevents/pressreleases/{year}-press.htm"
        try:
            resp = requests.get(archive_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [error] FED {year} archive fetch failed: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("div.row.ng-scope, .item")  
        for item in items:
            link_tag = item.find("a")
            if not link_tag:
                continue
            title = clean_text(link_tag.get_text())
            href = link_tag.get("href", "")
            full_url = href if href.startswith("http") else f"https://www.federalreserve.gov{href}"
            date_tag = item.find("time")
            published = date_tag.get("datetime") if date_tag else f"{year}-01-01"

            records.append(build_record(
                source="FED", source_type="Scraped-Historical", country="US",
                region="Global", title=title, description="", full_text="",
                url=full_url, published_time=published,
            ))
        time.sleep(REQUEST_DELAY_SECONDS)
    return records


def fetch_article_text(url, timeout=20):
    """
    Visits an individual article/press-release page and pulls out the real
    body text - not just the title from the listing page. Generic approach
    since we don't know SBP's exact HTML structure in advance: try common
    content containers first, fall back to joining all <p> tags on the page.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        return "", f"fetch failed: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Strip elements that are never real article content.
    for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
        tag.decompose()

    candidates = soup.select(
        "div.content, div.press-release-content, div.article-content, "
        "article, div.main-content, div#content"
    )

    body_text = ""
    for container in candidates:
        text = clean_text(container.get_text(" "))
        if len(text) > len(body_text):
            body_text = text  # keep the largest matching block found

    if len(body_text) < 100:
        # Fallback: no good container found - join all paragraph text instead.
        paragraphs = soup.find_all("p")
        body_text = clean_text(" ".join(p.get_text(" ") for p in paragraphs))

    return body_text, None


def collect_sbp_scraped(max_retries=3, max_articles=25, fetch_full_text=True):
    records = []
    url = "https://www.sbp.org.pk/press-release"
    resp = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=45)
            resp.raise_for_status()
            break
        except requests.Timeout:
            print(f"  [SBP] attempt {attempt}/{max_retries} timed out (45s)...")
        except requests.RequestException as e:
            print(f"  [error] SBP fetch failed: {e}")
            return records

    if resp is None:
        print(f"  [error] SBP unreachable after {max_retries} attempts.")
        return records

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a")
    print(f"  [SBP] page fetched OK, {len(links)} total <a> tags found on page")

    candidates = []
    sample_shown = 0
    for link in links:
        href = link.get("href", "")
        title = clean_text(link.get_text())

        if sample_shown < 8:
            print(f"    [sample] title={title[:60]!r} href={href[:80]!r}")
            sample_shown += 1

        if not href or href.strip() in ("#", "") or href.lower().startswith("javascript:"):
            continue
        if len(title) < 15: 
            continue

        full_url = href if href.startswith("http") else f"https://www.sbp.org.pk{href}"
        candidates.append((title, full_url))

    print(f"  [SBP] {len(candidates)} of {len(links)} links passed the filter.")

    if fetch_full_text:
        to_fetch = candidates[:max_articles]
        if len(candidates) > max_articles:
            print(f"  [SBP] fetching full text for the first {max_articles} of "
                  f"{len(candidates)} articles (raise max_articles to fetch more).")
        for i, (title, full_url) in enumerate(to_fetch, 1):
            print(f"  [SBP] fetching article {i}/{len(to_fetch)}: {title[:50]!r}...")
            body_text, error = fetch_article_text(full_url)
            if error:
                print(f"    [warning] could not fetch full text: {error}")
            description = body_text[:300] if body_text else ""
            records.append(build_record(
                source="SBP", source_type="Scraped", country="PK",
                region="Pakistan", title=title, description=description,
                full_text=body_text, url=full_url, published_time="",
            ))
            time.sleep(REQUEST_DELAY_SECONDS) 

        for title, full_url in candidates[max_articles:]:
            records.append(build_record(
                source="SBP", source_type="Scraped-TitleOnly", country="PK",
                region="Pakistan", title=title, description="", full_text="",
                url=full_url, published_time="",
            ))
    else:
        for title, full_url in candidates:
            records.append(build_record(
                source="SBP", source_type="Scraped-TitleOnly", country="PK",
                region="Pakistan", title=title, description="", full_text="",
                url=full_url, published_time="",
            ))

    kept = len(records)
    print(f"  [SBP] kept {kept} of {len(links)} links after filtering.")
    if kept == 0:
        print("  [SBP DIAGNOSTIC] 0 records kept even though the page fetched successfully. "
              "Look at the [sample] lines printed above - if real press release titles/links "
              "are visible there, the filter rule (title length, href pattern) needs adjusting "
              "to match what SBP's actual links look like.")
    return records


def collect_ecb_historical(years=YEARS_OF_HISTORY):
    records = []
    url = "https://www.ecb.europa.eu/press/pubbydate/html/index.en.html"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [error] ECB archive fetch failed: {e}")
        return records

    soup = BeautifulSoup(resp.text, "html.parser")
    cutoff_year = datetime.now().year - years

    dt_tags = soup.find_all("dt")
    dd_tags = soup.find_all("dd")
    print(f"  [ECB] page fetched OK, found {len(dt_tags)} <dt> and {len(dd_tags)} <dd> tags")

    pairs = list(zip(dt_tags, dd_tags))
    for i, (dt, dd) in enumerate(pairs[:8]):
        print(f"    [sample] date={clean_text(dt.get_text())[:30]!r} "
              f"title={clean_text(dd.get_text())[:60]!r}")

    kept = 0
    for dt, dd in pairs:
        date_text = clean_text(dt.get_text())
        link_tag = dd.find("a")
        if not link_tag:
            continue
        title = clean_text(link_tag.get_text())
        href = link_tag.get("href", "")
        full_url = href if href.startswith("http") else f"https://www.ecb.europa.eu{href}"

        year_match = re.search(r"(20\d{2})", date_text)
        if year_match and int(year_match.group(1)) < cutoff_year:
            continue 

        records.append(build_record(
            source="ECB", source_type="Scraped-Historical", country="EU",
            region="Global", title=title, description="", full_text="",
            url=full_url, published_time=date_text,
        ))
        kept += 1

    print(f"  [ECB] kept {kept} records from {len(pairs)} dt/dd pairs found.")
    if kept == 0 and not pairs:
        print("  [ECB DIAGNOSTIC] No <dt>/<dd> pairs found - the page structure doesn't "
              "match the expected pattern. Inspect the live page and adjust the selector "
              "in collect_ecb_historical().")
    return records


def collect_boe_historical(years=YEARS_OF_HISTORY):
    records = []
    url = "https://www.bankofengland.co.uk/news"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [error] BoE archive fetch failed: {e}")
        return records

    soup = BeautifulSoup(resp.text, "html.parser")
    links = soup.find_all("a", href=True)
    print(f"  [BOE] page fetched OK, {len(links)} total <a> tags found")

    news_links = [l for l in links if "/news/" in l["href"].lower()]
    print(f"  [BOE] {len(news_links)} links contain '/news/' in href")

    for link in news_links[:8]:
        print(f"    [sample] title={clean_text(link.get_text())[:60]!r} href={link['href'][:80]!r}")

    kept = 0
    for link in news_links:
        title = clean_text(link.get_text())
        href = link["href"]
        if len(title) < 15:  
            continue
        full_url = href if href.startswith("http") else f"https://www.bankofengland.co.uk{href}"

        parent = link.find_parent()
        time_tag = parent.find("time") if parent else None
        published = time_tag.get("datetime") if time_tag else ""

        records.append(build_record(
            source="BOE", source_type="Scraped-Historical", country="GB",
            region="Global", title=title, description="", full_text="",
            url=full_url, published_time=published,
        ))
        kept += 1

    print(f"  [BOE] kept {kept} of {len(news_links)} news links after filtering.")
    if kept == 0 and news_links:
        print("  [BOE DIAGNOSTIC] Links were found but all got filtered out - "
              "check the [sample] lines above and loosen the title-length filter if needed.")
    return records

# MAIN

def run_seed(days=180):
    print(f"Running ONE-TIME SEED (real data, filtered to last {days} days by published date)...")
    print("NOTE: only sources in RSS_SOURCES are covered by date-filtering - other sources are scraped in full and may include older items.")
    existing_ids = load_existing_ids(OUTPUT_FILE)
    all_records = []
    for name, config in RSS_SOURCES.items():
        print(f"Fetching {name}...")
        all_records.extend(collect_rss_seed(name, config, days=days))

    print("Fetching SBP (scraped, no reliable date filter - all currently listed items included)...")
    all_records.extend(collect_sbp_scraped())

    new_records = [r for r in all_records if r["id"] not in existing_ids]
    added = append_records(OUTPUT_FILE, new_records)
    print(f"Seed complete. {added} new record(s) added to {OUTPUT_FILE}.")
    if added == 0 and all_records:
        print("Note: 0 NEW records doesn't mean 0 records were fetched - it means everything "
              "fetched this run already exists in your Excel file from a previous run. "
              "That's expected deduplication behavior, not a failure.")


def run_daily():
    print("Running DAILY collection (RSS + SBP scrape)...")
    existing_ids = load_existing_ids(OUTPUT_FILE)
    all_records = []
    for name, config in RSS_SOURCES.items():
        print(f"  Fetching {name}...")
        all_records.extend(collect_rss_daily(name, config))

    print("  Fetching SBP (scraped)...")
    all_records.extend(collect_sbp_scraped())  

    new_records = [r for r in all_records if r["id"] not in existing_ids]
    added = append_records(OUTPUT_FILE, new_records)
    print(f"Daily run complete. {added} new record(s) added to {OUTPUT_FILE}.")


def run_historical():
    print(f"Running ONE-TIME HISTORICAL backfill (~{YEARS_OF_HISTORY} years)...")
    existing_ids = load_existing_ids(OUTPUT_FILE)
    all_records = []

    all_records.extend(collect_fed_historical())
    all_records.extend(collect_sbp_scraped())
    all_records.extend(collect_ecb_historical())
    all_records.extend(collect_boe_historical())

    new_records = [r for r in all_records if r["id"] not in existing_ids]
    added = append_records(OUTPUT_FILE, new_records)
    print(f"Historical backfill complete. {added} new record(s) added to {OUTPUT_FILE}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daily", "historical", "seed"], default="daily")
    parser.add_argument("--days", type=int, default=180,
                         help="For --mode seed: how many days back to keep (default 180)")
    args = parser.parse_args()

    if args.mode == "historical":
        run_historical()
    elif args.mode == "seed":
        run_seed(days=args.days)
    else:
        run_daily()