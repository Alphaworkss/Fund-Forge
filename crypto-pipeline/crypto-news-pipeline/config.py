"""
Central configuration for the Crypto News & Exchange Pipeline.

Everything that is likely to change over time (URLs, CSS selectors,
keyword lists) lives here so it can be fixed in one place.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "pipeline.db"
CSV_PATH = DATA_DIR / "pipeline_output.csv"

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 15  # seconds

# Max articles to pull per source per run (keeps runs fast and polite).
MAX_ITEMS_PER_SOURCE = 25

# ---------------------------------------------------------------------------
# News sources (RSS where available, homepage scrape fallback)
# ---------------------------------------------------------------------------

NEWS_SOURCES = {
    "CoinDesk": {
        "rss": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "homepage": "https://www.coindesk.com/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "fallback_selectors": {
            "article_link": "a[href*='/markets/'], a[href*='/business/'], a[href*='/policy/']",
        },
    },
    "Cointelegraph": {
        "rss": "https://cointelegraph.com/rss",
        "homepage": "https://cointelegraph.com/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "fallback_selectors": {
            "article_link": "a[href^='/news/']",
        },
    },
    "Decrypt": {
        "rss": "https://decrypt.co/feed",
        "homepage": "https://decrypt.co/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "fallback_selectors": {
            "article_link": "a[href*='decrypt.co/'][href*='/']",
        },
    },
    "Bitcoin Magazine": {
        "rss": "https://bitcoinmagazine.com/feed",
        "homepage": "https://bitcoinmagazine.com/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "fallback_selectors": {
            "article_link": "a[href*='/articles/'], a[href*='/markets/'], a[href*='/business/']",
        },
    },
    "The Block": {
        "rss": "https://www.theblock.co/rss.xml",
        "homepage": "https://www.theblock.co/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "fallback_selectors": {
            "article_link": "a[href*='/post/']",
        },
    },
}

# ---------------------------------------------------------------------------
# Exchange announcement sources (scraped)
#
# Each entry defines the announcements listing page plus CSS selectors for
# the item container, title, link, and (optionally) date. If a site changes
# its HTML, only these selectors need updating.
# ---------------------------------------------------------------------------

EXCHANGE_SOURCES = {
    "Binance": {
        "url": "https://www.binance.com/en/support/announcement",
        # VERIFY: selector may need adjustment if site HTML has changed
        "selectors": {
            "item": "a[href*='/support/announcement/']",
            "title": None,  # title is the anchor text itself
            "link_attr": "href",
            "date": None,
        },
        "base_url": "https://www.binance.com",
    },
    "Coinbase": {
        "url": "https://www.coinbase.com/blog",
        # VERIFY: selector may need adjustment if site HTML has changed
        "selectors": {
            "item": "a[href*='/blog/']",
            "title": None,
            "link_attr": "href",
            "date": None,
        },
        "base_url": "https://www.coinbase.com",
    },
    "Kraken": {
        "url": "https://blog.kraken.com/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "selectors": {
            "item": "article a[href*='blog.kraken.com']",
            "title": None,
            "link_attr": "href",
            "date": "time",
        },
        "base_url": "https://blog.kraken.com",
    },
    "OKX": {
        "url": "https://www.okx.com/help/section/announcements-latest-announcements",
        # VERIFY: selector may need adjustment if site HTML has changed
        "selectors": {
            "item": "a[href*='/help/']",
            "title": None,
            "link_attr": "href",
            "date": None,
        },
        "base_url": "https://www.okx.com",
    },
    "Bybit": {
        "url": "https://announcements.bybit.com/en-US/",
        # VERIFY: selector may need adjustment if site HTML has changed
        "selectors": {
            "item": "a[href*='/article/']",
            "title": None,
            "link_attr": "href",
            "date": None,
        },
        "base_url": "https://announcements.bybit.com",
    },
}

# ---------------------------------------------------------------------------
# Coin keyword list: canonical name -> ticker (matched case-insensitively
# against title + content; the ticker itself is also matched as a word).
# ---------------------------------------------------------------------------

COIN_KEYWORDS = {
    "Bitcoin": "BTC",
    "Ethereum": "ETH",
    "Solana": "SOL",
    "Ripple": "XRP",
    "Cardano": "ADA",
    "Dogecoin": "DOGE",
    "Polkadot": "DOT",
    "Chainlink": "LINK",
    "Litecoin": "LTC",
    "Avalanche": "AVAX",
    "Polygon": "MATIC",
    "Tron": "TRX",
    "Shiba Inu": "SHIB",
    "Uniswap": "UNI",
    "Cosmos": "ATOM",
    "Stellar": "XLM",
    "Monero": "XMR",
    "Ethereum Classic": "ETC",
    "Bitcoin Cash": "BCH",
    "Aptos": "APT",
    "Arbitrum": "ARB",
    "Optimism": "OP",
    "Near Protocol": "NEAR",
    "Filecoin": "FIL",
    "Aave": "AAVE",
    "Algorand": "ALGO",
    "VeChain": "VET",
    "Injective": "INJ",
    "The Graph": "GRT",
    "Sui": "SUI",
    "Tether": "USDT",
    "USD Coin": "USDC",
    "Toncoin": "TON",
    "Hedera": "HBAR",
    "Render": "RNDR",
}

# ---------------------------------------------------------------------------
# Event category keyword rules.
#
# Categories are evaluated IN ORDER; the first category with any keyword
# match wins. Keywords are matched case-insensitively as substrings of
# title + content.
# ---------------------------------------------------------------------------

EVENT_CATEGORY_KEYWORDS = [
    ("Exchange Hack", [
        "exchange hack", "exchange hacked", "exchange breach",
        "hot wallet compromised", "funds stolen from exchange",
        "hacked exchange", "security breach at",
    ]),
    ("Wallet Exploit", [
        "wallet exploit", "wallet drained", "wallet hack",
        "exploit", "drained wallets", "private key leak",
        "phishing attack", "smart contract exploit",
    ]),
    ("Exchange Outage", [
        "outage", "downtime", "service disruption", "trading halted",
        "temporarily unavailable", "degraded performance",
    ]),
    ("Regulatory Announcement", [
        "sec", "regulator", "regulation", "regulatory", "lawsuit",
        "settlement", "cftc", "compliance", "license", "banned",
        "sanction", "court ruling", "legal action",
    ]),
    # Delisting must be evaluated BEFORE Exchange Listing because
    # "delisting" contains the substring "listing".
    ("Delisting", [
        "delist", "delisting", "will remove", "removal of",
        "cease trading", "trading suspension", "suspend trading",
    ]),
    ("Exchange Listing", [
        "will list", "lists ", "listing", "now available for trading",
        "trading pair", "adds support for", "new asset",
        "launches trading",
    ]),
    ("Token Burn", [
        "token burn", "burned tokens", "burn event", "coin burn",
        "supply burn", "buyback and burn",
    ]),
    ("Fork", [
        "hard fork", "soft fork", "chain split", "forked",
        " fork ",
    ]),
    ("Airdrop", [
        "airdrop", "token distribution", "free tokens", "claim tokens",
    ]),
    ("ETF News", [
        "etf", "exchange-traded fund", "spot etf", "etf approval",
        "etf filing", "etf inflow", "etf outflow",
    ]),
    ("Protocol Upgrade", [
        "upgrade", "mainnet launch", "testnet", "hard fork upgrade",
        "network upgrade", "protocol update", "v2 launch", "eip-",
    ]),
    ("Network Congestion", [
        "congestion", "high gas fees", "network overload",
        "transaction backlog", "mempool",
    ]),
    ("Maintenance Notice", [
        "maintenance", "scheduled downtime", "system upgrade window",
        "wallet maintenance", "deposits and withdrawals suspended",
    ]),
]

DEFAULT_CATEGORY = "Other"

# ---------------------------------------------------------------------------
# Importance score rules (see processing/feature_extraction.py)
# ---------------------------------------------------------------------------

IMPORTANCE_BASE = 0.3
IMPORTANCE_HIGH_CATEGORIES = {
    "Exchange Hack", "Wallet Exploit", "Exchange Outage",
    "Regulatory Announcement",
}
IMPORTANCE_MEDIUM_CATEGORIES = {
    "Exchange Listing", "Delisting", "ETF News", "Fork",
}
IMPORTANCE_HIGH_BONUS = 0.3
IMPORTANCE_MEDIUM_BONUS = 0.2
IMPORTANCE_OFFICIAL_BONUS = 0.1
IMPORTANCE_SENTIMENT_BONUS = 0.1
IMPORTANCE_SENTIMENT_THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

# Boilerplate / ad phrases stripped from content during cleaning.
BOILERPLATE_PHRASES = [
    "Subscribe to our newsletter",
    "Sign up for our newsletter",
    "Read more:",
    "Disclaimer:",
    "This article is for informational purposes only",
    "Follow us on Twitter",
    "Follow us on X",
    "Join our Telegram",
    "Advertisement",
    "Sponsored content",
    "Click here to read more",
    "All rights reserved",
]

# Fuzzy title de-duplication threshold (0..1, SequenceMatcher ratio).
TITLE_SIMILARITY_THRESHOLD = 0.90

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

SCHEDULE_INTERVAL_MINUTES = 30

# ---------------------------------------------------------------------------
# Historical backfill (backfill.py)
# ---------------------------------------------------------------------------

BACKFILL_STATE_PATH = DATA_DIR / "backfill_state.json"
BACKFILL_REPORT_PATH = DATA_DIR / "backfill_report.json"

# Default target window, delay between requests, and retry policy.
BACKFILL_TARGET_MONTHS = 24
BACKFILL_REQUEST_DELAY_SECONDS = 1.5
BACKFILL_MAX_RETRIES = 3          # attempts per page/article
BACKFILL_BACKOFF_BASE_SECONDS = 2  # 2s, 4s, 8s between retries
BACKFILL_BATCH_SIZE = 25           # records processed+stored per flush
BACKFILL_MAX_PAGES_SAFETY = 500    # hard cap per paginated exchange source

# News sitemap entry points. All of these were verified live (HTTP 200,
# real XML) at build time — see the child-sitemap URL patterns noted below.
BACKFILL_NEWS_SITEMAPS = {
    # Verified: sitemap index at /sitemap-index.xml (robots.txt canonical);
    # children look like /sitemaps/articles-N.xml
    "CoinDesk": "https://www.coindesk.com/sitemap-index.xml",
    # Verified: index at /sitemap.xml; article children at
    # /sitemap/articles/N.xml. Only 'articles' children are used.
    "Cointelegraph": "https://cointelegraph.com/sitemap.xml",
    # Verified: index at /sitemap_index.xml (robots.txt); children are
    # /post-sitemapN.xml with lastmod on each index entry.
    "Decrypt": "https://decrypt.co/sitemap_index.xml",
    # Verified: Yoast-style index at /sitemap.xml; children are
    # /post-sitemapN.xml with lastmod on each index entry.
    "Bitcoin Magazine": "https://bitcoinmagazine.com/sitemap.xml",
    # Verified: WP index at /sitemap.xml; children like
    # /sitemap_tbco_post_type_post_N.xml with lastmod.
    "The Block": "https://www.theblock.co/sitemap.xml",
}

# Only sitemap URLs matching these substrings are treated as articles
# (filters out category/author/tag/static sitemaps and non-EN locales).
BACKFILL_ARTICLE_SITEMAP_FILTERS = {
    "CoinDesk": ["/sitemaps/articles-"],
    "Cointelegraph": ["/sitemap/articles/"],
    "Decrypt": ["/post-sitemap"],
    "Bitcoin Magazine": ["/post-sitemap"],
    "The Block": ["sitemap_tbco_post_type_post_"],
}

# Exchange announcement pagination. `page_url` is a format string with {n}
# (page 1 = the normal listing page). Reuses EXCHANGE_SOURCES selectors.
BACKFILL_EXCHANGE_PAGINATION = {
    # Verified live: /page/2 returns 200 with server-rendered HTML.
    "Kraken": {"page_url": "https://blog.kraken.com/page/{n}", "first_page_url": "https://blog.kraken.com/"},
    # Verified live: /page/2 returns 200.
    "OKX": {
        "page_url": "https://www.okx.com/help/section/announcements-latest-announcements/page/{n}",
        "first_page_url": "https://www.okx.com/help/section/announcements-latest-announcements",
    },
    # Verified live: ?page=2 returns 200.
    "Bybit": {
        "page_url": "https://announcements.bybit.com/en-US/?page={n}",
        "first_page_url": "https://announcements.bybit.com/en-US/",
    },
    # VERIFY: Binance returned HTTP 202 (bot challenge) with an empty body
    # when probed — pagination will almost certainly yield 0 records
    # without a JS-capable client. Kept so the report shows real coverage.
    "Binance": {
        "page_url": "https://www.binance.com/en/support/announcement?page={n}",
        "first_page_url": "https://www.binance.com/en/support/announcement",
    },
    # VERIFY: Coinbase /blog/page/2 returned HTTP 403 when probed — likely
    # blocked for non-browser clients. Kept so the report shows real coverage.
    "Coinbase": {
        "page_url": "https://www.coinbase.com/blog/page/{n}",
        "first_page_url": "https://www.coinbase.com/blog",
    },
}

# ---------------------------------------------------------------------------
# Unified schema field names (single source of truth for validation,
# DB columns, and CSV headers).
# ---------------------------------------------------------------------------

SCHEMA_FIELDS = [
    "id",
    "source_type",
    "source_name",
    "title",
    "url",
    "published_at",
    "content",
    "collected_at",
    "event_category",
    "affected_coins",
    "sentiment_score",
    "importance_score",
]
