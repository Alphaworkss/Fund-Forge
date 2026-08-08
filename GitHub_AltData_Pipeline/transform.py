"""
transform.py — Stage 3: Normalization, Stage 4: Feature Extraction

collect.py's raw taxonomy has 2 metrics ("snapshot" carrying both stars
and forks; "commits" carrying one number), but github_features has one
`value` column per (repo, date, metric) row — there's no schema room
for two numbers on one row. So _melt_to_long() explodes each
"snapshot" row into two rows ("stars", "forks"); "commits" rows keep
their row, renamed to "value". The result is three fully independent
series per repo (stars, forks, commits) — their growth rates don't
meaningfully correlate on any short window, so each gets its own
normalization and rolling stats, grouped by (repo, metric) rather than
Google Trends' single-key groupby("keyword").
"""

import pandas as pd

LONG_COLUMNS = ["repo", "date", "metric", "value"]
FEATURE_COLUMNS = ["repo", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"]


def _melt_to_long(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=LONG_COLUMNS)

    commits_rows = (
        df[df["metric"] == "commits"][["repo", "date", "commits"]]
        .rename(columns={"commits": "value"})
        .assign(metric="commits")
    )

    snapshot = df[df["metric"] == "snapshot"]
    stars_rows = (
        snapshot[["repo", "date", "stars"]]
        .rename(columns={"stars": "value"})
        .assign(metric="stars")
    )
    forks_rows = (
        snapshot[["repo", "date", "forks"]]
        .rename(columns={"forks": "value"})
        .assign(metric="forks")
    )

    long_df = pd.concat([commits_rows, stars_rows, forks_rows], ignore_index=True)
    return long_df[LONG_COLUMNS]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    long_df = _melt_to_long(df)

    if long_df.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    out = long_df.sort_values(["repo", "metric", "date"]).reset_index(drop=True)
    grouped = out.groupby(["repo", "metric"])["value"]

    out["value_norm"] = grouped.transform(
        lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0.0
    )
    out["rolling_avg"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).mean())
    out["pct_change"] = grouped.transform(lambda s: s.pct_change(periods=7))
    out["pct_change"] = out["pct_change"].replace([float("inf"), float("-inf")], float("nan"))

    roll_mean_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).mean())
    roll_std_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).std())
    out["zscore"] = (out["value"] - roll_mean_30) / roll_std_30
    out["zscore"] = out["zscore"].replace([float("inf"), float("-inf")], float("nan"))

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out[FEATURE_COLUMNS]
