import os
import pandas as pd
from cleaning.clean import clean
from normalization.normalize import normalize
from storage.writer import write_parquet


def test_end_to_end_fixture(tmp_path):
    raw = pd.DataFrame({
        "location": ["Islamabad", "Islamabad"],
        "timestamp": ["2026-01-01", "2026-01-02"],
        "metric_type": ["temperature_c", "rainfall_mm"],
        "value": [30, 5],
        "unit": ["C", "mm"],
    })

    normalized = normalize(raw, source="NASA_POWER")
    cleaned = clean(normalized)

    out_path = str(tmp_path / "weather_records.parquet")
    write_parquet(cleaned, path=out_path)

    assert os.path.exists(out_path)
    result = pd.read_parquet(out_path)
    assert len(result) == 2
    assert set(result.columns) >= {"location", "timestamp", "metric_type", "value", "unit"}
