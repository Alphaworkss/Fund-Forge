"""
clean.py — Stage 2: Data Cleaning

Takes the raw records from collect.py and:
  - drops rows flagged is_partial=True — the current, still-accumulating
    commit week would otherwise pollute downstream feature calculations
    with a not-finished-yet value
  - drops duplicate (repo, date, metric) triples, keeping the latest

Unlike ../Google trends/clean.py, there is no zero-fill/forward-fill
step here: a 0 is a real data point (a quiet commit week), not evidence
of a reporting gap the way Google Trends' interest score dropping to 0
often is — GitHub's commit-count endpoint doesn't have that failure
mode, and stars/forks realistically never hit 0 for these repos.

No reshaping happens here — the output stays in the same raw shape as
the input (repo, date, metric, stars, forks, commits, is_partial), just
with fewer rows. Reshaping into the per-metric long format is
transform.py's job.
"""

import pandas as pd

RAW_COLUMNS = ["repo", "date", "metric", "stars", "forks", "commits", "is_partial"]


def clean(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=RAW_COLUMNS)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    # is_partial round-trips out of storage.py's SQLite github_raw table as
    # INTEGER 0/1 (or NULL), not Python bool — SQLite has no native boolean
    # type. Coerce to a clean bool dtype so `~` works regardless of whether
    # the input came fresh from collect.py (real bool) or back out of the
    # database (int 0/1, or None/NaN if absent). Missing/None is treated as
    # not-partial, consistent with how collect.py/storage.py always
    # populate a real value in practice.
    df["is_partial"] = df["is_partial"].apply(lambda v: bool(v) if pd.notna(v) else False)

    # Drop partial rows BEFORE deduplicating: this makes the result
    # order-independent. If dedup ran first, a finalized/partial duplicate
    # pair could have drop_duplicates(keep="last") keep the partial one
    # (if it happens to appear later in the input), which the partial
    # filter would then drop entirely — silently losing the data point.
    # Filtering first ensures only genuinely finalized rows ever reach
    # dedup, so whichever is "last" among them is a correct choice
    # regardless of input order.
    df = df[~df["is_partial"]].copy()
    df = df.drop_duplicates(subset=["repo", "date", "metric"], keep="last")

    for col in RAW_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df.sort_values(["repo", "metric", "date"])[RAW_COLUMNS].reset_index(drop=True)
