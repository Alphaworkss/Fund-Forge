import pandas as pd
from normalization.normalize import normalize, fahrenheit_to_celsius, inches_to_mm


def test_fahrenheit_to_celsius():
    assert round(fahrenheit_to_celsius(32), 1) == 0.0
    assert round(fahrenheit_to_celsius(212), 1) == 100.0


def test_inches_to_mm():
    assert round(inches_to_mm(1), 1) == 25.4


def test_normalize_converts_fahrenheit_rows():
    df = pd.DataFrame({
        "location": ["X"], "timestamp": ["2026-01-01"],
        "metric_type": ["temperature_c"], "value": [32], "unit": ["F"],
    })
    result = normalize(df, source="NOAA")
    assert result.iloc[0]["unit"] == "C"
    assert round(result.iloc[0]["value"], 1) == 0.0
    assert result.iloc[0]["source"] == "NOAA"


def test_normalize_output_has_required_columns():
    df = pd.DataFrame({
        "location": ["X"], "timestamp": ["2026-01-01"],
        "metric_type": ["rainfall_mm"], "value": [5], "unit": ["mm"],
    })
    result = normalize(df, source="NASA_POWER")
    assert list(result.columns) == ["source", "location", "timestamp", "metric_type", "value", "unit"]
