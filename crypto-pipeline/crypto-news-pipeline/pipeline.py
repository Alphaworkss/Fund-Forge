"""
Pipeline orchestrator: collect -> clean -> normalize -> extract features
-> store in SQLite -> export CSV -> log summary.

Run a single manual pass with:
    python pipeline.py
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collectors.exchange_collector import collect_all_exchanges  # noqa: E402
from collectors.news_collector import collect_all_news  # noqa: E402
from processing.cleaning import clean_records  # noqa: E402
from processing.feature_extraction import extract_features_batch  # noqa: E402
from processing.normalization import normalize_records  # noqa: E402
from storage.csv_export import export_to_csv  # noqa: E402
from storage.db import get_engine, save_batch  # noqa: E402

logger = logging.getLogger("pipeline")


def run_pipeline(raw_records: Optional[list[dict]] = None) -> dict:
    """
    Execute one full pipeline pass and return a summary dict.

    `raw_records` may be supplied (e.g. by tests) to bypass live network
    collection; when None, both live collectors run.
    """
    start = time.monotonic()
    errors = 0

    # 1. Collect
    if raw_records is None:
        raw_records = []
        try:
            raw_records.extend(collect_all_news())
        except Exception as exc:
            logger.error("News collection stage failed: %s", exc)
            errors += 1
        try:
            raw_records.extend(collect_all_exchanges())
        except Exception as exc:
            logger.error("Exchange collection stage failed: %s", exc)
            errors += 1
    collected = len(raw_records)

    # 2. Clean (validate + de-duplicate)
    cleaned = clean_records(raw_records)

    # 3. Normalize into the unified schema
    normalized = normalize_records(cleaned)

    # 4. Extract features
    enriched = extract_features_batch(normalized)

    # 5. Store in SQLite (duplicates skipped)
    engine = get_engine()
    stored = save_batch(engine, enriched)

    # 6. Export the full DB to CSV — always the last step of every run
    export_to_csv(engine)

    duration = time.monotonic() - start
    summary = {
        "collected": collected,
        "cleaned": len(cleaned),
        "normalized": len(normalized),
        "enriched": len(enriched),
        "stored_new": stored,
        "errors": errors,
        "duration_seconds": round(duration, 2),
    }
    logger.info(
        "Pipeline run complete: collected=%d cleaned=%d normalized=%d "
        "stored_new=%d errors=%d duration=%.2fs",
        summary["collected"], summary["cleaned"], summary["normalized"],
        summary["stored_new"], summary["errors"], summary["duration_seconds"],
    )
    return summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    result = run_pipeline()
    print(f"Run summary: {result}")
