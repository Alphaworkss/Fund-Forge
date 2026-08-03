"""
collect.py — Stage 1: Data Collection

Pulls raw interest-over-time data for a set of keywords from Google Trends
via trendspy (github.com/sdil87/trendspy).

Note: this used to use `pytrends`, but that library's GitHub repo was
archived by its maintainer in April 2025 and hasn't been updated since
2023 — Google changed how it issues an access cookie, pytrends never
adapted, and it now fails with a 429 on the very first call for
essentially everyone. trendspy is a maintained replacement that handles
the current cookie/session flow correctly.

Returns plain dicts. No cleaning or transformation happens here — that's
clean.py and transform.py's job. Keeping this stage "dumb" makes it easy
to test the other stages without hitting the network.
"""

import datetime
import logging
import time

from trendspy import Trends

logger = logging.getLogger(__name__)

# These track Pakistani market/economic conditions relevant to mutual fund
# performance, matching FundForge's use of this data as a market-conditions
# signal alongside the financial news sentiment score. Add AMC or fund
# names here too if you want fund-level search interest.
KEYWORDS = [
    "PSX",
    "KSE 100",
    "SBP interest rate",
    "Pakistan inflation",
    "mutual funds Pakistan",
]

# How far back to pull on each run.
HISTORY_YEARS = 2

GEO = "PK"

# Google Trends only scores interest 0-100 WITHIN a single batch of up to
# 5 keywords queried together — scores are only directly comparable to
# each other if they came from the same batch. With 5 keywords this fits
# in one batch; if you add more, later keywords won't be on the same
# scale as earlier ones unless you keep batches under 5.
# (transform.py's normalization step is designed around this limitation.)
BATCH_SIZE = 5


def _default_timeframe(years: int = HISTORY_YEARS) -> str:
    """
    Build a trendspy/Google Trends date-range string ('YYYY-MM-DD YYYY-MM-DD')
    covering the last `years` years, ending today.

    This is computed fresh on every call rather than being a fixed module
    constant, so it still means "the last 2 years" correctly even inside a
    long-running process like scheduler.py, which imports this module once
    and then calls collect() again every day for weeks/months — a frozen
    constant would otherwise slowly go stale.

    Both this and the old "today 12-m" style span well beyond Google's
    ~9-month daily/weekly granularity cutoff, so — like before — the data
    that comes back is WEEKLY, not daily (see the note in transform.py).
    """
    end = datetime.date.today()
    start = end - datetime.timedelta(days=365 * years)
    return f"{start.isoformat()} {end.isoformat()}"


def collect(keywords=None, timeframe: str = None, geo: str = GEO) -> list[dict]:
    keywords = keywords or KEYWORDS
    timeframe = timeframe or _default_timeframe()
    tr = Trends()
    records = []

    for i in range(0, len(keywords), BATCH_SIZE):
        batch = keywords[i:i + BATCH_SIZE]
        try:
            df = tr.interest_over_time(batch, timeframe=timeframe, geo=geo)
        except Exception:
            logger.exception("Failed to fetch batch %s", batch)
            continue

        if df is None or df.empty:
            logger.warning("No data returned for batch: %s", batch)
            continue

        has_partial_col = "isPartial" in df.columns
        for kw in batch:
            if kw not in df.columns:
                continue
            for dt, value in df[kw].items():
                records.append(
                    {
                        "keyword": kw,
                        "date": dt.strftime("%Y-%m-%d"),
                        "interest": int(value),
                        "is_partial": bool(df.loc[dt, "isPartial"]) if has_partial_col else False,
                        "raw_response": df.loc[dt].to_dict(),
                    }
                )

        time.sleep(2)  # be polite between batches, avoid rate limiting

    return records