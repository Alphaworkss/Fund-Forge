"""
test_pipeline.py — Stage 8: Testing (pipeline.py)

Tests run_once()'s orchestration with collect() mocked — a unit test
shouldn't depend on the live GitHub API. Uses a real temp-file SQLite
database (via pytest's tmp_path fixture), not :memory:, because
run_once() opens its own connection internally via
get_connection(db_path), and :memory: databases are per-connection —
not shared across the separate connection a test needs to pre-seed
data through. export_to_excel is always mocked so tests never write a
real file, and never touch this project's real github_data.xlsx.

Run with: pytest test_pipeline.py
"""

from unittest.mock import patch

import pytest

from storage import get_connection, upsert_raw

import pipeline


def test_run_once_stores_new_records_and_features(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-27", "commits": 5, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    raw_count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    feature_count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    conn.close()

    assert raw_count == 1
    assert feature_count == 1


def test_run_once_computes_features_over_full_history_not_just_new_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    # Pre-seed 6 historical commit records for the same (repo, metric)
    # series, simulating data already sitting in the database from a
    # prior day's collect() run or the one-time backfill.
    conn = get_connection(db_path)
    upsert_raw(
        conn,
        [
            {"repo": "x/y", "metric": "commits", "date": f"2026-06-{d:02d}", "commits": d, "is_partial": False}
            for d in [1, 8, 15, 22, 29]
        ]
        + [{"repo": "x/y", "metric": "commits", "date": "2026-07-06", "commits": 6, "is_partial": False}],
    )
    conn.close()

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-13", "commits": 7, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    feature_count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    rolling_avg = conn.execute(
        "SELECT rolling_avg FROM github_features WHERE date = '2026-07-13'"
    ).fetchone()[0]
    conn.close()

    # 7 total raw records (6 pre-seeded + 1 fresh from collect()) means
    # 7 feature rows — if run_once() only transformed collect()'s fresh
    # output (1 record), this would be 1, not 7.
    assert feature_count == 7
    # A 7-point rolling average that only saw the single newest record
    # would equal that record's own value (7.0). Seeing a different
    # value proves the full read-back history fed the computation, not
    # just today's fresh slice.
    assert rolling_avg != 7.0


def test_run_once_exits_when_collect_returns_no_records(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[]), patch("pipeline.export_to_excel") as mock_export:
        with pytest.raises(SystemExit):
            pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    raw_count = conn.execute("SELECT COUNT(*) FROM github_raw").fetchone()[0]
    feature_count = conn.execute("SELECT COUNT(*) FROM github_features").fetchone()[0]
    conn.close()

    assert raw_count == 0
    assert feature_count == 0
    mock_export.assert_not_called()


def test_run_once_exports_to_excel_after_a_successful_run(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-27", "commits": 5, "is_partial": False},
    ]), patch("pipeline.export_to_excel") as mock_export:
        pipeline.run_once(db_path=db_path)

    mock_export.assert_called_once()


def test_run_once_stores_common_records_for_new_records_only(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-27", "commits": 5, "is_partial": False},
    ]), patch("pipeline.export_to_excel"):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    common_count = conn.execute("SELECT COUNT(*) FROM github_common").fetchone()[0]
    common_id = conn.execute("SELECT id FROM github_common").fetchone()[0]
    conn.close()

    assert common_count == 1
    assert common_id == "github:x/y:2026-07-27:commits"


def test_run_once_skips_common_records_that_fail_validation(tmp_path):
    db_path = str(tmp_path / "test.db")

    with patch("pipeline.collect", return_value=[
        {"repo": "x/y", "metric": "commits", "date": "2026-07-27", "commits": 5, "is_partial": False},
    ]), patch("pipeline.export_to_excel"), patch(
        "pipeline.validate_common_record", return_value=["source is missing"]
    ):
        pipeline.run_once(db_path=db_path)

    conn = get_connection(db_path)
    common_count = conn.execute("SELECT COUNT(*) FROM github_common").fetchone()[0]
    conn.close()

    assert common_count == 0
