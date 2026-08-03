# test_transform.py
"""
test_transform.py — Stage 8: Testing (transform.py)

Run with: pytest test_transform.py
"""

import pandas as pd

from transform import transform


def test_transform_adds_expected_columns():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-30"), "metric": "tx_count", "value": 712078, "is_partial": False},
    ])

    out = transform(df)

    assert set(out.columns) == {"coin", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}


def test_transform_normalizes_within_zero_one_per_series():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp(f"2026-01-0{i}"), "metric": "tx_count", "value": v, "is_partial": False}
        for i, v in zip(range(1, 4), [500000, 600000, 700000])
    ])

    out = transform(df)

    assert out["value_norm"].min() == 0.0
    assert out["value_norm"].max() == 1.0


def test_transform_computes_independent_series_per_metric():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-30"), "metric": "tx_count", "value": 712078, "is_partial": False},
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-30"), "metric": "active_addresses", "value": 497475, "is_partial": False},
    ])

    out = transform(df)

    tx_rows = out[out["metric"] == "tx_count"]
    addr_rows = out[out["metric"] == "active_addresses"]
    assert len(tx_rows) == 1 and tx_rows["value"].iloc[0] == 712078
    assert len(addr_rows) == 1 and addr_rows["value"].iloc[0] == 497475


def test_transform_two_coins_do_not_mix_series():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-01-01"), "metric": "tx_count", "value": 1000000, "is_partial": False},
        {"coin": "ethereum", "date": pd.Timestamp("2026-01-01"), "metric": "tx_count", "value": 10, "is_partial": False},
    ])

    out = transform(df)

    assert (out["value_norm"] == 0.0).all()


def test_transform_date_formatted_as_string():
    df = pd.DataFrame([
        {"coin": "bitcoin", "date": pd.Timestamp("2026-07-27"), "metric": "tx_count", "value": 712078, "is_partial": False},
    ])

    out = transform(df)

    assert out["date"].iloc[0] == "2026-07-27"


def test_transform_pct_change_infinity_becomes_null():
    df = pd.DataFrame([
        {"coin": "bnb", "date": pd.Timestamp(f"2026-01-0{i}"), "metric": "tx_count", "value": v, "is_partial": False}
        for i, v in zip(range(1, 10), [0, 0, 0, 0, 0, 0, 0, 5, 10])
    ])

    out = transform(df)

    # pct_change vs 7 points prior: the row for 2026-01-08 (index 7,
    # value 5) divides by the value from 2026-01-01 (0) -> inf without
    # the fix. Must be null (None/NaN), not inf, matching the GitHub
    # pipeline's Bug #3 lesson.
    row = out[out["date"] == "2026-01-08"]
    assert pd.isna(row["pct_change"].iloc[0])


def test_transform_empty_dataframe_returns_empty_with_all_columns():
    df = pd.DataFrame(columns=["coin", "date", "metric", "value", "is_partial"])

    out = transform(df)

    assert out.empty
    assert set(out.columns) == {"coin", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}
