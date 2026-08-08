"""
Scheduler: runs the full pipeline every SCHEDULE_INTERVAL_MINUTES using
APScheduler. A failed run is logged and never kills the scheduler process.

Start continuous automated runs with:
    python scheduler/run_scheduler.py
"""

import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import SCHEDULE_INTERVAL_MINUTES  # noqa: E402
from pipeline import run_pipeline  # noqa: E402

logger = logging.getLogger("scheduler")


def scheduled_job() -> None:
    """One scheduled pipeline run, fully wrapped so failures never
    propagate up and stop the scheduler."""
    try:
        summary = run_pipeline()
        logger.info("Scheduled run finished: %s", summary)
    except Exception:
        logger.exception("Scheduled pipeline run failed — scheduler continues")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        scheduled_job,
        trigger="interval",
        minutes=SCHEDULE_INTERVAL_MINUTES,
        id="crypto_pipeline",
        max_instances=1,          # never overlap runs
        coalesce=True,            # collapse missed runs into one
        misfire_grace_time=300,   # tolerate up to 5 min of lateness
        next_run_time=None,
    )

    logger.info(
        "Starting scheduler: pipeline every %d minutes (first run now)",
        SCHEDULE_INTERVAL_MINUTES,
    )
    # Kick off an immediate first run, then continue on the interval.
    scheduled_job()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
