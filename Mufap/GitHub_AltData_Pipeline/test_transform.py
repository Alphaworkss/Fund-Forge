"""
test_transform.py — Stage 8: Testing (transform.py)

Run with: pytest test_transform.py
"""

import pandas as pd

from transform import _melt_to_long, transform


def test_melt_splits_snapshot_into_stars_and_forks():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-30"), "metric": "snapshot",
         "stars": 100, "forks": 20, "commits": pd.NA, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert set(long_df["metric"]) == {"stars", "forks"}
    assert long_df[long_df["metric"] == "stars"]["value"].iloc[0] == 100
    assert long_df[long_df["metric"] == "forks"]["value"].iloc[0] == 20


def test_melt_renames_commits_column_to_value():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert list(long_df["metric"]) == ["commits"]
    assert long_df["value"].iloc[0] == 5


def test_melt_output_has_exactly_these_columns():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert list(long_df.columns) == ["repo", "date", "metric", "value"]


def test_melt_handles_mixed_snapshot_and_commits_rows():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-30"), "metric": "snapshot",
         "stars": 100, "forks": 20, "commits": pd.NA, "is_partial": False},
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    long_df = _melt_to_long(df)

    assert len(long_df) == 3
    assert set(long_df["metric"]) == {"stars", "forks", "commits"}


def test_melt_empty_dataframe_returns_empty_long_dataframe():
    df = pd.DataFrame(columns=["repo", "date", "metric", "stars", "forks", "commits", "is_partial"])

    long_df = _melt_to_long(df)

    assert long_df.empty
    assert list(long_df.columns) == ["repo", "date", "metric", "value"]


def test_transform_adds_expected_columns():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    out = transform(df)

    assert set(out.columns) == {"repo", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}


def test_transform_normalizes_within_zero_one_per_series():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp(f"2026-01-0{i}"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": v, "is_partial": False}
        for i, v in zip(range(1, 4), [5, 10, 15])
    ])

    out = transform(df)

    assert out["value_norm"].min() == 0.0
    assert out["value_norm"].max() == 1.0


def test_transform_computes_independent_series_per_metric():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-30"), "metric": "snapshot",
         "stars": 100, "forks": 20, "commits": pd.NA, "is_partial": False},
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    out = transform(df)

    stars_rows = out[out["metric"] == "stars"]
    forks_rows = out[out["metric"] == "forks"]
    commits_rows = out[out["metric"] == "commits"]
    assert len(stars_rows) == 1 and stars_rows["value"].iloc[0] == 100
    assert len(forks_rows) == 1 and forks_rows["value"].iloc[0] == 20
    assert len(commits_rows) == 1 and commits_rows["value"].iloc[0] == 5

    # Each metric is a single-point group for repo x/y, so value_norm should be 0.0
    # (zero-variance branch: s.max() == s.min() for a single point). This test catches
    # a regression where groupby(["repo", "metric"]) is accidentally changed to groupby(["repo"]),
    # which would produce cross-contaminated values like [0.0, 0.158, 1.0] instead.
    assert stars_rows["value_norm"].iloc[0] == 0.0
    assert forks_rows["value_norm"].iloc[0] == 0.0
    assert commits_rows["value_norm"].iloc[0] == 0.0


def test_transform_two_repos_do_not_mix_series():
    df = pd.DataFrame([
        {"repo": "a/a", "date": pd.Timestamp("2026-01-01"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 100, "is_partial": False},
        {"repo": "b/b", "date": pd.Timestamp("2026-01-01"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 1, "is_partial": False},
    ])

    out = transform(df)

    assert (out["value_norm"] == 0.0).all()


def test_transform_date_formatted_as_string():
    df = pd.DataFrame([
        {"repo": "x/y", "date": pd.Timestamp("2026-07-27"), "metric": "commits",
         "stars": pd.NA, "forks": pd.NA, "commits": 5, "is_partial": False},
    ])

    out = transform(df)

    assert out["date"].iloc[0] == "2026-07-27"


def test_transform_pct_change_from_zero_baseline_is_not_inf():
    # pct_change(periods=7) divides by the value 7 rows prior. When that
    # prior value is 0 (a real, legitimate "quiet commit week" per
    # design.md, not a data gap) and the later value is nonzero, pandas
    # computes literal inf. That must not leak into storage/Excel — it
    # should be coerced to None/NaN, matching how zscore already handles
    # its own inf case.
    dates = pd.date_range("2026-01-01", periods=8, freq="D")
    values = [0, 1, 1, 1, 1, 1, 1, 5]
    df = pd.DataFrame([
        {"repo": "x/y", "date": d, "metric": "commits", "stars": pd.NA, "forks": pd.NA,
         "commits": v, "is_partial": False}
        for d, v in zip(dates, values)
    ])

    out = transform(df)

    last_row = out.iloc[-1]
    assert last_row["value"] == 5
    assert pd.isna(last_row["pct_change"])


def test_transform_empty_dataframe_returns_empty_with_all_columns():
    df = pd.DataFrame(columns=["repo", "date", "metric", "stars", "forks", "commits", "is_partial"])

    out = transform(df)

    assert out.empty
    assert set(out.columns) == {"repo", "date", "metric", "value", "value_norm", "rolling_avg", "pct_change", "zscore"}
