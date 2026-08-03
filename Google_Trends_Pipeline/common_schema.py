"""
common_schema.py — maps Google Trends' native (keyword, date) records
onto FundForge's team-wide "Common Requirements (For Everyone)"
metadata contract, so every source's output is queryable in one
uniform shape regardless of which team member built it.

Not every field applies to a numeric search-interest time series (no
article text, no NLP-derived scores) — those columns are stored as
NULL rather than a fabricated value, per the contract's own "wherever
applicable" qualifier.
"""

from datetime import datetime, timezone
from urllib.parse import quote

SOURCE = "Google Trends (via trendspy)"
SOURCE_TYPE = "search_interest_time_series"
ASSET_CLASS = "Macro/Market Sentiment"
MARKET = "Pakistan"
SECTOR = "Financial Markets"
EVENT_TYPE = "search_trend_snapshot"
COUNTRY = "PK"
REGION = "Pakistan"
RELATED_ASSETS = ["PSX", "KSE100"]

REQUIRED_FIELDS = [
    "id", "source", "source_type", "url", "published_time_utc",
    "ingestion_time_utc", "asset_class", "market", "sector", "event_type",
]


def enrich(record: dict) -> dict:
    keyword = record["keyword"]
    date = record["date"]

    return {
        "id": f"google_trends:{keyword}:{date}",
        "source": SOURCE,
        "source_type": SOURCE_TYPE,
        "url": f"https://trends.google.com/trends/explore?geo={COUNTRY}&q={quote(keyword)}",
        "title": None,
        "description": None,
        "full_text": None,
        "published_time_utc": f"{date}T00:00:00Z",
        "ingestion_time_utc": datetime.now(timezone.utc).isoformat(),
        "country": COUNTRY,
        "region": REGION,
        "language": None,
        "asset_class": ASSET_CLASS,
        "market": MARKET,
        "sector": SECTOR,
        "event_type": EVENT_TYPE,
        "importance_score": None,
        "sentiment_score": None,
        "confidence_score": None,
        "keywords": [keyword],
        "named_entities": [keyword],
        "related_assets": list(RELATED_ASSETS),
        "raw_response": record.get("raw_response"),
    }


def validate_common_record(record: dict) -> list[str]:
    errors = []

    for field in REQUIRED_FIELDS:
        if not record.get(field):
            errors.append(f"missing required field: {field}")

    for field in ("importance_score", "sentiment_score", "confidence_score"):
        value = record.get(field)
        if value is not None and not isinstance(value, (int, float)):
            errors.append(f"{field} must be numeric or None, got {type(value).__name__}")

    for field in ("keywords", "named_entities", "related_assets"):
        value = record.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} must be a list, got {type(value).__name__}")

    for field in ("published_time_utc", "ingestion_time_utc"):
        value = record.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            errors.append(f"{field} must be a string, got {type(value).__name__}")
            continue
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{field} is not a valid ISO 8601 UTC timestamp: {value!r}")

    if record.get("source_type") not in (None, SOURCE_TYPE):
        errors.append(f"source_type must be {SOURCE_TYPE!r}, got {record.get('source_type')!r}")

    return errors
