"""
common_schema.py — maps this pipeline's native (coin, date, metric)
records onto FundForge's team-wide "Common Requirements (For Everyone)"
metadata contract, so every source's output is queryable in one
uniform shape regardless of which team member built it.

Not every field applies to a numeric on-chain metric time series (no
article text, no NLP-derived scores, no country/region/language) —
those columns are stored as NULL rather than a fabricated value, per
the contract's own "wherever applicable" qualifier.
"""

from datetime import datetime, timezone

SOURCE_TYPE = "onchain_wallet_metric_time_series"
ASSET_CLASS = "Crypto"
SECTOR = "Blockchain/Crypto"
EVENT_TYPE = "onchain_activity_snapshot"

COIN_SOURCES = {
    "bitcoin": "blockchain.com Charts API",
    "ethereum": "Etherscan chart CSV export",
    "bnb": "BscScan chart CSV export",
}

COIN_MARKET = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "bnb": "BNB Chain",
}

COIN_URLS = {
    ("bitcoin", "active_addresses"): "https://api.blockchain.info/charts/n-unique-addresses",
    ("bitcoin", "tx_count"): "https://api.blockchain.info/charts/n-transactions",
    ("bitcoin", "tx_volume"): "https://api.blockchain.info/charts/estimated-transaction-volume",
    ("ethereum", "tx_count"): "https://etherscan.io/chart/tx?output=csv",
    ("ethereum", "active_addresses"): "https://etherscan.io/chart/active-address?output=csv",
    ("bnb", "tx_count"): "https://bscscan.com/chart/tx?output=csv",
}

REQUIRED_FIELDS = [
    "id", "source", "source_type", "url", "published_time_utc",
    "ingestion_time_utc", "asset_class", "market", "sector", "event_type",
]


def enrich(record: dict) -> dict:
    coin = record["coin"]
    date = record["date"]
    metric = record["metric"]
    market = COIN_MARKET.get(coin, coin)

    return {
        "id": f"wallet_metrics:{coin}:{date}:{metric}",
        "source": COIN_SOURCES.get(coin, "unknown"),
        "source_type": SOURCE_TYPE,
        "url": COIN_URLS.get((coin, metric)),
        "title": None,
        "description": None,
        "full_text": None,
        "published_time_utc": f"{date}T00:00:00Z",
        "ingestion_time_utc": datetime.now(timezone.utc).isoformat(),
        "country": None,
        "region": None,
        "language": None,
        "asset_class": ASSET_CLASS,
        "market": market,
        "sector": SECTOR,
        "event_type": EVENT_TYPE,
        "importance_score": None,
        "sentiment_score": None,
        "confidence_score": None,
        "keywords": [coin, metric],
        "named_entities": [coin],
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
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{field} is not a valid ISO 8601 UTC timestamp: {value!r}")

    if record.get("source_type") not in (None, SOURCE_TYPE):
        errors.append(f"source_type must be {SOURCE_TYPE!r}, got {record.get('source_type')!r}")

    return errors
