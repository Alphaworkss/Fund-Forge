# Crypto News & Exchange Pipeline

> **Note:** This folder contains the backend data engine. For full-stack setup instructions (including the Next.js Dashboard), please see the main `README.md` in the root directory.

A fully local, zero-credential data ingestion pipeline that continuously
collects crypto news and exchange announcements, cleans and normalizes them
into one unified schema, extracts features (sentiment, importance score,
affected coins, event category), stores everything in SQLite, exports a CSV
snapshot after every run, and runs automatically on a 30-minute schedule.

The output directly feeds the Next.js Dashboard (and can be used for central prediction engines), so the storage format
is clean and self-describing: one table / one CSV, columns exactly matching
the schema below.

## Folder structure

```
crypto-news-pipeline/
├── requirements.txt
├── README.md
├── config.py                 # source URLs, selectors, coin list, category keyword rules
├── conftest.py               # pytest path setup
├── collectors/
│   ├── news_collector.py     # RSS + homepage-scrape fallback + full-text extraction
│   └── exchange_collector.py # exchange announcement page scrapers
├── processing/
│   ├── cleaning.py           # HTML strip, boilerplate removal, timestamps, dedup
│   ├── normalization.py      # unified schema mapping + validation
│   └── feature_extraction.py # coins, category, sentiment, importance
├── storage/
│   ├── db.py                 # SQLite schema + insert/query functions
│   └── csv_export.py         # full-DB CSV export (runs after every pipeline pass)
├── scheduler/
│   └── run_scheduler.py      # APScheduler job, every 30 minutes
├── pipeline.py               # run_pipeline() orchestrator
├── tests/
│   ├── test_cleaning.py
│   ├── test_normalization.py
│   ├── test_feature_extraction.py
│   └── test_pipeline_integration.py
└── data/
    ├── pipeline.db           # created at runtime
    └── pipeline_output.csv   # created/updated at runtime
```

## Install

```bash
cd crypto-news-pipeline
pip install -r requirements.txt
```

No API keys or paid credentials are required. Full-article text extraction
uses `trafilatura`; if `newspaper3k` is installed (works on Python <= 3.12),
the pipeline automatically prefers it and falls back to `trafilatura`.

## Run one manual pass

```bash
python pipeline.py
```

This collects from all sources, cleans, normalizes, extracts features,
stores new records in `data/pipeline.db`, regenerates
`data/pipeline_output.csv` from the full DB, and logs a run summary
(counts, errors, duration).

## Start continuous scheduled runs

```bash
python scheduler/run_scheduler.py
```

Runs the pipeline immediately, then every 30 minutes
(`SCHEDULE_INTERVAL_MINUTES` in `config.py`). A failed run is logged and
never kills the scheduler process.

## Historical backfill

```bash
python backfill.py                       # all sources, target 24 months back
python backfill.py --months 12           # smaller window
python backfill.py --sources "CoinDesk,Kraken"
python backfill.py --max-per-source 500  # cap per source (0 = unlimited)
python backfill.py --delay 2.0           # slower/politer pacing
python backfill.py --reset               # discard checkpoint, start over
```

Standalone (separate from the 30-minute scheduler). News history is
enumerated from each site's **XML sitemap** (all five verified to exist);
exchange history is collected by **paginating** each announcements listing
as far back as it really goes. Every record flows through the exact same
cleaning → normalization → feature-extraction → SQLite → CSV path as live
records, into the same schema, DB, and CSV.

- **Rate-limited**: fixed delay between requests per source + exponential
  backoff retries (3 attempts). Non-retryable 4xx responses are skipped.
- **Resumable**: progress is checkpointed to `data/backfill_state.json`
  after every sitemap/page and batch; interrupted runs continue where they
  stopped, and URLs already in the DB are never re-fetched.
- **No fabricated data**: a record only exists if the page really served
  it, and `published_at` comes from the sitemap `lastmod` or the page's own
  metadata — records with no genuine date are dropped.
- **Coverage report**: `data/backfill_report.json` (also printed) lists,
  per source, records collected/stored, earliest date reached, and whether
  the target was hit or the source's history ran out sooner.

Expected real-world coverage: the 5 news sources should reach ~24 months
via sitemaps. Kraken/OKX/Bybit pagination reaches months-to-a-year-plus but
usually not 24 months; Binance (bot challenge, HTTP 202) and Coinbase
(HTTP 403 on paginated blog pages) will likely yield ~0 — see the
`# VERIFY` notes in `config.py` (`BACKFILL_EXCHANGE_PAGINATION`).

## Run tests

```bash
pytest tests/
```

The integration test runs the whole pipeline against sample input with no
live network calls.

## Data schema

Every stored record — in both the SQLite table `records` and the CSV —
matches this schema exactly:

| Field              | Type  | Description                                                        |
| ------------------ | ----- | ------------------------------------------------------------------ |
| `id`               | str   | SHA-256 hash of `url+title`; stable/deterministic                  |
| `source_type`      | str   | `"news"` or `"exchange_announcement"`                              |
| `source_name`      | str   | e.g. `"CoinDesk"`, `"Binance"`                                     |
| `title`            | str   | Cleaned headline                                                   |
| `url`              | str   | Canonical article/announcement URL                                 |
| `published_at`     | str   | UTC ISO 8601 publication time                                      |
| `content`          | str   | Cleaned full text (or best available summary)                      |
| `collected_at`     | str   | UTC ISO 8601, when the pipeline pulled it                          |
| `event_category`   | str   | One of the categories below, or `"Other"`                          |
| `affected_coins`   | str   | Comma-separated tickers, e.g. `"BTC,ETH"`                          |
| `sentiment_score`  | float | VADER compound score, `-1.0` to `1.0`                              |
| `importance_score` | float | Rule-based, `0.0` to `1.0`                                         |

**Event categories:** Exchange Listing, Delisting, Token Burn, Fork,
Airdrop, ETF News, Wallet Exploit, Exchange Hack, Protocol Upgrade,
Network Congestion, Maintenance Notice, Exchange Outage, Regulatory
Announcement, Other.

**Importance score rule:** base `0.3`; `+0.3` for Exchange Hack / Wallet
Exploit / Exchange Outage / Regulatory Announcement; `+0.2` for Exchange
Listing / Delisting / ETF News / Fork; `+0.1` for official exchange
announcements; `+0.1` if `|sentiment| > 0.5`; clamped to `[0.0, 1.0]`.

## Source notes

| Source           | Method                        | Notes                                                                 |
| ---------------- | ----------------------------- | --------------------------------------------------------------------- |
| CoinDesk         | RSS (`/arc/outboundfeeds/rss/`) | Feed usually includes full/near-full content.                        |
| Cointelegraph    | RSS (`/rss`)                    | Summaries only; full text fetched per article.                       |
| Decrypt          | RSS (`/feed`)                   | Standard WordPress-style feed.                                       |
| Bitcoin Magazine | RSS (`/feed`)                   | Standard feed; occasional paywalled specials.                        |
| The Block        | RSS (`/rss.xml`)                | Some articles are subscriber-only; summary is stored then.           |
| Binance          | Scraped announcements page      | Heavily JS-rendered at times; selectors in `config.py` may need updates. |
| Coinbase         | Scraped blog                    | No dedicated public announcements RSS; blog is closest equivalent.   |
| Kraken           | Scraped blog                    | Server-rendered; most stable of the exchange scrapes.                |
| OKX              | Scraped help-center announcements | JS-heavy; selectors may need updates.                              |
| Bybit            | Scraped announcements site      | JS-heavy; selectors may need updates.                                |

All scraping selectors live in `config.py` (`EXCHANGE_SOURCES` /
`NEWS_SOURCES.fallback_selectors`) with `# VERIFY:` comments — if a site
changes its HTML, fix them there and nowhere else. One broken source never
crashes a run; it is logged and skipped.
