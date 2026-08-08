"""
test_common_schema.py — Stage 8: Testing (common_schema.py)

Unit tests for the Common Requirements (For Everyone) metadata mapping.
No I/O — pure function tests. Run with: pytest test_common_schema.py
"""

from common_schema import enrich, validate_common_record, SOURCE_TYPE


SAMPLE_RECORD = {"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False}


def test_enrich_sets_deterministic_id():
    common = enrich(SAMPLE_RECORD)
    assert common["id"] == "google_trends:PSX:2026-07-01"


def test_enrich_sets_required_fields():
    common = enrich(SAMPLE_RECORD)
    assert common["source"] == "Google Trends (via trendspy)"
    assert common["source_type"] == SOURCE_TYPE
    assert common["url"] == "https://trends.google.com/trends/explore?geo=PK&q=PSX"
    assert common["published_time_utc"] == "2026-07-01T00:00:00Z"
    assert common["asset_class"] == "Macro/Market Sentiment"
    assert common["market"] == "Pakistan"
    assert common["sector"] == "Financial Markets"
    assert common["event_type"] == "search_trend_snapshot"
    assert common["country"] == "PK"
    assert common["region"] == "Pakistan"


def test_enrich_leaves_not_applicable_fields_none():
    common = enrich(SAMPLE_RECORD)
    assert common["title"] is None
    assert common["description"] is None
    assert common["full_text"] is None
    assert common["language"] is None
    assert common["importance_score"] is None
    assert common["sentiment_score"] is None
    assert common["confidence_score"] is None


def test_enrich_sets_keyword_derived_lists():
    common = enrich(SAMPLE_RECORD)
    assert common["keywords"] == ["PSX"]
    assert common["named_entities"] == ["PSX"]
    assert common["related_assets"] == ["PSX", "KSE100"]


def test_enrich_passes_through_raw_response():
    record = dict(SAMPLE_RECORD, raw_response={"PSX": 40, "isPartial": False})
    common = enrich(record)
    assert common["raw_response"] == {"PSX": 40, "isPartial": False}


def test_enrich_raw_response_none_when_absent():
    common = enrich(SAMPLE_RECORD)
    assert common["raw_response"] is None


def test_validate_accepts_well_formed_record():
    common = enrich(SAMPLE_RECORD)
    assert validate_common_record(common) == []


def test_validate_flags_missing_required_field():
    common = enrich(SAMPLE_RECORD)
    common["source"] = None
    errors = validate_common_record(common)
    assert any("source" in e for e in errors)


def test_validate_flags_wrong_type_score():
    common = enrich(SAMPLE_RECORD)
    common["sentiment_score"] = "very positive"
    errors = validate_common_record(common)
    assert any("sentiment_score" in e for e in errors)


def test_validate_flags_non_list_keywords():
    common = enrich(SAMPLE_RECORD)
    common["keywords"] = "PSX"
    errors = validate_common_record(common)
    assert any("keywords" in e for e in errors)


def test_validate_flags_bad_timestamp():
    common = enrich(SAMPLE_RECORD)
    common["published_time_utc"] = "not-a-date"
    errors = validate_common_record(common)
    assert any("published_time_utc" in e for e in errors)


def test_validate_flags_wrong_source_type():
    common = enrich(SAMPLE_RECORD)
    common["source_type"] = "something_else"
    errors = validate_common_record(common)
    assert any("source_type" in e for e in errors)


def test_enrich_related_assets_is_not_shared_between_calls():
    """Verify that each call to enrich() returns a fresh copy of related_assets,
    not a shared reference to the module-level RELATED_ASSETS list."""
    record1 = enrich(SAMPLE_RECORD)
    record2 = enrich(SAMPLE_RECORD)

    # Mutate the first record's related_assets
    record1["related_assets"].append("SOMETHING")

    # Verify the second record's related_assets is unaffected
    assert record2["related_assets"] == ["PSX", "KSE100"]
    assert record1["related_assets"] == ["PSX", "KSE100", "SOMETHING"]


def test_validate_flags_non_string_timestamp_without_crashing():
    """Verify that validate_common_record gracefully handles non-string
    timestamp values by returning an error, not crashing."""
    common = enrich(SAMPLE_RECORD)
    common["published_time_utc"] = 12345  # Non-string value

    errors = validate_common_record(common)
    assert any("published_time_utc" in e for e in errors)
    # Should contain a type error, not crash
    assert any("must be a string" in e for e in errors)
