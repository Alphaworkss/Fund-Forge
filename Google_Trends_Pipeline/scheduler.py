"""
scheduler.py — Stage 7: Scheduler / Automation

Runs pipeline.run_once() daily. See pipeline.py for the full
collect -> clean -> transform -> store sequence this triggers each time.

Google Trends returns a full historical window on every call, so unlike
a live-price feed there's no benefit to running this frequently — once a
day is enough to keep it current, and running it too often raises the
odds of pytrends getting rate-limited by Google.

This keeps a Python process alive in the foreground. For a more robust
long-running setup (survives reboots, no dangling process), skip this
file and instead schedule `python pipeline.py` directly:
  - cron on Linux/Mac:       0 8 * * *  cd /path/to/google_trends_pipeline && python pipeline.py
  - Task Scheduler on Windows (daily trigger running the same command)

Run:  python scheduler.py
"""

import logging
import time

import schedule

from pipeline import run_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RUN_AT = "08:00"  # 24h "HH:MM", local machine time


def job():
    try:
        run_once()
    except Exception:
        logger.exception("Pipeline run failed")


if __name__ == "__main__":
    job()  # run once immediately on startup
    schedule.every().day.at(RUN_AT).do(job)
    logger.info("Scheduler started — running daily at %s. Ctrl+C to stop.", RUN_AT)
    while True:
        schedule.run_pending()
        time.sleep(60)
