"""Tests for backfill.py: sitemap parsing, checkpoint state, batch
processing through the existing pipeline modules, and report logic."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from backfill import (
    BatchProcessor,
    PoliteFetcher,
    _extract_title_from_text,
    _lastmod_dt,
    _make_report,
    _source_state,
    load_state,
    parse_sitemap_xml,
    save_state,
)
from storage.db import count_records, get_engine


SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/post-sitemap1.xml</loc>
    <lastmod>2026-07-01T00:00:00+00:00</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://example.com/post-sitemap2.xml</loc>
  </sitemap>
</sitemapindex>
"""

URLSET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/news/article-one</loc>
    <lastmod>2026-06-15T12:00:00Z</lastmod>
  </url>
  <url>
    <loc>https://example.com/news/article-two</loc>
  </url>
</urlset>
"""


class TestParseSitemapXml:
    def test_parses_sitemap_index(self):
        sitemaps, urls = parse_sitemap_xml(SITEMAP_INDEX_XML)
        assert len(sitemaps) == 2
        assert urls == []
        assert sitemaps[0]["loc"] == "https://example.com/post-sitemap1.xml"
        assert sitemaps[0]["lastmod"] == "2026-07-01T00:00:00+00:00"
        assert sitemaps[1]["lastmod"] is None

    def test_parses_urlset(self):
        sitemaps, urls = parse_sitemap_xml(URLSET_XML)
        assert sitemaps == []
        assert len(urls) == 2
        assert urls[0]["loc"] == "https://example.com/news/article-one"
        assert urls[0]["lastmod"] == "2026-06-15T12:00:00Z"
        assert urls[1]["lastmod"] is None

    def test_invalid_xml_returns_empty(self):
        assert parse_sitemap_xml("<html>not a sitemap</html>") == ([], [])
        assert parse_sitemap_xml("total garbage {") == ([], [])

    def test_lastmod_dt(self):
        entry = {"loc": "x", "lastmod": "2026-06-15T12:00:00Z"}
        dt = _lastmod_dt(entry)
        assert dt is not None and dt.year == 2026 and dt.month == 6
        assert _lastmod_dt({"loc": "x", "lastmod": None}) is None


class TestCheckpointState:
    def test_load_missing_state(self, tmp_path):
        state = load_state(tmp_path / "nope.json")
        assert state == {"sources": {}}

    def test_save_and_reload_roundtrip(self, tmp_path):
        path = tmp_path / "state.json"
        state = {"sources": {"CoinDesk": {"completed_sitemaps": ["a.xml"],
                                          "last_completed_page": 0,
                                          "oldest_date_reached": "2025-01-01T00:00:00+00:00",
                                          "done": False}}}
        save_state(state, path)
        assert load_state(path) == state

    def test_corrupt_state_starts_fresh(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text("{corrupt json")
        assert load_state(path) == {"sources": {}}

    def test_source_state_initializes_defaults(self):
        state = {"sources": {}}
        src = _source_state(state, "Kraken")
        assert src["last_completed_page"] == 0
        assert src["done"] is False
        # Same object returned on second call (mutations persist).
        src["last_completed_page"] = 5
        assert _source_state(state, "Kraken")["last_completed_page"] == 5


class TestBatchProcessor:
    _TITLES = {
        0: "Bitcoin surges past major milestone amid record ETF inflows",
        1: "Ethereum developers announce next protocol upgrade timeline",
        2: "Solana network activity climbs as DeFi volumes accelerate",
        99: "Kraken lists new asset for spot trading in Europe today",
    }

    def _raw(self, i):
        return {
            "title": self._TITLES[i],
            "url": f"https://example.com/article-{i}",
            "published_at": "2026-06-01T00:00:00+00:00",
            "raw_content": f"Bitcoin content body {i} " * 20,
            "source_name": "CoinDesk",
            "source_type": "news",
        }

    def test_flushes_at_batch_size_and_stores(self, tmp_path):
        engine = get_engine(tmp_path / "t.db")
        proc = BatchProcessor(engine, batch_size=3)
        for i in range(3):
            proc.add(self._raw(i))
        # auto-flush at batch_size
        assert count_records(engine) == 3
        assert proc.stored == 3
        proc.add(self._raw(99))
        proc.flush()
        assert count_records(engine) == 4

    def test_duplicates_not_double_stored(self, tmp_path):
        engine = get_engine(tmp_path / "t.db")
        proc = BatchProcessor(engine, batch_size=100)
        proc.add(self._raw(1))
        proc.flush()
        proc.add(self._raw(1))
        proc.flush()
        assert count_records(engine) == 1
        assert proc.stored == 1


class TestReport:
    def _proc(self, tmp_path):
        return BatchProcessor(get_engine(tmp_path / "t.db"))

    def test_target_reached(self, tmp_path):
        cutoff = datetime.now(timezone.utc) - timedelta(days=720)
        oldest = (cutoff + timedelta(days=10)).isoformat()
        rep = _make_report("X", self._proc(tmp_path), oldest, cutoff, [], False)
        assert rep["target_reached"] is True
        assert rep["history_exhausted_before_target"] is False

    def test_history_exhausted(self, tmp_path):
        cutoff = datetime.now(timezone.utc) - timedelta(days=720)
        oldest = (cutoff + timedelta(days=300)).isoformat()
        rep = _make_report("X", self._proc(tmp_path), oldest, cutoff, [], True)
        assert rep["target_reached"] is False
        assert rep["history_exhausted_before_target"] is True

    def test_no_data(self, tmp_path):
        cutoff = datetime.now(timezone.utc) - timedelta(days=720)
        rep = _make_report("X", self._proc(tmp_path), None, cutoff, ["note"], True)
        assert rep["earliest_date_reached"] is None
        assert rep["target_reached"] is False
        assert rep["notes"] == ["note"]

    def test_report_is_json_serializable(self, tmp_path):
        cutoff = datetime.now(timezone.utc) - timedelta(days=720)
        rep = _make_report("X", self._proc(tmp_path), None, cutoff, [], False)
        json.dumps(rep)


class TestHelpers:
    def test_extract_title_from_text(self):
        text = "Bitcoin ETF inflows hit record high\nBody paragraph follows here."
        assert _extract_title_from_text(text) == "Bitcoin ETF inflows hit record high"

    def test_extract_title_rejects_too_short_or_long(self):
        assert _extract_title_from_text("Short\nbody") is None
        assert _extract_title_from_text(("x" * 300) + "\nbody") is None

    def test_polite_fetcher_gives_up_on_404(self, monkeypatch):
        fetcher = PoliteFetcher(delay=0)

        calls = []

        class FakeResp:
            status_code = 404
            text = ""

        def fake_get(url, timeout=None):
            calls.append(url)
            return FakeResp()

        monkeypatch.setattr(fetcher._session, "get", fake_get)
        assert fetcher.get("https://example.com/missing") is None
        assert len(calls) == 1  # 404 must NOT be retried
