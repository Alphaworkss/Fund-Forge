"""
Integration test: run the full pipeline against a small sample input list
(no live network calls) and assert both the DB and CSV end up populated
correctly.
"""

import csv

import pytest

import config
from config import SCHEMA_FIELDS
from pipeline import run_pipeline
from storage.db import get_all_records, get_engine

SAMPLE_RAW_RECORDS = [
    {
        "title": "Binance will list Solana perpetual futures",
        "url": "https://binance.com/announce/100",
        "published_at": "Mon, 06 Jan 2025 10:00:00 GMT",
        "raw_content": "Binance announces a new SOL trading pair launching Friday.",
        "source_name": "Binance",
        "source_type": "exchange_announcement",
    },
    {
        "title": "SEC files lawsuit against major crypto exchange",
        "url": "https://coindesk.com/policy/lawsuit",
        "published_at": "2025-01-06T11:00:00Z",
        "raw_content": "<p>The SEC announced legal action targeting Bitcoin services.</p>",
        "source_name": "CoinDesk",
        "source_type": "news",
    },
    {
        # duplicate URL of the first record -> removed during cleaning
        "title": "Binance will list Solana perpetual futures",
        "url": "https://binance.com/announce/100",
        "published_at": "Mon, 06 Jan 2025 10:00:00 GMT",
        "raw_content": "Duplicate entry.",
        "source_name": "Binance",
        "source_type": "exchange_announcement",
    },
    {
        # invalid timestamp -> dropped during cleaning
        "title": "Broken record with no valid date",
        "url": "https://decrypt.co/broken",
        "published_at": "not-a-date",
        "raw_content": "irrelevant",
        "source_name": "Decrypt",
        "source_type": "news",
    },
]


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Point DB and CSV paths at a temp directory for the test run."""
    db_path = tmp_path / "pipeline.db"
    csv_path = tmp_path / "pipeline_output.csv"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(config, "CSV_PATH", csv_path)
    # storage modules imported these names directly, patch there too
    import storage.csv_export as csv_export_mod
    import storage.db as db_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(csv_export_mod, "CSV_PATH", csv_path)
    return db_path, csv_path


def test_full_pipeline_populates_db_and_csv(isolated_storage):
    db_path, csv_path = isolated_storage

    summary = run_pipeline(raw_records=list(SAMPLE_RAW_RECORDS))

    # Summary counts: 4 collected, 2 survive cleaning, 2 stored
    assert summary["collected"] == 4
    assert summary["cleaned"] == 2
    assert summary["stored_new"] == 2
    assert summary["errors"] == 0

    # --- DB assertions ---
    engine = get_engine(db_path)
    rows = get_all_records(engine)
    assert len(rows) == 2
    by_source = {r["source_name"]: r for r in rows}

    binance = by_source["Binance"]
    assert binance["source_type"] == "exchange_announcement"
    assert binance["event_category"] == "Exchange Listing"
    assert "SOL" in binance["affected_coins"]
    assert binance["importance_score"] >= 0.6
    assert binance["published_at"] == "2025-01-06T10:00:00+00:00"

    coindesk = by_source["CoinDesk"]
    assert coindesk["event_category"] == "Regulatory Announcement"
    assert "BTC" in coindesk["affected_coins"]
    assert "<p>" not in coindesk["content"]  # HTML stripped

    for row in rows:
        assert set(row.keys()) == set(SCHEMA_FIELDS)

    # --- CSV assertions ---
    assert csv_path.exists()
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == SCHEMA_FIELDS
        csv_rows = list(reader)
    assert len(csv_rows) == 2
    assert {r["source_name"] for r in csv_rows} == {"Binance", "CoinDesk"}


def test_rerun_skips_duplicates(isolated_storage):
    db_path, csv_path = isolated_storage

    first = run_pipeline(raw_records=list(SAMPLE_RAW_RECORDS))
    second = run_pipeline(raw_records=list(SAMPLE_RAW_RECORDS))

    assert first["stored_new"] == 2
    assert second["stored_new"] == 0  # all duplicates on second pass

    engine = get_engine(db_path)
    assert len(get_all_records(engine)) == 2
