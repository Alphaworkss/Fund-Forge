import pandas as pd
from cleaning.clean import clean


def test_drops_out_of_range_temperature():
    df = pd.DataFrame({
        "source": ["NOAA"], "location": ["X"],
        "timestamp": ["2026-01-01"], "metric_type": ["temperature_c"],
        "value": [200], "unit": ["C"],
    })
    result = clean(df)
    assert len(result) == 0


def test_keeps_valid_rows():
    df = pd.DataFrame({
        "source": ["NOAA"], "location": ["X"],
        "timestamp": ["2026-01-01"], "metric_type": ["temperature_c"],
        "value": [25], "unit": ["C"],
    })
    result = clean(df)
    assert len(result) == 1


def test_drops_duplicates():
    row = {
        "source": "NOAA", "location": "X", "timestamp": "2026-01-01",
        "metric_type": "temperature_c", "value": 25, "unit": "C",
    }
    df = pd.DataFrame([row, row])
    result = clean(df)
    assert len(result) == 1


def test_alert_rows_pass_through_unfiltered():
    df = pd.DataFrame({
        "source": ["NOAA"], "location": ["X"],
        "timestamp": ["2026-01-01"], "metric_type": ["alert"],
        "value": ["Flood Warning"], "unit": [None],
    })
    result = clean(df)
    assert len(result) == 1


def test_mixed_timestamp_formats_all_survive():
    """
    Regression test: weather sources use plain date strings like '20260115'
    (NASA POWER's raw format) while PMD alerts use full ISO datetimes with
    timezone offsets. Combined in one column, pandas' to_datetime used to
    lock onto whichever format it saw first and silently turn every
    non-matching row into NaT (which dropna then removed) - this is what
    was making the PMD Alerts sheet come out empty. format='mixed' in
    clean() fixes it; this test guards against that regressing.
    """
    df = pd.DataFrame({
        "source": ["NASA_POWER", "NASA_POWER", "PMD", "PMD"],
        "location": ["Lahore", "Lahore", "Widespread rain", "Urban flooding"],
        "timestamp": ["20260115", "20260116", "2026-07-31T07:34:22+00:00", "2026-07-30T11:16:16+00:00"],
        "metric_type": ["temperature_c", "temperature_c", "alert", "alert"],
        "value": [25, 26, "Heavy rain expected", "Flooding likely in Sindh"],
        "unit": ["C", "C", None, None],
    })
    result = clean(df)
    assert len(result) == 4, f"Expected all 4 rows to survive, got {len(result)}"
    assert (result["source"] == "PMD").sum() == 2, "PMD alert rows were dropped"
