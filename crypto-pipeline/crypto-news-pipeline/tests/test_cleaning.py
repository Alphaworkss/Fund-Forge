"""Tests for processing/cleaning.py edge cases."""

from processing.cleaning import (
    clean_record,
    clean_records,
    clean_text,
    deduplicate,
    normalize_whitespace,
    strip_html,
    titles_similar,
    to_utc_iso,
)


class TestStripHtml:
    def test_removes_tags(self):
        assert strip_html("<p>Hello <b>world</b></p>").strip() == "Hello  world".strip()

    def test_empty_input(self):
        assert strip_html("") == ""

    def test_plain_text_unchanged(self):
        assert strip_html("No tags here").strip() == "No tags here"


class TestNormalizeWhitespace:
    def test_collapses_runs(self):
        assert normalize_whitespace("a  b\n\tc   d") == "a b c d"

    def test_trims(self):
        assert normalize_whitespace("  hello  ") == "hello"


class TestCleanText:
    def test_removes_boilerplate(self):
        text = "Bitcoin rallies. Subscribe to our newsletter today!"
        cleaned = clean_text(text)
        assert "Subscribe to our newsletter" not in cleaned
        assert "Bitcoin rallies." in cleaned

    def test_html_and_whitespace(self):
        assert clean_text("<div>BTC   is<br/> up</div>") == "BTC is up"


class TestToUtcIso:
    def test_rfc2822(self):
        result = to_utc_iso("Mon, 06 Jan 2025 14:30:00 GMT")
        assert result == "2025-01-06T14:30:00+00:00"

    def test_iso_with_z(self):
        result = to_utc_iso("2025-01-06T14:30:00Z")
        assert result == "2025-01-06T14:30:00+00:00"

    def test_iso_with_offset_converted_to_utc(self):
        result = to_utc_iso("2025-01-06T14:30:00+02:00")
        assert result == "2025-01-06T12:30:00+00:00"

    def test_bare_date(self):
        result = to_utc_iso("2025-01-06")
        assert result.startswith("2025-01-06T00:00:00")

    def test_garbage_returns_none(self):
        assert to_utc_iso("not a date") is None

    def test_empty_returns_none(self):
        assert to_utc_iso("") is None


class TestTitlesSimilar:
    def test_identical(self):
        assert titles_similar("Bitcoin hits $100k", "Bitcoin hits $100k")

    def test_near_duplicate(self):
        assert titles_similar("Bitcoin hits $100,000 milestone", "Bitcoin hits $100,000 milestone!")

    def test_different(self):
        assert not titles_similar("Bitcoin hits $100k", "Ethereum upgrade delayed again")


class TestDeduplicate:
    def test_exact_url_dupes_removed(self):
        records = [
            {"title": "A story", "url": "https://x.com/1"},
            {"title": "Different story entirely", "url": "https://x.com/1"},
        ]
        assert len(deduplicate(records)) == 1

    def test_fuzzy_title_dupes_removed_across_sources(self):
        records = [
            {"title": "Binance lists new token XYZ today", "url": "https://a.com/1"},
            {"title": "Binance lists new token XYZ today!", "url": "https://b.com/2"},
        ]
        assert len(deduplicate(records)) == 1

    def test_distinct_records_kept(self):
        records = [
            {"title": "Bitcoin surges past resistance", "url": "https://a.com/1"},
            {"title": "SEC delays Ethereum ETF decision", "url": "https://b.com/2"},
        ]
        assert len(deduplicate(records)) == 2


class TestCleanRecord:
    def _base(self, **overrides):
        rec = {
            "title": "Valid title",
            "url": "https://x.com/a",
            "published_at": "2025-01-06T14:30:00Z",
            "raw_content": "<p>Some content</p>",
            "source_name": "CoinDesk",
            "source_type": "news",
        }
        rec.update(overrides)
        return rec

    def test_valid_record_cleaned(self):
        result = clean_record(self._base())
        assert result is not None
        assert result["raw_content"] == "Some content"
        assert result["published_at"] == "2025-01-06T14:30:00+00:00"

    def test_missing_title_dropped(self):
        assert clean_record(self._base(title="")) is None

    def test_html_only_title_dropped(self):
        assert clean_record(self._base(title="<br/>")) is None

    def test_bad_timestamp_dropped(self):
        assert clean_record(self._base(published_at="???")) is None


class TestCleanRecordsBatch:
    def test_batch_cleans_validates_and_dedupes(self):
        records = [
            {
                "title": "Bitcoin ETF approved by regulators",
                "url": "https://a.com/1",
                "published_at": "2025-01-06T10:00:00Z",
                "raw_content": "Big news.",
                "source_name": "CoinDesk",
                "source_type": "news",
            },
            {  # duplicate URL
                "title": "Bitcoin ETF approved by regulators",
                "url": "https://a.com/1",
                "published_at": "2025-01-06T10:00:00Z",
                "raw_content": "Big news.",
                "source_name": "CoinDesk",
                "source_type": "news",
            },
            {  # invalid timestamp -> dropped
                "title": "Broken record",
                "url": "https://a.com/2",
                "published_at": "no-date",
                "raw_content": "",
                "source_name": "Decrypt",
                "source_type": "news",
            },
        ]
        result = clean_records(records)
        assert len(result) == 1
        assert result[0]["url"] == "https://a.com/1"
