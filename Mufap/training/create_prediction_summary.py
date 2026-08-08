
"""
create_prediction_summary.py

FundForge
MUFAP NAV Prediction Summary

Reads:
    predictions/MUFAP/MUFAP_NAV_PREDICTIONS.csv

The prediction file contains:

    AMC
    Fund
    Latest_Date
    Current_NAV
    Predicted_NAV_15D
    Predicted_NAV_30D
    Predicted_NAV_90D
    Predicted_NAV_180D
    Predicted_NAV_270D
    Predicted_NAV_365D
    Predicted_NAV_730D
    Predicted_NAV_1095D

Produces:

    predictions/MUFAP/MUFAP_NAV_PREDICTION_SUMMARY.csv

The summary contains:

    AMC
    Fund
    Latest_Date
    Current_NAV
    Predicted NAV for each horizon
    Percentage change for each horizon
"""


import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PREDICTION_FILE = os.path.join(
    "predictions",
    "MUFAP",
    "MUFAP_NAV_PREDICTIONS.csv"
)


OUTPUT_FILE = os.path.join(
    "predictions",
    "MUFAP",
    "MUFAP_NAV_PREDICTION_SUMMARY.csv"
)


# ============================================================
# HORIZONS
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
# HEADER
# ============================================================

print()
print("#" * 70)
print("FundForge - MUFAP NAV Prediction Summary")
print("#" * 70)


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(PREDICTION_FILE):

    raise FileNotFoundError(
        f"Prediction file not found:\n"
        f"{PREDICTION_FILE}"
    )


# ============================================================
# LOAD DATA
# ============================================================

print()
print("Loading predictions...")

df = pd.read_csv(
    PREDICTION_FILE,
    low_memory=False
)


print(
    f"Rows loaded : {len(df):,}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [

    "AMC",

    "Fund",

    "Latest_Date",

    "Current_NAV"
]


for horizon in HORIZONS:

    required_columns.append(
        f"Predicted_NAV_{horizon}D"
    )


missing_columns = [

    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    print()
    print("ERROR: Missing columns:")

    for column in missing_columns:

        print(
            f"  - {column}"
        )

    raise ValueError(
        "Prediction CSV does not contain "
        "the required columns."
    )


# ============================================================
# DATE
# ============================================================

df["Latest_Date"] = pd.to_datetime(
    df["Latest_Date"],
    errors="coerce"
)


# ============================================================
# NUMERIC CONVERSION
# ============================================================

df["Current_NAV"] = pd.to_numeric(
    df["Current_NAV"],
    errors="coerce"
)


for horizon in HORIZONS:

    column = (
        f"Predicted_NAV_{horizon}D"
    )

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# CREATE SUMMARY
# ============================================================

summary = df[
    [
        "AMC",
        "Fund",
        "Latest_Date",
        "Current_NAV"
    ]
].copy()


# ============================================================
# CALCULATE PREDICTED NAV + CHANGE %
# ============================================================

for horizon in HORIZONS:

    prediction_column = (
        f"Predicted_NAV_{horizon}D"
    )

    change_column = (
        f"Change_{horizon}D_Percent"
    )


    # --------------------------------------------------------
    # Predicted NAV
    # --------------------------------------------------------

    summary[
        prediction_column
    ] = df[
        prediction_column
    ]


    # --------------------------------------------------------
    # Percentage Change
    #
    # Change % =
    # ((Predicted NAV - Current NAV)
    #  / Current NAV) * 100
    # --------------------------------------------------------

    summary[
        change_column
    ] = np.where(

        (
            df["Current_NAV"].notna()
            &
            df[prediction_column].notna()
            &
            (df["Current_NAV"] != 0)
        ),

        (
            (
                df[prediction_column]
                -
                df["Current_NAV"]
            )
            /
            df["Current_NAV"]
        )
        * 100,

        np.nan
    )


# ============================================================
# SAVE SUMMARY
# ============================================================

summary.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# BASIC INFORMATION
# ============================================================

print()
print("#" * 70)
print("SUMMARY CREATED SUCCESSFULLY")
print("#" * 70)

print()

print(
    f"Funds processed : "
    f"{summary['Fund'].nunique():,}"
)

print(
    f"Horizons        : "
    f"{len(HORIZONS)}"
)

print()

print(
    "Output file:"
)

print(
    OUTPUT_FILE
)


# ============================================================
# HORIZON STATISTICS
# ============================================================

print()
print("#" * 70)
print("PREDICTION STATISTICS")
print("#" * 70)


for horizon in HORIZONS:

    prediction_column = (
        f"Predicted_NAV_{horizon}D"
    )

    change_column = (
        f"Change_{horizon}D_Percent"
    )


    valid_predictions = summary[
        prediction_column
    ].dropna()


    valid_changes = summary[
        change_column
    ].dropna()


    if len(valid_predictions) == 0:

        print()
        print(
            f"{horizon:4}D : No valid predictions"
        )

        continue


    positive = (
        valid_changes > 0
    ).sum()


    negative = (
        valid_changes < 0
    ).sum()


    unchanged = (
        valid_changes == 0
    ).sum()


    print()

    print(
        f"{horizon:4}D : "
        f"Predictions = {len(valid_predictions):3d} | "
        f"Average Change = "
        f"{valid_changes.mean():8.2f}% | "
        f"Median = "
        f"{valid_changes.median():8.2f}% | "
        f"Positive = {positive:3d} | "
        f"Negative = {negative:3d} | "
        f"Zero = {unchanged:3d}"
    )


# ============================================================
# EXTREME CHANGE CHECK
# ============================================================

print()
print("#" * 70)
print("EXTREME PREDICTION CHECK")
print("#" * 70)


for horizon in HORIZONS:

    change_column = (
        f"Change_{horizon}D_Percent"
    )


    valid = summary[
        [
            "AMC",
            "Fund",
            "Current_NAV",
            f"Predicted_NAV_{horizon}D",
            change_column
        ]
    ].dropna(
        subset=[change_column]
    )


    if len(valid) == 0:

        continue


    extreme = valid[
        valid[change_column].abs() > 50
    ]


    print()

    print(
        f"{horizon:4}D : "
        f"{len(extreme)} predictions "
        f"with change > ±50%"
    )


    if len(extreme) > 0:

        print()

        print(
            extreme.sort_values(
                change_column,
                key=lambda x: x.abs(),
                ascending=False
            )
            .head(5)
            .to_string(
                index=False,
                float_format=lambda x:
                f"{x:.4f}"
            )
        )


# ============================================================
# SAMPLE
# ============================================================

print()
print("#" * 70)
print("SAMPLE PREDICTIONS")
print("#" * 70)

print()

sample_columns = [

    "Fund",

    "Current_NAV",

    "Predicted_NAV_15D",

    "Change_15D_Percent",

    "Predicted_NAV_30D",

    "Change_30D_Percent",

    "Predicted_NAV_90D",

    "Change_90D_Percent"
]


print(
    summary[
        sample_columns
    ]
    .head(10)
    .to_string(
        index=False,
        float_format=lambda x:
        f"{x:.4f}"
    )
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print()
print("#" * 70)
print("COMPLETED")
print("#" * 70)

print()

print(
    "Summary saved to:"
)

print(
    OUTPUT_FILE
)
