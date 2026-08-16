"""
test_storage.py — Stage 8: Testing (storage.py)

Run with: pytest test_storage.py
"""

import json

from common_schema import enrich
from storage import get_connection, upsert_raw, upsert_features, upsert_common, get_raw_records


def test_upsert_raw_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False}
    ]

    upsert_raw(conn, records)
    upsert_raw(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_raw_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_raw(conn, [{"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": True}])
    upsert_raw(conn, [{"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 9, "is_partial": False}])

    row = conn.execute("SELECT commits, is_partial FROM github_raw").fetchone()

    assert row == (9, 0)
    conn.close()


def test_upsert_raw_stores_snapshot_and_commit_rows_together():
    conn = get_connection(":memory:")

    upsert_raw(
        conn,
        [
            {"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20},
            {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    assert count == 2
    conn.close()


def test_features_table_exists_but_starts_empty():
    conn = get_connection(":memory:")

    count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]

    assert count == 0
    conn.close()


def test_upsert_features_is_idempotent():
    conn = get_connection(":memory:")
    records = [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "value": 5,
         "value_norm": 0.5, "rolling_avg": 5.0, "pct_change": 0.1, "zscore": 0.2},
    ]

    upsert_features(conn, records)
    upsert_features(conn, records)

    count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    assert count == 1
    conn.close()


def test_upsert_features_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    upsert_features(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "value": 5,
         "value_norm": 0.5, "rolling_avg": 5.0, "pct_change": 0.1, "zscore": 0.2},
    ])
    upsert_features(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "value": 9,
         "value_norm": 0.9, "rolling_avg": 7.0, "pct_change": 0.2, "zscore": 0.5},
    ])

    row = conn.execute("SELECT value, value_norm FROM github_features").fetchone()

    assert row == (9, 0.9)
    conn.close()


def test_upsert_features_stores_multiple_metrics_for_same_repo_date():
    conn = get_connection(":memory:")

    upsert_features(
        conn,
        [
            {"repo": "x/y", "date": "2026-07-30", "metric": "stars", "value": 100,
             "value_norm": 1.0, "rolling_avg": 100.0, "pct_change": None, "zscore": None},
            {"repo": "x/y", "date": "2026-07-30", "metric": "forks", "value": 20,
             "value_norm": 1.0, "rolling_avg": 20.0, "pct_change": None, "zscore": None},
        ],
    )

    count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    assert count == 2
    conn.close()


def test_upsert_features_handles_null_pct_change_and_zscore():
    conn = get_connection(":memory:")

    upsert_features(conn, [
        {"repo": "x/y", "date": "2026-07-30", "metric": "stars", "value": 100,
         "value_norm": 1.0, "rolling_avg": 100.0, "pct_change": None, "zscore": None},
    ])

    row = conn.execute("SELECT pct_change, zscore FROM github_features").fetchone()

    assert row == (None, None)
    conn.close()


def test_get_raw_records_returns_all_rows():
    conn = get_connection(":memory:")
    upsert_raw(
        conn,
        [
            {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
            {"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20, "is_partial": False},
        ],
    )

    records = get_raw_records(conn)

    assert len(records) == 2
    conn.close()


def test_get_raw_records_returns_expected_columns():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
    ])

    records = get_raw_records(conn)

    assert set(records[0].keys()) == {"repo", "date", "metric", "stars", "forks", "commits", "is_partial"}
    conn.close()


def test_get_raw_records_preserves_is_partial_as_stored_int():
    conn = get_connection(":memory:")
    upsert_raw(conn, [
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": True},
    ])

    records = get_raw_records(conn)

    # SQLite has no native boolean — upsert_raw stores int(True) == 1.
    # get_raw_records deliberately does NOT coerce this; clean.py's
    # existing is_partial coercion (added specifically for this
    # database-read-back path) is what handles it downstream.
    assert records[0]["is_partial"] == 1
    conn.close()


def test_get_raw_records_empty_table_returns_empty_list():
    conn = get_connection(":memory:")

    records = get_raw_records(conn)

    assert records == []
    conn.close()


def test_common_storage_upsert_is_idempotent():
    conn = get_connection(":memory:")
    common = enrich({"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False})

    upsert_common(conn, [common])
    upsert_common(conn, [common])

    count = conn.execute("SELECT COUNT(*) FROM github_common").fetchone()[0]
    assert count == 1
    conn.close()


def test_common_storage_roundtrips_json_fields():
    conn = get_connection(":memory:")
    common = enrich({
        "repo": "bitcoin/bitcoin", "date": "2026-07-30", "metric": "snapshot",
        "stars": 100, "forks": 20, "is_partial": False,
        "raw_response": {"stargazers_count": 100, "forks_count": 20},
    })

    upsert_common(conn, [common])

    row = conn.execute(
        "SELECT keywords, related_assets, raw_response FROM github_common"
    ).fetchone()
    assert json.loads(row[0]) == ["bitcoin/bitcoin", "snapshot"]
    assert json.loads(row[1]) == ["Bitcoin"]
    assert json.loads(row[2]) == {"stargazers_count": 100, "forks_count": 20}
    conn.close()


def test_common_storage_updates_existing_row_on_conflict():
    conn = get_connection(":memory:")
    record = {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": True}
    upsert_common(conn, [enrich(record)])

    updated = dict(record, commits=9, is_partial=False)
    upsert_common(conn, [enrich(updated)])

    count = conn.execute("SELECT COUNT(*) FROM github_common").fetchone()[0]
    assert count == 1
    conn.close()
