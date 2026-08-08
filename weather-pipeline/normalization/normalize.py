"""
Normalization stage: convert every source's units and column layout into
one unified schema (see docs/SCHEMA.md), so downstream code never has to
know which source a row came from.
"""
import pandas as pd

REQUIRED_COLUMNS = ["source", "location", "timestamp", "metric_type", "value", "unit"]


def fahrenheit_to_celsius(f):
    return (f - 32) * 5 / 9


def inches_to_mm(i):
    return i * 25.4


def normalize(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.copy()
    df["source"] = source

    if "unit" in df.columns and df["unit"].eq("F").any():
        mask = df["unit"] == "F"
        df.loc[mask, "value"] = df.loc[mask, "value"].apply(fahrenheit_to_celsius)
        df.loc[mask, "unit"] = "C"

    if "unit" in df.columns and df["unit"].eq("in").any():
        mask = df["unit"] == "in"
        df.loc[mask, "value"] = df.loc[mask, "value"].apply(inches_to_mm)
        df.loc[mask, "unit"] = "mm"

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[REQUIRED_COLUMNS]
