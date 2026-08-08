"""
clean.py — Stage 2: Data Cleaning

Takes the raw records from collect.py (or any sources/ adapter's
backfill()/collect()) and:
  - drops rows flagged is_partial=True — a no-op on this pipeline's
    current 3 coins (Bitcoin/Ethereum/BNB Chain never publish an
    in-progress day, verified live — see design.md), kept for schema
    consistency with the sibling pipelines and any future coin that
    does have partial data
  - drops duplicate (coin, date, metric) triples, keeping the latest

No zero-fill/forward-fill step: a 0 (e.g. a genuinely quiet day for a
low-activity metric) is a real data point, not evidence of a reporting
gap — same reasoning as the GitHub pipeline's commit counts.

No reshaping happens here — collect.py already emits one row per
(coin, date, metric) with a single value column, so unlike the GitHub
pipeline's clean.py/transform.py split, there's no melt step needed
anywhere in this pipeline.
"""

import pandas as pd

RAW_COLUMNS = ["coin", "date", "metric", "value", "is_partial"]


def clean(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=RAW_COLUMNS)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    df = df[~df["is_partial"]].copy()
    df = df.drop_duplicates(subset=["coin", "date", "metric"], keep="last")

    return df.sort_values(["coin", "metric", "date"])[RAW_COLUMNS].reset_index(drop=True)
