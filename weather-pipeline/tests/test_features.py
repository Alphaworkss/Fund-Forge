import pandas as pd
from features.extract_features import flag_heatwave, flag_flood_risk, flag_drought


def _temp_df(values_by_day, location="X"):
    rows = [
        {"location": location, "timestamp": pd.Timestamp(f"2026-01-{day:02d}", tz="UTC"),
         "metric_type": "temperature_c", "value": v}
        for day, v in values_by_day.items()
    ]
    return pd.DataFrame(rows)


def test_flags_heatwave_on_three_consecutive_hot_days():
    df = _temp_df({1: 42, 2: 41, 3: 43, 4: 20})
    result = flag_heatwave(df, threshold_c=40, consecutive_days=3)
    hot_flags = result.set_index("date")["heatwave"]
    assert hot_flags[pd.Timestamp("2026-01-03").date()] == True  # noqa: E712
    assert hot_flags[pd.Timestamp("2026-01-04").date()] == False  # noqa: E712


def test_no_heatwave_if_not_enough_consecutive_days():
    df = _temp_df({1: 42, 2: 20, 3: 42})
    result = flag_heatwave(df, threshold_c=40, consecutive_days=3)
    assert not result["heatwave"].any()


def test_flags_flood_risk_over_threshold():
    df = pd.DataFrame({
        "location": ["X"], "timestamp": [pd.Timestamp("2026-01-01", tz="UTC")],
        "metric_type": ["rainfall_mm"], "value": [150],
    })
    result = flag_flood_risk(df, rainfall_mm_24h=100)
    assert result["flood_risk"].iloc[0] == True  # noqa: E712


def test_flags_drought_on_low_30d_rainfall():
    df = pd.DataFrame({
        "location": ["X"], "timestamp": [pd.Timestamp("2026-01-01", tz="UTC")],
        "metric_type": ["rainfall_mm"], "value": [5],
    })
    result = flag_drought(df, low_rainfall_mm_30d=15)
    assert result["drought"].iloc[0] == True  # noqa: E712
