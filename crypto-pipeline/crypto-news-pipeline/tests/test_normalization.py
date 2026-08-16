"""Tests for processing/normalization.py schema compliance."""

import pytest

from config import SCHEMA_FIELDS
from processing.normalization import (
    SchemaValidationError,
    generate_id,
    normalize_record,
    normalize_records,
    validate_record,
)


def _cleaned_record(**overrides):
    rec = {
        "title": "Binance lists SOL trading pair",
        "url": "https://binance.com/announce/1",
        "published_at": "2025-01-06T14:30:00+00:00",
        "raw_content": "Binance will list a new Solana trading pair.",
        "source_name": "Binance",
        "source_type": "exchange_announcement",
    }
    rec.update(overrides)
    return rec


class TestGenerateId:
    def test_deterministic(self):
        assert generate_id("https://a.com", "Title") == generate_id("https://a.com", "Title")

    def test_differs_by_url(self):
        assert generate_id("https://a.com", "Title") != generate_id("https://b.com", "Title")

    def test_differs_by_title(self):
        assert generate_id("https://a.com", "Title A") != generate_id("https://a.com", "Title B")

    def test_is_hex_sha256(self):
        result = generate_id("https://a.com", "Title")
        assert len(result) == 64
        int(result, 16)  # raises if not hex


class TestNormalizeRecord:
    def test_output_matches_schema_exactly(self):
        result = normalize_record(_cleaned_record())
        assert set(result.keys()) == set(SCHEMA_FIELDS)

    def test_field_mapping(self):
        result = normalize_record(_cleaned_record())
        assert result["source_type"] == "exchange_announcement"
        assert result["source_name"] == "Binance"
        assert result["content"] == "Binance will list a new Solana trading pair."
        assert result["published_at"] == "2025-01-06T14:30:00+00:00"

    def test_defaults_for_feature_fields(self):
        result = normalize_record(_cleaned_record())
        assert result["event_category"] == "Other"
        assert result["affected_coins"] == ""
        assert result["sentiment_score"] == 0.0
        assert result["importance_score"] == 0.0

    def test_collected_at_is_set(self):
        result = normalize_record(_cleaned_record())
        assert result["collected_at"]
        assert "T" in result["collected_at"]


class TestValidateRecord:
    def test_valid_record_passes(self):
        validate_record(normalize_record(_cleaned_record()))

    def test_missing_field_raises(self):
        record = normalize_record(_cleaned_record())
        del record["title"]
        with pytest.raises(SchemaValidationError):
            validate_record(record)

    def test_extra_field_raises(self):
        record = normalize_record(_cleaned_record())
        record["bogus"] = 1
        with pytest.raises(SchemaValidationError):
            validate_record(record)

    def test_wrong_type_raises(self):
        record = normalize_record(_cleaned_record())
        record["sentiment_score"] = "very positive"
        with pytest.raises(SchemaValidationError):
            validate_record(record)

    def test_bad_source_type_raises(self):
        record = normalize_record(_cleaned_record())
        record["source_type"] = "tweet"
        with pytest.raises(SchemaValidationError):
            validate_record(record)

    def test_out_of_range_sentiment_raises(self):
        record = normalize_record(_cleaned_record())
        record["sentiment_score"] = 2.5
        with pytest.raises(SchemaValidationError):
            validate_record(record)

    def test_out_of_range_importance_raises(self):
        record = normalize_record(_cleaned_record())
        record["importance_score"] = 1.5
        with pytest.raises(SchemaValidationError):
            validate_record(record)


class TestNormalizeRecordsBatch:
    def test_bad_records_dropped_not_passed_through(self):
        good = _cleaned_record()
        bad = _cleaned_record(url="https://x.com/2")
        del bad["source_type"]  # will raise KeyError during normalization
        result = normalize_records([good, bad])
        assert len(result) == 1
        assert result[0]["url"] == good["url"]

    def test_all_outputs_valid(self):
        records = [
            _cleaned_record(),
            _cleaned_record(url="https://x.com/2", title="Another headline entirely"),
        ]
        result = normalize_records(records)
        assert len(result) == 2
        for record in result:
            validate_record(record)  # should not raise
