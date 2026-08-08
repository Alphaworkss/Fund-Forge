"""
test_pipeline.py — Stage 8: Testing

Unit tests for the clean/transform/storage stages. Deliberately does NOT
call collect() over the network — a unit test shouldn't depend on a live
external API. Run with: pytest test_pipeline.py
"""

import json
import pandas as pd
from unittest.mock import patch

from clean import clean
from common_schema import enrich
from transform import transform
from storage import get_connection, upsert_raw, upsert_features, upsert_common
import pipeline


SAMPLE_RECORDS = [
    {"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False},
    {"keyword": "PSX", "date": "2026-07-02", "interest": 0, "is_partial": False},   # gap, should ffill
    {"keyword": "PSX", "date": "2026-07-03", "interest": 45, "is_partial": False},
    {"keyword": "PSX", "date": "2026-07-04", "interest": 90, "is_partial": True},   # dropped
    {"keyword": "PSX", "date": "2026-07-01", "interest": 41, "is_partial": False},  # dup, latest wins
]


def test_clean_drops_partial_rows():
    df = clean(SAMPLE_RECORDS)
    assert not df["is_partial"].any()
    assert df["date"].max() < pd.Timestamp("2026-07-04")


def test_clean_deduplicates_keeping_latest():
    df = clean(SAMPLE_RECORDS)
    row = df[(df["keyword"] == "PSX") & (df["date"] == pd.Timestamp("2026-07-01"))]
    assert len(row) == 1
    assert row.iloc[0]["interest"] == 41


def test_clean_fills_zero_gaps():
    df = clean(SAMPLE_RECORDS)
    row = df[(df["keyword"] == "PSX") & (df["date"] == pd.Timestamp("2026-07-02"))]
    assert row.iloc[0]["interest"] == 41  # forward-filled from the prior day


def test_transform_adds_expected_columns():
    df = clean(SAMPLE_RECORDS)
    out = transform(df)
    for col in ["interest_norm", "rolling_avg_7d", "pct_change_7d", "zscore_30d"]:
        assert col in out.columns


def test_transform_normalizes_within_zero_one():
    df = clean(SAMPLE_RECORDS)
    out = transform(df)
    assert out["interest_norm"].between(0, 1).all()


def test_storage_upsert_is_idempotent():
    conn = get_connection(":memory:")
    records = [{"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False}]
    upsert_raw(conn, records)
    upsert_raw(conn, records)  # run twice — should update, not duplicate
    count = conn.execute("SELECT COUNT(*) FROM google_trends_raw").fetchone()[0]
    assert count == 1
    conn.close()


def test_feature_storage_roundtrip():
    conn = get_connection(":memory:")
    df = clean(SAMPLE_RECORDS)
    featured = transform(df)
    upsert_features(conn, featured.to_dict(orient="records"))
    count = conn.execute("SELECT COUNT(*) FROM google_trends_features").fetchone()[0]
    assert count == len(featured)
    conn.close()


def test_common_storage_upsert_is_idempotent():
    conn = get_connection(":memory:")
    common = enrich({"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False})

    upsert_common(conn, [common])
    upsert_common(conn, [common])

    count = conn.execute("SELECT COUNT(*) FROM google_trends_common").fetchone()[0]
    assert count == 1
    conn.close()


def test_common_storage_roundtrips_json_fields():
    conn = get_connection(":memory:")
    common = enrich({
        "keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False,
        "raw_response": {"PSX": 40},
    })

    upsert_common(conn, [common])

    row = conn.execute(
        "SELECT keywords, related_assets, raw_response FROM google_trends_common"
    ).fetchone()
    assert json.loads(row[0]) == ["PSX"]
    assert json.loads(row[1]) == ["PSX", "KSE100"]
    assert json.loads(row[2]) == {"PSX": 40}
    conn.close()


def test_common_storage_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    record = {"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False}
    first = enrich(record)
    upsert_common(conn, [first])

    second = enrich(dict(record, raw_response={"PSX": 41}))
    upsert_common(conn, [second])

    row = conn.execute("SELECT raw_response FROM google_trends_common").fetchone()
    assert json.loads(row[0]) == {"PSX": 41}
    conn.close()


def test_run_once_stores_common_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    common_count = conn.execute("SELECT COUNT(*) FROM google_trends_common").fetchone()[0]
    common_id = conn.execute("SELECT id FROM google_trends_common").fetchone()[0]
    conn.close()

    assert common_count == 1
    assert common_id == "google_trends:PSX:2026-07-01"


def test_run_once_skips_common_records_that_fail_validation(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"keyword": "PSX", "date": "2026-07-01", "interest": 40, "is_partial": False},
    ]), patch("pipeline.export_to_excel"), patch(
        "pipeline.validate_common_record", return_value=["source is missing"]
    ):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    common_count = conn.execute("SELECT COUNT(*) FROM google_trends_common").fetchone()[0]
    conn.close()

    assert common_count == 0
