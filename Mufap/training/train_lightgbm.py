
"""
train_lightgbm.py

FundForge
LightGBM models for MUFAP NAV prediction

Trains LightGBM for all 8 prediction horizons:

NAV_15D
NAV_30D
NAV_90D
NAV_180D
NAV_270D
NAV_365D
NAV_730D
NAV_1095D

Produces:
    - One LightGBM model per horizon
    - One comparison CSV containing test metrics
"""

import os
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb

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
    "lightgbm_NAV"
)

RESULT_FOLDER = os.path.join(
    "training_results",
    "MUFAP"
)

RESULT_FILE = os.path.join(
    RESULT_FOLDER,
    "lightgbm_NAV_comparison.csv"
)


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
# LIGHTGBM PARAMETERS
# ============================================================

LGB_PARAMS = {

    "objective": "regression",

    "n_estimators": 500,

    "learning_rate": 0.05,

    "num_leaves": 31,

    "max_depth": -1,

    "subsample": 0.8,

    "colsample_bytree": 0.8,

    "reg_alpha": 0.0,

    "reg_lambda": 0.0,

    "random_state": 42,

    "n_jobs": -1
}


# ============================================================
# CREATE DIRECTORIES
# ============================================================

os.makedirs(
    MODEL_FOLDER,
    exist_ok=True
)

os.makedirs(
    RESULT_FOLDER,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print()
print("#" * 70)
print("FundForge - LightGBM MUFAP NAV Training")
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

invalid_dates = df["Validity_Date"].isna().sum()

print(
    f"Invalid dates removed : {invalid_dates:,}"
)

df = df.dropna(
    subset=["Validity_Date"]
).copy()


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    ["Fund", "Validity_Date"]
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

    # Targets
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
# DISPLAY FEATURES
# ============================================================

print()
print("Features:")

for feature in feature_columns:

    print(
        f"  - {feature}"
    )


# ============================================================
# EVALUATION FUNCTION
# ============================================================

def evaluate_model(
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


    return {

        "MAE": mae,

        "RMSE": rmse,

        "MAPE": mape,

        "R2": r2
    }


# ============================================================
# RESULTS STORAGE
# ============================================================

comparison_results = []


# ============================================================
# TRAIN ALL TARGETS
# ============================================================

for TARGET in TARGETS:

    print()
    print("#" * 70)
    print(
        f"TRAINING TARGET : {TARGET}"
    )
    print("#" * 70)


    # ========================================================
    # TARGET FILTERING
    # ========================================================

    target_df = df.copy()

    target_df[TARGET] = pd.to_numeric(
        target_df[TARGET],
        errors="coerce"
    )


    before = len(target_df)

    target_df = target_df.dropna(
        subset=[TARGET]
    ).copy()


    print(
        f"Rows after target filtering : "
        f"{len(target_df):,}"
    )


    # ========================================================
    # IMPORTANT:
    # LIGHTGBM CAN HANDLE NaN VALUES
    # ========================================================

    missing_values = target_df[
        feature_columns
    ].isna().sum().sum()


    print(
        f"Missing feature values : "
        f"{missing_values:,}"
    )

    print(
        "Keeping missing feature values "
        "because LightGBM handles NaN natively."
    )


    print(
        f"Final Rows : "
        f"{len(target_df):,}"
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


    # Safety check
    if (
        train_end_index >= n_dates
        or
        validation_end_index >= n_dates
    ):

        raise ValueError(
            f"Not enough dates for {TARGET}. "
            f"Available dates: {n_dates}"
        )


    train_end_date = unique_dates[
        train_end_index
    ]

    validation_end_date = unique_dates[
        validation_end_index
    ]


    train_df = target_df[
        target_df["Validity_Date"]
        <
        train_end_date
    ].copy()


    validation_df = target_df[
        (
            target_df["Validity_Date"]
            >=
            train_end_date
        )
        &
        (
            target_df["Validity_Date"]
            <
            validation_end_date
        )
    ].copy()


    test_df = target_df[
        target_df["Validity_Date"]
        >=
        validation_end_date
    ].copy()


    print(
        f"Training   : "
        f"{len(train_df):,}"
    )

    print(
        f"Validation : "
        f"{len(validation_df):,}"
    )

    print(
        f"Testing    : "
        f"{len(test_df):,}"
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
    # PREPARE DATA
    # ========================================================

    X_train = train_df[
        feature_columns
    ]

    y_train = train_df[
        TARGET
    ]


    X_validation = validation_df[
        feature_columns
    ]

    y_validation = validation_df[
        TARGET
    ]


    X_test = test_df[
        feature_columns
    ]

    y_test = test_df[
        TARGET
    ]


    # ========================================================
    # BUILD MODEL
    # ========================================================

    print()
    print(
        f"Training LightGBM for {TARGET}..."
    )


    model = lgb.LGBMRegressor(
        **LGB_PARAMS
    )


    # ========================================================
    # TRAIN
    # ========================================================

    model.fit(

        X_train,

        y_train,

        eval_set=[
            (
                X_validation,
                y_validation
            )
        ],

        callbacks=[
            lgb.early_stopping(
                30,
                verbose=False
            )
        ]
    )


    print(
        "Training completed."
    )


    # ========================================================
    # VALIDATION PREDICTIONS
    # ========================================================

    validation_predictions = model.predict(
        X_validation
    )


    validation_metrics = evaluate_model(

        y_validation,

        validation_predictions
    )


    print()
    print(
        "VALIDATION RESULTS"
    )

    print(
        f"MAE  : "
        f"{validation_metrics['MAE']:.6f}"
    )

    print(
        f"RMSE : "
        f"{validation_metrics['RMSE']:.6f}"
    )

    print(
        f"MAPE : "
        f"{validation_metrics['MAPE']:.4f}%"
    )

    print(
        f"R²   : "
        f"{validation_metrics['R2']:.6f}"
    )


    # ========================================================
    # TEST PREDICTIONS
    # ========================================================

    test_predictions = model.predict(
        X_test
    )


    test_metrics = evaluate_model(

        y_test,

        test_predictions
    )


    print()
    print(
        "TEST RESULTS"
    )

    print(
        f"MAE  : "
        f"{test_metrics['MAE']:.6f}"
    )

    print(
        f"RMSE : "
        f"{test_metrics['RMSE']:.6f}"
    )

    print(
        f"MAPE : "
        f"{test_metrics['MAPE']:.4f}%"
    )

    print(
        f"R²   : "
        f"{test_metrics['R2']:.6f}"
    )


    # ========================================================
    # SAVE MODEL
    # ========================================================

    model_file = os.path.join(

        MODEL_FOLDER,

        f"{TARGET}.pkl"
    )


    joblib.dump(
        model,
        model_file
    )


    # ========================================================
    # SAVE FEATURE LIST
    # ========================================================

    feature_file = os.path.join(

        MODEL_FOLDER,

        f"{TARGET}_features.pkl"
    )


    joblib.dump(

        feature_columns,

        feature_file
    )


    print()
    print(
        f"Model saved : "
        f"{model_file}"
    )


    # ========================================================
    # STORE COMPARISON RESULT
    # ========================================================

    comparison_results.append({

        "Target": TARGET,

        "Test_MAE":
            test_metrics["MAE"],

        "Test_RMSE":
            test_metrics["RMSE"],

        "Test_MAPE":
            test_metrics["MAPE"],

        "Test_R2":
            test_metrics["R2"]
    })


# ============================================================
# CREATE COMPARISON TABLE
# ============================================================

comparison_df = pd.DataFrame(
    comparison_results
)


# ============================================================
# PRINT COMPARISON TABLE
# ============================================================

print()
print("#" * 70)
print("LIGHTGBM COMPARISON TABLE")
print("#" * 70)

print()

print(
    comparison_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}"
    )
)


# ============================================================
# SAVE COMPARISON TABLE
# ============================================================

comparison_df.to_csv(
    RESULT_FILE,
    index=False
)


print()
print("#" * 70)
print("TRAINING COMPLETED")
print("#" * 70)

print()

print(
    "Comparison table saved to:"
)

print(
    RESULT_FILE
)

print()

print(
    "All 8 LightGBM models trained successfully."
)
