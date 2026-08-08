"""
Cleaning stage: drop invalid rows, remove duplicates, catch out-of-range
values, standardize timestamps to UTC. Runs after ingestion, before
normalization.
"""
import pandas as pd
from config.settings import VALID_RANGES


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    df = df.dropna(subset=["timestamp", "value"])
    df = df.drop_duplicates(subset=["source", "location", "timestamp", "metric_type"])

    # Only apply numeric range checks to metric types we have ranges for.
    # Alert rows (metric_type == "alert") have text values and are skipped.
    for metric, (lo, hi) in VALID_RANGES.items():
        mask = df["metric_type"] == metric
        numeric_values = pd.to_numeric(df.loc[mask, "value"], errors="coerce")
        out_of_range = mask & (~numeric_values.between(lo, hi)).reindex(df.index, fill_value=False)
        df = df[~out_of_range]

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce", format="mixed")
    df = df.dropna(subset=["timestamp"])

    print(f"Cleaning: {before} -> {len(df)} rows")
    return df
