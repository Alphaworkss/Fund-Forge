"""
test_clean.py — Stage 8: Testing (clean.py)

Run with: pytest test_clean.py
"""

import pandas as pd

from clean import clean


def test_clean_drops_partial_rows():
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 3, "is_partial": True},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-20")


def test_clean_deduplicates_keeping_latest():
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 9, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["commits"] == 9


def test_clean_keeps_zero_values_as_is():
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 0, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["commits"] == 0


def test_clean_handles_mixed_snapshot_and_commits_metrics():
    records = [
        {"repo": "x/y", "date": "2026-07-30", "metric": "snapshot", "stars": 100, "forks": 20, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2
    assert set(df["metric"]) == {"snapshot", "commits"}


def test_clean_different_metrics_on_same_date_are_not_deduplicated_away():
    records = [
        {"repo": "x/y", "date": "2026-07-27", "metric": "snapshot", "stars": 100, "forks": 20, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 5, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2


def test_clean_empty_records_returns_empty_dataframe_with_columns():
    df = clean([])

    assert df.empty
    assert list(df.columns) == ["repo", "date", "metric", "stars", "forks", "commits", "is_partial"]


def test_clean_handles_is_partial_as_int_from_db_read():
    # storage.py's SQLite github_raw table has no native boolean type, so
    # is_partial round-trips as INTEGER 0/1, not Python bool. clean() must
    # not crash on that shape, and must still drop the partial (1) row.
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": 0},
        {"repo": "x/y", "date": "2026-07-27", "metric": "commits", "commits": 3, "is_partial": 1},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-20")
    assert df.iloc[0]["commits"] == 5


def test_clean_handles_is_partial_as_none_treated_as_not_partial():
    # A NULL is_partial (missing/malformed input) should be treated as
    # False (not partial), not crash with TypeError on unary ~.
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": None},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["commits"] == 5


def test_clean_dedup_keeps_finalized_row_when_finalized_appears_before_partial_duplicate():
    # If drop_duplicates(keep="last") ran BEFORE the partial filter, the
    # later (partial) duplicate would win the dedup and then get dropped
    # by the partial filter, silently losing the data point entirely.
    # Partial rows must be dropped first so only real duplicates
    # (finalized vs. finalized) ever reach dedup.
    records = [
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 5, "is_partial": False},
        {"repo": "x/y", "date": "2026-07-20", "metric": "commits", "commits": 3, "is_partial": True},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["commits"] == 5
