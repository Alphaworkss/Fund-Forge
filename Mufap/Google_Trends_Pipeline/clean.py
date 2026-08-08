"""
clean.py — Stage 2: Data Cleaning

Takes the raw records from collect.py and:
  - drops rows flagged isPartial=True — Google Trends marks the most
    recent day/week as still-accumulating, so including it would let an
    artificially low "not finished yet" value pollute rolling stats
  - drops duplicate (keyword, date) pairs, keeping the latest
  - forward-fills isolated zero values within a keyword's series — Google
    Trends sometimes reports 0 for a genuine data gap rather than true
    zero interest; a single 0 surrounded by non-zero values is treated as
    a gap and filled from the prior day
"""

import pandas as pd


def clean(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=["keyword", "date", "interest", "is_partial"])

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    df = df.drop_duplicates(subset=["keyword", "date"], keep="last")
    df = df[~df["is_partial"]].copy()

    df = df.sort_values(["keyword", "date"])
    df["interest"] = df.groupby("keyword")["interest"].transform(
        lambda s: s.mask(s == 0).ffill().fillna(0)
    )

    return df.reset_index(drop=True)
