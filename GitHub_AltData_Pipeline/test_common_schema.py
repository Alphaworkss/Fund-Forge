"""
test_common_schema.py — Stage 8: Testing (common_schema.py)

Unit tests for the Common Requirements (For Everyone) metadata mapping.
No I/O — pure function tests. Run with: pytest test_common_schema.py
"""

from common_schema import enrich, validate_common_record, SOURCE_TYPE


SNAPSHOT_RECORD = {
    "repo": "bitcoin/bitcoin", "date": "2026-07-30", "metric": "snapshot",
    "stars": 100, "forks": 20, "is_partial": False,
}
COMMITS_RECORD = {
    "repo": "bitcoin/bitcoin", "date": "2026-07-27", "metric": "commits",
    "commits": 5, "is_partial": False,
}


def test_enrich_sets_deterministic_id():
    common = enrich(SNAPSHOT_RECORD)
    assert common["id"] == "github:bitcoin/bitcoin:2026-07-30:snapshot"


def test_enrich_maps_repo_to_market():
    common = enrich(SNAPSHOT_RECORD)
    assert common["market"] == "Bitcoin"
    assert common["asset_class"] == "Crypto"
    assert common["sector"] == "Blockchain/Crypto"
    assert common["related_assets"] == ["Bitcoin"]


def test_enrich_falls_back_to_repo_name_for_unmapped_repo():
    record = dict(SNAPSHOT_RECORD, repo="someorg/somerepo")
    common = enrich(record)
    assert common["market"] == "someorg/somerepo"


def test_enrich_sets_event_type_per_metric():
    assert enrich(SNAPSHOT_RECORD)["event_type"] == "developer_activity_snapshot"
    assert enrich(COMMITS_RECORD)["event_type"] == "commit_activity_snapshot"


def test_enrich_snapshot_url_is_repo_endpoint():
    common = enrich(SNAPSHOT_RECORD)
    assert common["url"] == "https://api.github.com/repos/bitcoin/bitcoin"


def test_enrich_commits_url_includes_since_and_until():
    common = enrich(COMMITS_RECORD)
    assert common["url"] == (
        "https://api.github.com/repos/bitcoin/bitcoin/commits"
        "?since=2026-07-27T00:00:00Z&until=2026-08-03T00:00:00Z"
    )


def test_enrich_leaves_not_applicable_fields_none():
    common = enrich(SNAPSHOT_RECORD)
    assert common["title"] is None
    assert common["description"] is None
    assert common["full_text"] is None
    assert common["country"] is None
    assert common["region"] is None
    assert common["language"] is None
    assert common["importance_score"] is None
    assert common["sentiment_score"] is None
    assert common["confidence_score"] is None


def test_enrich_keywords_include_repo_and_metric():
    common = enrich(COMMITS_RECORD)
    assert common["keywords"] == ["bitcoin/bitcoin", "commits"]
    assert common["named_entities"] == ["bitcoin/bitcoin"]


def test_enrich_passes_through_raw_response():
    record = dict(SNAPSHOT_RECORD, raw_response={"stargazers_count": 100, "forks_count": 20})
    common = enrich(record)
    assert common["raw_response"] == {"stargazers_count": 100, "forks_count": 20}


def test_validate_accepts_well_formed_record():
    assert validate_common_record(enrich(SNAPSHOT_RECORD)) == []
    assert validate_common_record(enrich(COMMITS_RECORD)) == []


def test_validate_flags_missing_required_field():
    common = enrich(SNAPSHOT_RECORD)
    common["market"] = None
    errors = validate_common_record(common)
    assert any("market" in e for e in errors)


def test_validate_flags_wrong_type_score():
    common = enrich(SNAPSHOT_RECORD)
    common["importance_score"] = "high"
    errors = validate_common_record(common)
    assert any("importance_score" in e for e in errors)


def test_validate_flags_non_list_related_assets():
    common = enrich(SNAPSHOT_RECORD)
    common["related_assets"] = "Bitcoin"
    errors = validate_common_record(common)
    assert any("related_assets" in e for e in errors)


def test_validate_flags_bad_timestamp():
    common = enrich(SNAPSHOT_RECORD)
    common["ingestion_time_utc"] = "not-a-date"
    errors = validate_common_record(common)
    assert any("ingestion_time_utc" in e for e in errors)


def test_validate_flags_non_string_timestamp_without_crashing():
    """Verify that validate_common_record gracefully handles non-string
    timestamp values by returning an error, not crashing."""
    common = enrich(SNAPSHOT_RECORD)
    common["ingestion_time_utc"] = 12345  # Non-string value

    errors = validate_common_record(common)
    assert any("ingestion_time_utc" in e for e in errors)
    # Should contain a type error, not crash
    assert any("must be a string" in e for e in errors)
