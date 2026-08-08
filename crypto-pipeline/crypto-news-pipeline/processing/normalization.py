"""
Normalization: map cleaned collector records into the exact unified schema,
generate deterministic ids, and validate every output record.

Unified schema:
    id, source_type, source_name, title, url, published_at, content,
    collected_at, event_category, affected_coins, sentiment_score,
    importance_score
"""

import hashlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import SCHEMA_FIELDS  # noqa: E402

logger = logging.getLogger(__name__)

VALID_SOURCE_TYPES = {"news", "exchange_announcement"}

# Expected python types for each schema field.
_FIELD_TYPES = {
    "id": str,
    "source_type": str,
    "source_name": str,
    "title": str,
    "url": str,
    "published_at": str,
    "content": str,
    "collected_at": str,
    "event_category": str,
    "affected_coins": str,
    "sentiment_score": float,
    "importance_score": float,
}


class SchemaValidationError(ValueError):
    """Raised when a normalized record does not match the unified schema."""


def generate_id(url: str, title: str) -> str:
    """Deterministic, stable id: SHA-256 hash of url+title."""
    return hashlib.sha256(f"{url}|{title}".encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    """Current time as UTC ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def normalize_record(record: dict, collected_at: Optional[str] = None) -> dict:
    """
    Map one cleaned collector record into the unified schema.
    Feature fields (event_category, affected_coins, sentiment_score,
    importance_score) are initialized to defaults and filled in by
    feature_extraction.
    """
    url = record["url"]
    title = record["title"]

    return {
        "id": generate_id(url, title),
        "source_type": record["source_type"],
        "source_name": record["source_name"],
        "title": title,
        "url": url,
        "published_at": record["published_at"],
        "content": record.get("raw_content", "") or "",
        "collected_at": collected_at or utc_now_iso(),
        "event_category": "Other",
        "affected_coins": "",
        "sentiment_score": 0.0,
        "importance_score": 0.0,
    }


def validate_record(record: dict) -> None:
    """
    Validate a record against the unified schema. Raises
    SchemaValidationError on any mismatch.
    """
    keys = set(record.keys())
    expected = set(SCHEMA_FIELDS)
    if keys != expected:
        missing = expected - keys
        extra = keys - expected
        raise SchemaValidationError(
            f"Schema field mismatch: missing={sorted(missing)}, extra={sorted(extra)}"
        )

    for field, expected_type in _FIELD_TYPES.items():
        value = record[field]
        if expected_type is float and isinstance(value, int):
            # ints are acceptable where floats are expected
            continue
        if not isinstance(value, expected_type):
            raise SchemaValidationError(
                f"Field '{field}' has type {type(value).__name__}, expected {expected_type.__name__}"
            )

    if record["source_type"] not in VALID_SOURCE_TYPES:
        raise SchemaValidationError(
            f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}, got {record['source_type']!r}"
        )

    if not record["id"] or not record["title"] or not record["url"]:
        raise SchemaValidationError("id, title, and url must be non-empty")

    if not -1.0 <= float(record["sentiment_score"]) <= 1.0:
        raise SchemaValidationError("sentiment_score must be in [-1.0, 1.0]")

    if not 0.0 <= float(record["importance_score"]) <= 1.0:
        raise SchemaValidationError("importance_score must be in [0.0, 1.0]")


def normalize_records(records: list[dict]) -> list[dict]:
    """
    Normalize a batch of cleaned records. Records that fail validation are
    logged and skipped, never silently passed through.
    """
    collected_at = utc_now_iso()
    normalized: list[dict] = []

    for record in records:
        try:
            norm = normalize_record(record, collected_at=collected_at)
            validate_record(norm)
            normalized.append(norm)
        except (KeyError, SchemaValidationError) as exc:
            logger.error(
                "Dropping record failing normalization (%s): %s",
                exc, record.get("url", "<no url>"),
            )

    logger.info("Normalization: %d in, %d out", len(records), len(normalized))
    return normalized
