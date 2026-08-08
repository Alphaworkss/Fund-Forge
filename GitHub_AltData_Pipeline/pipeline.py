"""
pipeline.py — Orchestrator

Chains all stages together:
  collect -> upsert_raw -> get_raw_records -> clean -> transform ->
  upsert_features -> export_to_excel
  collect -> enrich (common schema) -> validate -> upsert_common

Google Trends' pipeline.py does transform(clean(collect())) directly —
that works there because its collect() always re-pulls its entire
window every run. This project's collect() deliberately does not (see
design.md): it only returns today's incremental slice (~15 records).
So run_once() reads the full github_raw table back via
get_raw_records() after storing today's slice, and computes features
over that full history — not just what collect() returned this run.
Common-schema enrichment, by contrast, runs on new_records only — each
run's ingestion_time_utc should reflect records actually ingested this
run, not the full history.

backfill_commit_history() is never called from here. It stays a
strictly separate, manually-run, one-time operation (see design.md);
its rows never get a common-schema record — see common_schema.py's
module docstring for that scope boundary.

This is the one entry point both a future Task Scheduler job and a
one-off manual run should call.
"""

import logging

from collect import collect
from clean import clean
from transform import transform
from common_schema import enrich, validate_common_record
from storage import get_connection, upsert_raw, upsert_features, get_raw_records, upsert_common
from export_excel import export_to_excel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_once(db_path: str = "github_data.db") -> None:
    conn = get_connection(db_path)
    try:
        new_records = collect()
        if not new_records:
            logger.warning("No records collected — check GITHUB_TOKEN/rate limit, or retry later.")
            raise SystemExit(1)
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

        export_to_excel(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    run_once()
