"""
common_schema.py — maps GitHub's native (repo, date, metric) records
onto FundForge's team-wide "Common Requirements (For Everyone)"
metadata contract, so every source's output is queryable in one
uniform shape regardless of which team member built it.

Not every field applies to a numeric developer-activity time series
(no article text, no NLP-derived scores, no country/region/language)
— those columns are stored as NULL rather than a fabricated value,
per the contract's own "wherever applicable" qualifier.

Scope boundary: enrich()/validate_common_record() only run on records
passed through pipeline.py's run_once() (i.e. each day's incremental
collect() slice). backfill_commit_history()'s rows are written directly
to github_raw outside of run_once() and never get a common-schema record.
"""

import datetime

SOURCE = "GitHub REST API"
SOURCE_TYPE = "developer_activity_time_series"
ASSET_CLASS = "Crypto"
SECTOR = "Blockchain/Crypto"

REPO_TO_MARKET = {
    "bitcoin/bitcoin": "Bitcoin",
    "ethereum/go-ethereum": "Ethereum",
    "bnb-chain/bsc": "BNB Chain",
    "ripple/rippled": "XRP",
    "solana-labs/solana": "Solana",
}

EVENT_TYPES = {
    "snapshot": "developer_activity_snapshot",
    "commits": "commit_activity_snapshot",
}

REQUIRED_FIELDS = [
    "id", "source", "source_type", "url", "published_time_utc",
    "ingestion_time_utc", "asset_class", "market", "sector", "event_type",
]


def _url(record: dict) -> str:
    repo = record["repo"]
    if record["metric"] == "snapshot":
        return f"https://api.github.com/repos/{repo}"
    since = record["date"]
    until = (datetime.date.fromisoformat(since) + datetime.timedelta(days=7)).isoformat()
    return f"https://api.github.com/repos/{repo}/commits?since={since}T00:00:00Z&until={until}T00:00:00Z"


def enrich(record: dict) -> dict:
    repo = record["repo"]
    date = record["date"]
    metric = record["metric"]
    market = REPO_TO_MARKET.get(repo, repo)

    return {
        "id": f"github:{repo}:{date}:{metric}",
        "source": SOURCE,
        "source_type": SOURCE_TYPE,
        "url": _url(record),
        "title": None,
        "description": None,
        "full_text": None,
        "published_time_utc": f"{date}T00:00:00Z",
        "ingestion_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "country": None,
        "region": None,
        "language": None,
        "asset_class": ASSET_CLASS,
        "market": market,
        "sector": SECTOR,
        "event_type": EVENT_TYPES.get(metric, metric),
        "importance_score": None,
        "sentiment_score": None,
        "confidence_score": None,
        "keywords": [repo, metric],
        "named_entities": [repo],
        "related_assets": [market],
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
            datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{field} is not a valid ISO 8601 UTC timestamp: {value!r}")

    if record.get("source_type") not in (None, SOURCE_TYPE):
        errors.append(f"source_type must be {SOURCE_TYPE!r}, got {record.get('source_type')!r}")

    return errors
