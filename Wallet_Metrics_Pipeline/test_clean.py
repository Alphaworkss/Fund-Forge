"""
test_clean.py — Stage 8: Testing (clean.py)

Run with: pytest test_clean.py
"""

import pandas as pd

from clean import clean


def test_clean_drops_partial_rows():
    records = [
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 700000, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-27", "metric": "tx_count", "value": 650000, "is_partial": True},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["date"] == pd.Timestamp("2026-07-20")


def test_clean_deduplicates_keeping_latest():
    records = [
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 700000, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 712078, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["value"] == 712078


def test_clean_drops_partial_row_even_when_it_is_the_latest_duplicate():
    records = [
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-20", "metric": "tx_count", "value": 650000, "is_partial": True},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["value"] == 712078


def test_clean_keeps_zero_values_as_is():
    records = [
        {"coin": "bnb", "date": "2020-08-29", "metric": "tx_count", "value": 0, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 1
    assert df.iloc[0]["value"] == 0


def test_clean_handles_multiple_metrics_for_same_coin_and_date():
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "active_addresses", "value": 497475, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2
    assert set(df["metric"]) == {"tx_count", "active_addresses"}


def test_clean_different_metrics_on_same_date_are_not_deduplicated_away():
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_volume", "value": 92620.9, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2


def test_clean_different_coins_on_same_date_and_metric_are_not_deduplicated_away():
    records = [
        {"coin": "bitcoin", "date": "2026-07-30", "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "ethereum", "date": "2026-07-30", "metric": "tx_count", "value": 1766208, "is_partial": False},
    ]

    df = clean(records)

    assert len(df) == 2


def test_clean_empty_records_returns_empty_dataframe_with_columns():
    df = clean([])

    assert df.empty
    assert list(df.columns) == ["coin", "date", "metric", "value", "is_partial"]
