"""
create_master_comparison.py

FundForge
Creates a master comparison of:

    XGBoost
    LightGBM
    LSTM
    Transformer

across all MUFAP NAV prediction horizons.
"""

import os
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RESULT_FOLDER = os.path.join(
    "training_results",
    "MUFAP"
)

OUTPUT_FILE = os.path.join(
    RESULT_FOLDER,
    "MUFAP_NAV_MASTER_COMPARISON.csv"
)


MODEL_FILES = {
    "XGBoost": "xgboost_NAV_comparison.csv",
    "LightGBM": "lightgbm_NAV_comparison.csv",
    "LSTM": "lstm_NAV_comparison.csv",
    "Transformer": "transformer_NAV_comparison.csv"
}


# ============================================================
# LOAD RESULTS
# ============================================================

print()
print("#" * 70)
print("FundForge - MUFAP NAV Master Model Comparison")
print("#" * 70)

all_results = []


for model_name, filename in MODEL_FILES.items():

    filepath = os.path.join(
        RESULT_FOLDER,
        filename
    )

    print()
    print(
        f"Loading {model_name}..."
    )

    if not os.path.exists(filepath):

        print(
            f"ERROR: File not found:"
            f" {filepath}"
        )

        continue


    df = pd.read_csv(
        filepath
    )


    # Add model name

    df["Model"] = model_name


    all_results.append(
        df
    )


    print(
        f"Rows loaded : {len(df)}"
    )


# ============================================================
# COMBINE ALL MODELS
# ============================================================

if not all_results:

    print()
    print(
        "ERROR: No comparison files found."
    )

    raise SystemExit


master_df = pd.concat(
    all_results,
    ignore_index=True
)


# ============================================================
# REORDER COLUMNS
# ============================================================

master_df = master_df[
    [
        "Target",
        "Model",
        "Test_MAE",
        "Test_RMSE",
        "Test_MAPE",
        "Test_R2"
    ]
]


# ============================================================
# ROUND VALUES
# ============================================================

master_df["Test_MAE"] = master_df[
    "Test_MAE"
].round(4)


master_df["Test_RMSE"] = master_df[
    "Test_RMSE"
].round(4)


master_df["Test_MAPE"] = master_df[
    "Test_MAPE"
].round(4)


master_df["Test_R2"] = master_df[
    "Test_R2"
].round(4)


# ============================================================
# HORIZON ORDER
# ============================================================

horizon_order = [
    "NAV_15D",
    "NAV_30D",
    "NAV_90D",
    "NAV_180D",
    "NAV_270D",
    "NAV_365D",
    "NAV_730D",
    "NAV_1095D"
]


master_df["Horizon_Order"] = master_df[
    "Target"
].apply(
    lambda x:
    horizon_order.index(x)
    if x in horizon_order
    else 999
)


master_df = master_df.sort_values(
    [
        "Horizon_Order",
        "Model"
    ]
)


master_df = master_df.drop(
    columns=["Horizon_Order"]
)


# ============================================================
# SAVE MASTER TABLE
# ============================================================

master_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY MASTER TABLE
# ============================================================

print()
print("#" * 70)
print("MASTER COMPARISON TABLE")
print("#" * 70)

print()

print(
    master_df.to_string(
        index=False
    )
)


# ============================================================
# AUTOMATIC RANKING
# ============================================================

print()
print("#" * 70)
print("CALCULATING MODEL RANKINGS")
print("#" * 70)


ranking_results = []


for target in horizon_order:

    horizon_df = master_df[
        master_df["Target"] == target
    ].copy()


    if horizon_df.empty:

        continue


    # --------------------------------------------------------
    # Rank each metric
    #
    # MAE     → lower is better
    # RMSE    → lower is better
    # MAPE    → lower is better
    # R²      → higher is better
    # --------------------------------------------------------

    horizon_df["MAE_Rank"] = (
        horizon_df["Test_MAE"]
        .rank(
            ascending=True,
            method="min"
        )
    )


    horizon_df["RMSE_Rank"] = (
        horizon_df["Test_RMSE"]
        .rank(
            ascending=True,
            method="min"
        )
    )


    horizon_df["MAPE_Rank"] = (
        horizon_df["Test_MAPE"]
        .rank(
            ascending=True,
            method="min"
        )
    )


    horizon_df["R2_Rank"] = (
        horizon_df["Test_R2"]
        .rank(
            ascending=False,
            method="min"
        )
    )


    # --------------------------------------------------------
    # Overall score
    #
    # Lower score = better model
    # --------------------------------------------------------

    horizon_df["Overall_Score"] = (
        horizon_df["MAE_Rank"]
        +
        horizon_df["RMSE_Rank"]
        +
        horizon_df["MAPE_Rank"]
        +
        horizon_df["R2_Rank"]
    )


    horizon_df = horizon_df.sort_values(
        "Overall_Score"
    )


    # Overall rank

    horizon_df["Overall_Rank"] = range(
        1,
        len(horizon_df) + 1
    )


    # --------------------------------------------------------
    # Best model
    # --------------------------------------------------------

    best = horizon_df.iloc[0]


    ranking_results.append({

        "Target":
            target,

        "Best_Model":
            best["Model"],

        "Overall_Score":
            best["Overall_Score"],

        "MAE":
            best["Test_MAE"],

        "RMSE":
            best["Test_RMSE"],

        "MAPE":
            best["Test_MAPE"],

        "R2":
            best["Test_R2"]

    })


# ============================================================
# BEST MODEL TABLE
# ============================================================

best_models_df = pd.DataFrame(
    ranking_results
)


best_models_file = os.path.join(
    RESULT_FOLDER,
    "MUFAP_NAV_BEST_MODELS.csv"
)


best_models_df.to_csv(
    best_models_file,
    index=False
)


# ============================================================
# PRINT BEST MODELS
# ============================================================

print()
print("#" * 70)
print("BEST MODEL FOR EACH HORIZON")
print("#" * 70)

print()

print(
    best_models_df.to_string(
        index=False
    )
)


# ============================================================
# MODEL WIN COUNT
# ============================================================

win_counts = (
    best_models_df[
        "Best_Model"
    ]
    .value_counts()
    .reset_index()
)


win_counts.columns = [
    "Model",
    "Horizon_Wins"
]


print()
print("#" * 70)
print("MODEL WIN COUNT")
print("#" * 70)

print()

print(
    win_counts.to_string(
        index=False
    )
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("#" * 70)
print("COMPLETED")
print("#" * 70)

print()
print(
    "Master comparison:"
)

print(
    OUTPUT_FILE
)

print()
print(
    "Best models:"
)

print(
    best_models_file
)