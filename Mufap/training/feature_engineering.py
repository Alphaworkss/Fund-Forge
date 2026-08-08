"""
feature_engineering.py

FundForge
MUFAP NAV Feature Engineering

Creates historical NAV features and future prediction targets
for every FundID independently.

Important:
- FundID is treated as the unique fund/product identity.
- Different categories with the same Fund name are NOT merged.
- Invalid/non-positive NAV values are removed.
- Duplicate FundID + Validity_Date records are handled.
- Features are calculated independently for every FundID.
"""

import os
import pandas as pd
import numpy as np


# ============================================================
# FILES
# ============================================================

INPUT_FILE = os.path.join(
    "training_data",
    "MUFAP_NAV_Preprocessed.csv"
)

OUTPUT_FOLDER = "training_data"

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "MUFAP_NAV_Features.csv"
)


# ============================================================
# PREDICTION HORIZONS
# ============================================================

HORIZONS = [
    15,
    30,
    90,
    180,
    270,
    365,
    730,
    1095
]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_features(df):

    print("\nCreating features...")

    # ========================================================
    # BASIC CLEANING
    # ========================================================

    print("\nCleaning NAV data...")

    # Ensure required columns exist
    required_columns = [
        "FundID",
        "Fund",
        "Validity_Date",
        "NAV"
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    # Convert NAV to numeric
    df["NAV"] = pd.to_numeric(
        df["NAV"],
        errors="coerce"
    )

    # Convert date
    df["Validity_Date"] = pd.to_datetime(
        df["Validity_Date"],
        errors="coerce"
    )

    # Remove missing FundID
    before = len(df)

    df = df.dropna(
        subset=[
            "FundID",
            "Validity_Date",
            "NAV"
        ]
    ).copy()

    print(
        f"Rows removed due to missing values : "
        f"{before - len(df):,}"
    )

    # ========================================================
    # REMOVE INVALID NAV VALUES
    # ========================================================

    before = len(df)

    invalid_nav = (
        (df["NAV"] <= 0)
        |
        (~np.isfinite(df["NAV"]))
    )

    invalid_count = invalid_nav.sum()

    df = df[
        ~invalid_nav
    ].copy()

    print(
        f"Invalid/non-positive NAV rows removed : "
        f"{invalid_count:,}"
    )

    # ========================================================
    # SORT
    # ========================================================

    df = df.sort_values(
        [
            "FundID",
            "Validity_Date"
        ]
    ).reset_index(
        drop=True
    )

    # ========================================================
    # REMOVE DUPLICATE FUNDID + DATE
    # ========================================================

    print(
        "\nChecking duplicate FundID + Validity_Date records..."
    )

    duplicate_mask = df.duplicated(
        subset=[
            "FundID",
            "Validity_Date"
        ],
        keep=False
    )

    duplicate_rows = duplicate_mask.sum()

    print(
        f"Duplicate rows detected : "
        f"{duplicate_rows:,}"
    )

    if duplicate_rows > 0:

        print(
            "Keeping the last record for each "
            "FundID + Validity_Date."
        )

        df = df.drop_duplicates(
            subset=[
                "FundID",
                "Validity_Date"
            ],
            keep="last"
        ).copy()

    # Sort again
    df = df.sort_values(
        [
            "FundID",
            "Validity_Date"
        ]
    ).reset_index(
        drop=True
    )

    # ========================================================
    # GROUP BY FUNDID
    # ========================================================

    print(
        "\nGrouping data by FundID..."
    )

    grouped = df.groupby(
        "FundID",
        group_keys=False
    )

    print(
        f"Unique FundIDs : "
        f"{df['FundID'].nunique():,}"
    )

    # ========================================================
    # NAV LAG FEATURES
    # ========================================================

    print(
        "\nCreating NAV lag features..."
    )

    lag_periods = [
        1,
        5,
        10,
        20,
        30,
        60
    ]

    for lag in lag_periods:

        df[f"NAV_Lag_{lag}"] = (
            grouped["NAV"].shift(lag)
        )

    # ========================================================
    # NAV RETURN FEATURES
    # ========================================================

    print(
        "Creating return features..."
    )

    df["NAV_Return_1D"] = (
        grouped["NAV"].pct_change(1)
    )

    df["NAV_Return_5D"] = (
        grouped["NAV"].pct_change(5)
    )

    df["NAV_Return_10D"] = (
        grouped["NAV"].pct_change(10)
    )

    df["NAV_Return_20D"] = (
        grouped["NAV"].pct_change(20)
    )

    df["NAV_Return_30D"] = (
        grouped["NAV"].pct_change(30)
    )

    # ========================================================
    # MOVING AVERAGES
    # ========================================================

    print(
        "Creating moving averages..."
    )

    for window in [
        7,
        14,
        30,
        60
    ]:

        df[f"NAV_MA_{window}"] = (
            grouped["NAV"]
            .transform(
                lambda x:
                x.rolling(
                    window=window,
                    min_periods=window
                ).mean()
            )
        )

    # ========================================================
    # ROLLING STANDARD DEVIATION
    # ========================================================

    print(
        "Creating volatility features..."
    )

    for window in [
        7,
        14,
        30,
        60
    ]:

        df[f"NAV_STD_{window}"] = (
            grouped["NAV"]
            .transform(
                lambda x:
                x.rolling(
                    window=window,
                    min_periods=window
                ).std()
            )
        )

    # ========================================================
    # ROLLING MINIMUM
    # ========================================================

    print(
        "Creating rolling minimum features..."
    )

    for window in [
        7,
        30,
        60
    ]:

        df[f"NAV_MIN_{window}"] = (
            grouped["NAV"]
            .transform(
                lambda x:
                x.rolling(
                    window=window,
                    min_periods=window
                ).min()
            )
        )

    # ========================================================
    # ROLLING MAXIMUM
    # ========================================================

    print(
        "Creating rolling maximum features..."
    )

    for window in [
        7,
        30,
        60
    ]:

        df[f"NAV_MAX_{window}"] = (
            grouped["NAV"]
            .transform(
                lambda x:
                x.rolling(
                    window=window,
                    min_periods=window
                ).max()
            )
        )

    # ========================================================
    # FUTURE TARGETS
    # ========================================================

    print(
        "\nCreating future NAV targets..."
    )

    # We use calendar dates rather than simply shift(-15).
    #
    # Example:
    #
    # Current date : 2026-08-01
    # 15D target   : NAV around 2026-08-16
    #
    # This is more appropriate when the dataset contains
    # missing dates/weekends.

    for horizon in HORIZONS:

        target_column = (
            f"NAV_{horizon}D"
        )

        print(
            f"  Creating {target_column}..."
        )

        future_dates = (
            df["Validity_Date"]
            +
            pd.Timedelta(
                days=horizon
            )
        )

        future_lookup = (
            df[
                [
                    "FundID",
                    "Validity_Date",
                    "NAV"
                ]
            ]
            .rename(
                columns={
                    "Validity_Date":
                        "Future_Date",

                    "NAV":
                        target_column
                }
            )
        )

        # Merge exact future calendar date
        target_data = pd.DataFrame({

            "FundID":
                df["FundID"].values,

            "Future_Date":
                future_dates.values
        })

        target_data = target_data.merge(
            future_lookup,
            on=[
                "FundID",
                "Future_Date"
            ],
            how="left"
        )

        df[target_column] = (
            target_data[target_column]
            .values
        )

    # ========================================================
    # FUTURE RETURN TARGETS
    # ========================================================

    print(
        "\nCreating future return targets..."
    )

    for horizon in HORIZONS:

        nav_target = (
            f"NAV_{horizon}D"
        )

        return_target = (
            f"Return_{horizon}D"
        )

        df[return_target] = (
            df[nav_target]
            /
            df["NAV"]
        ) - 1

    # ========================================================
    # REMOVE EXTREME NUMERIC ERRORS
    # ========================================================

    df.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan,
        inplace=True
    )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "FundForge - MUFAP NAV Feature Engineering"
    )
    print("=" * 70)

    # ========================================================
    # LOAD DATA
    # ========================================================

    print(
        "\nLoading preprocessed dataset..."
    )

    df = pd.read_csv(
        INPUT_FILE,
        low_memory=False
    )

    print(
        f"Rows Loaded : {len(df):,}"
    )

    # ========================================================
    # CREATE FEATURES
    # ========================================================

    df = create_features(
        df
    )

    # ========================================================
    # SAVE
    # ========================================================

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    print(
        "\nSaving feature dataset..."
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print(
        "FEATURE ENGINEERING COMPLETED"
    )
    print("=" * 70)

    print(
        f"Rows             : "
        f"{len(df):,}"
    )

    print(
        f"Columns          : "
        f"{len(df.columns)}"
    )

    print(
        f"Unique Funds     : "
        f"{df['Fund'].nunique():,}"
    )

    print(
        f"Unique FundIDs   : "
        f"{df['FundID'].nunique():,}"
    )

    print(
        "\nPrediction Horizons:"
    )

    for horizon in HORIZONS:

        print(
            f"  NAV_{horizon}D"
        )

    print(
        f"\nSaved To : "
        f"{OUTPUT_FILE}"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()