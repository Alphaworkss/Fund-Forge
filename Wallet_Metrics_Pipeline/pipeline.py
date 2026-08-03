"""
pipeline.py — Orchestrator

Chains all stages together:
  collect -> upsert_raw -> get_raw_records -> clean -> transform ->
  upsert_features -> export_to_excel
  collect -> enrich (common schema) -> validate -> upsert_common

run_once() reads the full wallet_metrics_raw table back via
get_raw_records() after storing today's fresh collect() output, and
computes features over that full history — not just what collect()
returned this run — because meaningful rolling/pct-change/z-score
features need more than one day's data point. Common-schema
enrichment, by contrast, runs on new_records only — each run's
ingestion_time_utc should reflect records actually ingested this run,
not the full history.

This is the one entry point both the Task Scheduler job (Task 4) and a
one-off manual run should call.
"""

import logging

from collect import collect
from clean import clean
from transform import transform
from common_schema import enrich, validate_common_record
from storage import get_connection, upsert_raw, upsert_features, get_raw_records, upsert_common, DB_PATH
from export_excel import export_to_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_once(db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        new_records = collect()
        if not new_records:
            logger.warning("No records collected from any source — check network/rate limits, or retry later.")
            return
        upsert_raw(conn, new_records)
        logger.info("Stored %d new raw records", len(new_records))

        common_records = []
        for r in new_records:
            common = enrich(r)
            errors = validate_common_record(common)
            if errors:
                logger.warning("Dropping invalid common record %s: %s", common.get("id"), errors)
                continue
            common_records.append(common)
        upsert_common(conn, common_records)
        logger.info("Stored %d common-schema records", len(common_records))

        all_records = get_raw_records(conn)
        cleaned = clean(all_records)
        featured = transform(cleaned)
        feature_records = featured.to_dict(orient="records")
        upsert_features(conn, feature_records)
        logger.info(
            "Stored %d feature records (from %d total raw records)",
            len(feature_records),
            len(all_records),
        )

        exported = export_to_excel(conn)
        if not exported:
            logger.error(
                "Pipeline run stored data successfully but the Excel export failed — see the error above."
            )
    finally:
        conn.close()


if __name__ == "__main__":
    run_once()
