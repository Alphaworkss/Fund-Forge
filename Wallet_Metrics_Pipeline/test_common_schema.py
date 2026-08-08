"""
test_common_schema.py — Stage 8: Testing (common_schema.py)

Unit tests for the Common Requirements (For Everyone) metadata mapping.
No I/O — pure function tests. Run with: pytest test_common_schema.py
"""

from common_schema import enrich, validate_common_record, SOURCE_TYPE


BITCOIN_RECORD = {
    "coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses",
    "value": 478468.0, "is_partial": False,
}
ETH_RECORD = {
    "coin": "ethereum", "date": "2026-07-30", "metric": "tx_count",
    "value": 1200000, "is_partial": False,
}


def test_enrich_sets_deterministic_id():
    common = enrich(BITCOIN_RECORD)
    assert common["id"] == "wallet_metrics:bitcoin:2026-07-30:active_addresses"


def test_enrich_maps_coin_to_source_and_market():
    common = enrich(BITCOIN_RECORD)
    assert common["source"] == "blockchain.com Charts API"
    assert common["market"] == "Bitcoin"
    assert common["asset_class"] == "Crypto"
    assert common["sector"] == "Blockchain/Crypto"
    assert common["related_assets"] == ["Bitcoin"]


def test_enrich_maps_ethereum_source_correctly():
    common = enrich(ETH_RECORD)
    assert common["source"] == "Etherscan chart CSV export"
    assert common["market"] == "Ethereum"


def test_enrich_sets_url_per_coin_and_metric():
    common = enrich(BITCOIN_RECORD)
    assert common["url"] == "https://api.blockchain.info/charts/n-unique-addresses"

    common_eth = enrich(ETH_RECORD)
    assert common_eth["url"] == "https://etherscan.io/chart/tx?output=csv"


def test_enrich_event_type_is_fixed():
    assert enrich(BITCOIN_RECORD)["event_type"] == "onchain_activity_snapshot"
    assert enrich(ETH_RECORD)["event_type"] == "onchain_activity_snapshot"


def test_enrich_leaves_not_applicable_fields_none():
    common = enrich(BITCOIN_RECORD)
    assert common["title"] is None
    assert common["description"] is None
    assert common["full_text"] is None
    assert common["country"] is None
    assert common["region"] is None
    assert common["language"] is None
    assert common["importance_score"] is None
    assert common["sentiment_score"] is None
    assert common["confidence_score"] is None


def test_enrich_keywords_include_coin_and_metric():
    common = enrich(BITCOIN_RECORD)
    assert common["keywords"] == ["bitcoin", "active_addresses"]
    assert common["named_entities"] == ["bitcoin"]


def test_enrich_passes_through_raw_response():
    record = dict(BITCOIN_RECORD, raw_response={"x": 1785283200, "y": 478468.0})
    common = enrich(record)
    assert common["raw_response"] == {"x": 1785283200, "y": 478468.0}


def test_validate_accepts_well_formed_record():
    assert validate_common_record(enrich(BITCOIN_RECORD)) == []
    assert validate_common_record(enrich(ETH_RECORD)) == []


def test_validate_flags_missing_required_field():
    common = enrich(BITCOIN_RECORD)
    common["asset_class"] = None
    errors = validate_common_record(common)
    assert any("asset_class" in e for e in errors)


def test_validate_flags_wrong_type_score():
    common = enrich(BITCOIN_RECORD)
    common["confidence_score"] = "high"
    errors = validate_common_record(common)
    assert any("confidence_score" in e for e in errors)


def test_validate_flags_non_list_keywords():
    common = enrich(BITCOIN_RECORD)
    common["keywords"] = "bitcoin"
    errors = validate_common_record(common)
    assert any("keywords" in e for e in errors)


def test_validate_flags_bad_timestamp():
    common = enrich(BITCOIN_RECORD)
    common["published_time_utc"] = "not-a-date"
    errors = validate_common_record(common)
    assert any("published_time_utc" in e for e in errors)


def test_validate_flags_non_string_timestamp_without_crashing():
    """Verify that validate_common_record gracefully handles non-string
    timestamp values by returning an error, not crashing."""
    common = enrich(BITCOIN_RECORD)
    common["published_time_utc"] = 12345  # Non-string value

    errors = validate_common_record(common)
    assert any("published_time_utc" in e for e in errors)
    # Should contain a type error, not crash
    assert any("must be a string" in e for e in errors)
