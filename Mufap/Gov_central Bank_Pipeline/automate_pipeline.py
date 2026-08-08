"""
Runs scraper.py's daily collection automatically, once every 24 hours.

"""

import time
import schedule

from scraper import run_daily

RUN_TIME = "06:00"  # 24-hour format, runs once per day at this time


def job():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled daily run...")
    try:
        run_daily()
    except Exception as e:
        print(f"  [error] Daily run failed: {e}")


if __name__ == "__main__":
    schedule.every().day.at(RUN_TIME).do(job)
    print(f"Scheduler started. Will run daily collection every day at {RUN_TIME}.")
    print("Leave this terminal window open. Press Ctrl+C to stop.")

    # Run once immediately on startup too, so you don't wait a full day to see it work
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)
