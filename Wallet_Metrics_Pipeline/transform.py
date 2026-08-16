# transform.py
"""
transform.py — Stage 3: Normalization, Stage 4: Feature Extraction

Unlike the GitHub pipeline's transform.py, there's no melt step here:
collect.py already emits one row per (coin, date, metric) with a
single value column (see design.md), so this module goes straight to
feature computation, grouped by (coin, metric) — same 2-key grouping
as GitHub's (repo, metric).

Same math as both sibling pipelines: min-max value_norm within that
series' own history; rolling_avg (7 data points, min_periods=1);
pct_change (vs. 7 data points prior, inf treated as unknown/blank per
the GitHub pipeline's Bug #3 lesson — dividing by a real zero, e.g. a
quiet day, is a valid data point, not an error, but the resulting
infinity must not leak into storage/exports); zscore (30-data-point
trailing mean/std, min_periods=5).
"""

import pandas as pd

FEATURE_COLUMNS = ["coin", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    out = df.sort_values(["coin", "metric", "date"]).reset_index(drop=True)
    grouped = out.groupby(["coin", "metric"])["value"]

    out["value_norm"] = grouped.transform(
        lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0.0
    )
    out["rolling_avg"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).mean())
    out["pct_change"] = grouped.transform(lambda s: s.pct_change(periods=7))
    out["pct_change"] = out["pct_change"].replace([float("inf"), float("-inf")], None)

    roll_mean_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).mean())
    roll_std_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).std())
    out["zscore"] = (out["value"] - roll_mean_30) / roll_std_30
    out["zscore"] = out["zscore"].replace([float("inf"), float("-inf")], None)

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out[FEATURE_COLUMNS]
