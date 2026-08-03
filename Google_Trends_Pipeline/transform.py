"""
transform.py — Stage 3: Normalization, Stage 4: Feature Extraction

Rather than relying on Google's own 0-100 cross-batch normalization
(which only holds within a single query batch — see the note in
collect.py), each keyword's series is normalized against its OWN
history with min-max scaling. This sidesteps the cross-batch
comparability problem entirely, and arguably produces a more useful
signal for the prediction engine anyway: "is interest in this term
unusually high/low right now", not just a raw level that's partly an
artifact of which batch it was queried in.

Features produced per (keyword, date):
  - interest_norm    : min-max normalized interest, 0-1, within that
                        keyword's own history
  - rolling_avg_7d    : rolling mean over the last 7 DATA POINTS
                        (smooths noise)
  - pct_change_7d     : % change vs. 7 DATA POINTS prior (momentum)
  - zscore_30d        : how many std devs today's value is from the
                         trailing 30-DATA-POINT mean (anomaly/spike
                         indicator)

IMPORTANT — these column names say "7d"/"30d" but that's data points,
not calendar days. Google Trends changes the granularity of what it
returns based on how wide a window you ask for: under ~9 months you get
daily points, beyond that you get weekly points, and beyond ~5 years,
monthly. `collect.py` requests a rolling 2-year window (`HISTORY_YEARS`),
which is beyond that daily/weekly line, so Google returns
WEEKLY points — so as currently configured, rolling_avg_7d is really a
~7-week average and zscore_30d is really a ~30-week (~7 month) z-score,
not 7/30 calendar days. The math is correct either way; just don't read
the column names as a literal day count. If you shorten TIMEFRAME to
under 9 months, these become genuinely daily windows again — at the
cost of losing the longer history.
"""

import pandas as pd


def transform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(
            interest_norm=pd.Series(dtype=float),
            rolling_avg_7d=pd.Series(dtype=float),
            pct_change_7d=pd.Series(dtype=float),
            zscore_30d=pd.Series(dtype=float),
        )

    out = df.copy()
    grouped = out.groupby("keyword")["interest"]

    out["interest_norm"] = grouped.transform(
        lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0.0
    )
    out["rolling_avg_7d"] = grouped.transform(lambda s: s.rolling(7, min_periods=1).mean())
    out["pct_change_7d"] = grouped.transform(lambda s: s.pct_change(periods=7))

    roll_mean_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).mean())
    roll_std_30 = grouped.transform(lambda s: s.rolling(30, min_periods=5).std())
    out["zscore_30d"] = (out["interest"] - roll_mean_30) / roll_std_30
    out["zscore_30d"] = out["zscore_30d"].replace([float("inf"), float("-inf")], None)

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out