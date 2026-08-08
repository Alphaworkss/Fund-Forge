
"""
train_xgboost.py

FundForge
XGBoost training for all MUFAP NAV prediction horizons
"""

import os
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_FILE = os.path.join(
    "training_data",
    "MUFAP_NAV_Features.csv"
)

MODEL_FOLDER = os.path.join(
    "models",
    "MUFAP",
    "xgboost_NAV"
)

RESULTS_FOLDER = os.path.join(
    "training_results",
    "MUFAP"
)

RESULTS_FILE = os.path.join(
    RESULTS_FOLDER,
    "xgboost_NAV_comparison.csv"
)


# ============================================================
# PREDICTION HORIZONS
# ============================================================

TARGETS = [
    "NAV_15D",
    "NAV_30D",
    "NAV_90D",
    "NAV_180D",
    "NAV_270D",
    "NAV_365D",
    "NAV_730D",
    "NAV_1095D"
]


# ============================================================
# XGBOOST PARAMETERS
# ============================================================

XGB_PARAMETERS = {

    "n_estimators": 500,

    "max_depth": 8,

    "learning_rate": 0.05,

    "subsample": 0.8,

    "colsample_bytree": 0.8,

    "objective": "reg:squarederror",

    "tree_method": "hist",

    "random_state": 42,

    "n_jobs": -1
}


# ============================================================
# CREATE FOLDERS
# ============================================================

os.makedirs(
    MODEL_FOLDER,
    exist_ok=True
)

os.makedirs(
    RESULTS_FOLDER,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print()
print("#" * 70)
print("FundForge - XGBoost MUFAP NAV Training")
print("#" * 70)


# ============================================================
# LOAD DATA
# ============================================================

print()
print("Loading dataset...")

df = pd.read_csv(
    DATA_FILE,
    low_memory=False
)

print(
    f"Rows Loaded : {len(df):,}"
)


# ============================================================
# CONVERT DATE
# ============================================================

df["Validity_Date"] = pd.to_datetime(
    df["Validity_Date"],
    errors="coerce"
)

before = len(df)

df = df.dropna(
    subset=["Validity_Date"]
).copy()

print(
    f"Invalid dates removed : "
    f"{before - len(df):,}"
)


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    ["Validity_Date", "Fund"]
).reset_index(
    drop=True
)


# ============================================================
# SELECT FEATURES
# ============================================================

exclude_columns = [

    "AMC",
    "Fund",
    "Validity_Date",

    # Prediction targets
    "NAV_15D",
    "NAV_30D",
    "NAV_90D",
    "NAV_180D",
    "NAV_270D",
    "NAV_365D",
    "NAV_730D",
    "NAV_1095D"
]


feature_columns = [
    col
    for col in df.columns
    if col not in exclude_columns
]


# ============================================================
# CONVERT FEATURES TO NUMERIC
# ============================================================

print()
print("Converting features to numeric...")

for col in feature_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


print(
    f"Features Available : "
    f"{len(feature_columns)}"
)


# ============================================================
# STORE RESULTS
# ============================================================

results = []


# ============================================================
# TRAIN EACH HORIZON
# ============================================================

for target in TARGETS:

    print()
    print("#" * 70)
    print(
        f"TRAINING TARGET : {target}"
    )
    print("#" * 70)


    # ========================================================
    # CONVERT TARGET
    # ========================================================

    df[target] = pd.to_numeric(
        df[target],
        errors="coerce"
    )


    # ========================================================
    # REMOVE MISSING TARGET
    # ========================================================

    target_df = df.dropna(
        subset=[target]
    ).copy()

    print()
    print(
        f"Rows after target filtering : "
        f"{len(target_df):,}"
    )


    # ========================================================
    # HANDLE MISSING FEATURES
    # ========================================================

    # XGBoost can handle NaN values natively.
    # Therefore, we keep rows containing missing feature values.

    missing_feature_values = target_df[
        feature_columns
    ].isna().sum().sum()

    print(
        f"Missing feature values : "
        f"{missing_feature_values:,}"
    )

    print(
        "Keeping missing feature values "
        "because XGBoost handles NaN natively."
    )

    print(
        f"Final Rows : {len(target_df):,}"
    )



    # ========================================================
    # CHRONOLOGICAL SPLIT
    # ========================================================

    print()
    print("Creating chronological split...")


    unique_dates = sorted(
        target_df[
            "Validity_Date"
        ].unique()
    )


    n_dates = len(
        unique_dates
    )


    train_end_index = int(
        n_dates * 0.60
    )

    validation_end_index = int(
        n_dates * 0.80
    )


    train_end_date = unique_dates[
        train_end_index
    ]

    validation_end_date = unique_dates[
        validation_end_index
    ]


    train_df = target_df[
        target_df["Validity_Date"]
        < train_end_date
    ].copy()


    validation_df = target_df[
        (target_df["Validity_Date"] >= train_end_date)
        &
        (target_df["Validity_Date"] < validation_end_date)
    ].copy()


    test_df = target_df[
        target_df["Validity_Date"]
        >= validation_end_date
    ].copy()


    print(
        f"Training   : {len(train_df):,}"
    )

    print(
        f"Validation : {len(validation_df):,}"
    )

    print(
        f"Testing    : {len(test_df):,}"
    )

    print()

    print(
        f"Train End : "
        f"{train_df['Validity_Date'].max()}"
    )

    print(
        f"Validation End : "
        f"{validation_df['Validity_Date'].max()}"
    )


    # ========================================================
    # PREPARE X AND Y
    # ========================================================

    X_train = train_df[
        feature_columns
    ]

    y_train = train_df[
        target
    ]


    X_validation = validation_df[
        feature_columns
    ]

    y_validation = validation_df[
        target
    ]


    X_test = test_df[
        feature_columns
    ]

    y_test = test_df[
        target
    ]


    # ========================================================
    # BUILD MODEL
    # ========================================================

    print()
    print("Building XGBoost model...")


    model = XGBRegressor(
        **XGB_PARAMETERS
    )


    # ========================================================
    # TRAIN
    # ========================================================

    print()
    print(
        f"Training XGBoost for {target}..."
    )


    model.fit(

        X_train,
        y_train,

        eval_set=[
            (
                X_validation,
                y_validation
            )
        ],

        verbose=False
    )


    print(
        "Training completed."
    )


    # ========================================================
    # EVALUATION FUNCTION
    # ========================================================

    def evaluate(
        actual,
        predicted
    ):

        mae = mean_absolute_error(
            actual,
            predicted
        )

        rmse = np.sqrt(
            mean_squared_error(
                actual,
                predicted
            )
        )


        mask = actual != 0


        if mask.sum() > 0:

            mape = np.mean(
                np.abs(
                    (
                        actual[mask]
                        -
                        predicted[mask]
                    )
                    /
                    actual[mask]
                )
            ) * 100

        else:

            mape = np.nan


        r2 = r2_score(
            actual,
            predicted
        )


        return (
            mae,
            rmse,
            mape,
            r2
        )


    # ========================================================
    # VALIDATION PREDICTIONS
    # ========================================================

    print()
    print(
        "Evaluating validation set..."
    )


    validation_predictions = model.predict(
        X_validation
    )


    (
        validation_mae,
        validation_rmse,
        validation_mape,
        validation_r2
    ) = evaluate(
        y_validation,
        validation_predictions
    )


    # ========================================================
    # TEST PREDICTIONS
    # ========================================================

    print(
        "Evaluating test set..."
    )


    test_predictions = model.predict(
        X_test
    )


    (
        test_mae,
        test_rmse,
        test_mape,
        test_r2
    ) = evaluate(
        y_test,
        test_predictions
    )


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print()
    print("-" * 70)
    print(
        f"{target} RESULTS"
    )
    print("-" * 70)


    print()
    print("VALIDATION")

    print(
        f"MAE  : {validation_mae:.6f}"
    )

    print(
        f"RMSE : {validation_rmse:.6f}"
    )

    print(
        f"MAPE : {validation_mape:.4f}%"
    )

    print(
        f"R²   : {validation_r2:.6f}"
    )


    print()
    print("TEST")

    print(
        f"MAE  : {test_mae:.6f}"
    )

    print(
        f"RMSE : {test_rmse:.6f}"
    )

    print(
        f"MAPE : {test_mape:.4f}%"
    )

    print(
        f"R²   : {test_r2:.6f}"
    )


    # ========================================================
    # SAVE MODEL
    # ========================================================

    model_file = os.path.join(
        MODEL_FOLDER,
        f"{target}.pkl"
    )


    joblib.dump(
        model,
        model_file
    )


    print()
    print(
        f"Model saved : {model_file}"
    )


    # ========================================================
    # SAVE RESULTS
    # ========================================================

    results.append({

        "Target": target,

        "Train_Rows": len(train_df),

        "Validation_Rows": len(
            validation_df
        ),

        "Test_Rows": len(
            test_df
        ),

        "Validation_MAE":
            validation_mae,

        "Validation_RMSE":
            validation_rmse,

        "Validation_MAPE":
            validation_mape,

        "Validation_R2":
            validation_r2,

        "Test_MAE":
            test_mae,

        "Test_RMSE":
            test_rmse,

        "Test_MAPE":
            test_mape,

        "Test_R2":
            test_r2,

        "Model_Path":
            model_file
    })


# ============================================================
# CREATE COMPARISON TABLE
# ============================================================

print()
print("#" * 70)
print("XGBOOST COMPARISON TABLE")
print("#" * 70)


results_df = pd.DataFrame(
    results
)


# ============================================================
# ROUND VALUES
# ============================================================

numeric_columns = [

    "Validation_MAE",
    "Validation_RMSE",
    "Validation_MAPE",
    "Validation_R2",

    "Test_MAE",
    "Test_RMSE",
    "Test_MAPE",
    "Test_R2"
]


results_df[
    numeric_columns
] = results_df[
    numeric_columns
].round(6)


# ============================================================
# DISPLAY TABLE
# ============================================================

print()

print(
    results_df[
        [
            "Target",

            "Test_MAE",
            "Test_RMSE",
            "Test_MAPE",
            "Test_R2"
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# SAVE COMPARISON
# ============================================================

results_df.to_csv(
    RESULTS_FILE,
    index=False
)


print()
print("#" * 70)
print("TRAINING COMPLETED")
print("#" * 70)

print()
print(
    f"Comparison table saved to:"
)

print(
    RESULTS_FILE
)

print()
print(
    "All 8 XGBoost models trained successfully."
)
