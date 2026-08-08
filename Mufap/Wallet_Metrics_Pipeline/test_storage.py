"""
test_storage.py — Stage 8: Testing (storage.py)

Run with: pytest test_storage.py
"""

import json
import pandas as pd

from storage import get_connection, upsert_raw, upsert_features, get_raw_records, upsert_common
from common_schema import enrich


def test_upsert_raw_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False}
    ]

    upsert_raw(conn, records)
    upsert_raw(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_raw_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_raw(conn, [{"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 700000, "is_partial": True}])
    upsert_raw(conn, [{"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False}])

    row = conn.execute("SELECT value, is_partial FROM wallet_metrics_raw").fetchone()

    assert row == (712078, 0)
    conn.close()


def test_upsert_raw_stores_multiple_metrics_and_coins_together():
    conn = get_connection(":memory:")

    upsert_raw(
        conn,
        [
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
            {"coin": "ethereum", "date": "2026-07-30", "metric": "active_addresses", "value": 497475, "is_partial": False},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_raw").fetchone()[0]
    assert count == 2
    conn.close()


def test_features_table_exists_but_starts_empty():
    conn = get_connection(":memory:")

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]

    assert count == 0
    conn.close()


def test_upsert_features_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
         "value_norm": 0.5, "rolling_avg": 700000.0, "pct_change": 0.1, "zscore": 0.2},
    ]

    upsert_features(conn, records)
    upsert_features(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_features_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_features(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
         "value_norm": 0.5, "rolling_avg": 700000.0, "pct_change": 0.1, "zscore": 0.2},
    ])
    upsert_features(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 720000,
         "value_norm": 0.9, "rolling_avg": 710000.0, "pct_change": 0.2, "zscore": 0.5},
    ])

    row = conn.execute("SELECT value, value_norm FROM wallet_metrics_features").fetchone()

    assert row == (720000, 0.9)
    conn.close()


def test_upsert_features_stores_multiple_metrics_for_same_coin_date():
    conn = get_connection(":memory:")

    upsert_features(
        conn,
        [
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
             "value_norm": 1.0, "rolling_avg": 700000.0, "pct_change": None, "zscore": None},
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses", "value": 497475,
             "value_norm": 1.0, "rolling_avg": 480000.0, "pct_change": None, "zscore": None},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_features").fetchone()[0]
    assert count == 2
    conn.close()


def test_upsert_features_handles_null_pct_change_and_zscore():
    conn = get_connection(":memory:")

    upsert_features(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
         "value_norm": 1.0, "rolling_avg": 700000.0, "pct_change": None, "zscore": None},
    ])

    row = conn.execute("SELECT pct_change, zscore FROM wallet_metrics_features").fetchone()

    assert row == (None, None)
    conn.close()


def test_get_raw_records_returns_all_rows():
    conn = get_connection(":memory:")
    upsert_raw(
        conn,
        [
            {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
            {"coin": "ethereum", "date": "2026-07-30", "metric": "active_addresses", "value": 497475, "is_partial": False},
        ],
    )

    records = get_raw_records(conn)

    assert len(records) == 2
    conn.close()


def test_get_raw_records_returns_expected_columns():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
    ])

    records = get_raw_records(conn)

    assert set(records[0].keys()) == {"coin", "date", "metric", "value", "is_partial"}
    conn.close()


def test_get_raw_records_preserves_is_partial_as_stored_int():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": True},
    ])

    records = get_raw_records(conn)

    # get_raw_records() coerces SQLite's stored int (0/1) back to a real
    # Python bool — this is load-bearing: clean.py's "~df['is_partial']"
    # does integer bitwise-NOT (not boolean negation) on an uncoerced
    # int64 column and raises KeyError downstream without it.
    assert records[0]["is_partial"] is True
    conn.close()


def test_get_raw_records_empty_table_returns_empty_list():
    conn = get_connection(":memory:")

    records = get_raw_records(conn)

    assert records == []
    conn.close()


def test_partial_record_survives_storage_roundtrip_and_is_dropped_by_clean():
    from clean import clean

    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-31", "metric": "tx_count", "value": 999999, "is_partial": True},
    ])

    records = get_raw_records(conn)
    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-30")
    conn.close()


def test_common_storage_upsert_is_idempotent():
    conn = get_connection(":memory:")
    common = enrich({"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False})

    upsert_common(conn, [common])
    upsert_common(conn, [common])

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_common").fetchone()[0]
    assert count == 1
    conn.close()


def test_common_storage_roundtrips_json_fields():
    conn = get_connection(":memory:")
    common = enrich({
        "coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078,
        "is_partial": False, "raw_response": {"x": 1785369600, "y": 712078},
    })

    upsert_common(conn, [common])

    row = conn.execute(
        "SELECT keywords, related_assets, raw_response FROM wallet_metrics_common"
    ).fetchone()
    assert json.loads(row[0]) == ["bitcoin", "tx_count"]
    assert json.loads(row[1]) == ["Bitcoin"]
    assert json.loads(row[2]) == {"x": 1785369600, "y": 712078}
    conn.close()


def test_common_storage_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    record = {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False}
    upsert_common(conn, [enrich(record)])

    updated = dict(record, value=800000)
    upsert_common(conn, [enrich(updated)])

    count = conn.execute("SELECT COUNT(*) FROM wallet_metrics_common").fetchone()[0]
    assert count == 1
    conn.close()
