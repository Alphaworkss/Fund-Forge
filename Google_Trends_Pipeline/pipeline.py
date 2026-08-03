"""
pipeline.py — Orchestrator

Chains all stages together:
  collect -> clean -> transform (normalize + feature extraction) -> store
  collect -> enrich (common schema) -> validate -> store

This is the single entry point everything else (the scheduler, a manual
run, a test) should call — it's the one place that knows the full
sequence, so no other file needs to.
"""

import logging

from collect import collect
from clean import clean
from transform import transform
from common_schema import enrich, validate_common_record
from storage import get_connection, upsert_raw, upsert_features, upsert_common
from export_excel import export_to_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_once(db_path: str = "alt_data.db") -> None:
    conn = get_connection(db_path)
    try:
        raw_records = collect()
        if not raw_records:
            logger.warning("No records collected — check keywords/timeframe, or retry later (rate limit).")
            return
        upsert_raw(conn, raw_records)
        logger.info("Stored %d raw records", len(raw_records))

        common_records = []
        for r in raw_records:
            common = enrich(r)
            errors = validate_common_record(common)
            if errors:
                logger.warning("Dropping invalid common record %s: %s", common.get("id"), errors)
                continue
            common_records.append(common)
        upsert_common(conn, common_records)
        logger.info("Stored %d common-schema records", len(common_records))

        cleaned = clean(raw_records)
        featured = transform(cleaned)
        feature_records = featured.to_dict(orient="records")
        upsert_features(conn, feature_records)
        logger.info("Stored %d feature records", len(feature_records))

        export_to_excel(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    run_once()
