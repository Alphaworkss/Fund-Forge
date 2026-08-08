
"""
train_lstm.py

FundForge
LSTM models for MUFAP NAV prediction

Trains LSTM for all 8 prediction horizons:

NAV_15D
NAV_30D
NAV_90D
NAV_180D
NAV_270D
NAV_365D
NAV_730D
NAV_1095D

Produces:
    - One LSTM model per horizon
    - One scaler per horizon
    - One feature list per horizon
    - One training history per horizon
    - One comparison CSV
"""

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from sklearn.preprocessing import StandardScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout
)

from tensorflow.keras.callbacks import EarlyStopping


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
    "lstm_NAV"
)

RESULT_FOLDER = os.path.join(
    "training_results",
    "MUFAP"
)

RESULT_FILE = os.path.join(
    RESULT_FOLDER,
    "lstm_NAV_comparison.csv"
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


SEQUENCE_LENGTH = 30

EPOCHS = 30

BATCH_SIZE = 256


# ============================================================
# DIRECTORIES
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
print("FundForge - LSTM MUFAP NAV Training")
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
# DATE CONVERSION
# ============================================================

df["Validity_Date"] = pd.to_datetime(
    df["Validity_Date"],
    errors="coerce"
)

invalid_dates = df[
    "Validity_Date"
].isna().sum()

print(
    f"Invalid dates removed : "
    f"{invalid_dates:,}"
)

df = df.dropna(
    subset=["Validity_Date"]
).copy()


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    [
        "Fund",
        "Validity_Date"
    ]
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


# ============================================================
# CONVERT POSSIBLE FEATURES TO NUMERIC
# ============================================================

print()
print("Selecting numeric features...")

candidate_features = [
    col
    for col in df.columns
    if col not in exclude_columns
]


for col in candidate_features:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


feature_columns = [
    col
    for col in candidate_features
    if pd.api.types.is_numeric_dtype(
        df[col]
    )
]


print(
    f"Numeric Features Available : "
    f"{len(feature_columns)}"
)


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
# CREATE SEQUENCES
# ============================================================

def create_sequences(
    data,
    feature_columns,
    target,
    sequence_length
):

    X = []
    y = []

    for fund, group in data.groupby(
        "Fund",
        sort=False
    ):

        group = group.sort_values(
            "Validity_Date"
        )

        values = group[
            feature_columns
        ].values.astype(
            np.float32
        )

        targets = group[
            target
        ].values.astype(
            np.float32
        )


        if len(group) <= sequence_length:

            continue


        for i in range(
            sequence_length,
            len(group)
        ):

            X.append(
                values[
                    i - sequence_length:i
                ]
            )

            y.append(
                targets[i]
            )


    if len(X) == 0:

        return (

            np.empty(
                (
                    0,
                    sequence_length,
                    len(feature_columns)
                ),
                dtype=np.float32
            ),

            np.empty(
                (0,),
                dtype=np.float32
            )
        )


    return (

        np.asarray(
            X,
            dtype=np.float32
        ),

        np.asarray(
            y,
            dtype=np.float32
        )
    )


# ============================================================
# RESULTS
# ============================================================

comparison_results = []


# ============================================================
# TRAIN EACH HORIZON
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
    # FILL MISSING FEATURES
    # ========================================================

    print()
    print(
        "Handling missing feature values..."
    )


    missing_before = target_df[
        feature_columns
    ].isna().sum().sum()


    print(
        f"Missing feature values before "
        f"filling : {missing_before:,}"
    )


    # Forward/backward fill within each fund
    target_df[feature_columns] = (

        target_df
        .groupby("Fund")[
            feature_columns
        ]
        .transform(
            lambda x:
            x.ffill().bfill()
        )
    )


    # Remaining values, if any
    target_df[feature_columns] = (

        target_df[
            feature_columns
        ].fillna(0)
    )


    missing_after = target_df[
        feature_columns
    ].isna().sum().sum()


    print(
        f"Missing feature values after "
        f"filling : {missing_after:,}"
    )


    print(
        f"Final Rows : "
        f"{len(target_df):,}"
    )


    # ========================================================
    # CHRONOLOGICAL SPLIT
    # ========================================================

    print()
    print(
        "Creating chronological split..."
    )


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
    # SCALE FEATURES
    # ========================================================

    print()
    print(
        "Scaling features..."
    )


    scaler = StandardScaler()


    # Explicit float conversion avoids
    # pandas incompatible dtype warnings

    train_features = train_df[
        feature_columns
    ].astype(
        np.float32
    )

    validation_features = validation_df[
        feature_columns
    ].astype(
        np.float32
    )

    test_features = test_df[
        feature_columns
    ].astype(
        np.float32
    )


    scaler.fit(
        train_features
    )


    train_df.loc[
        :,
        feature_columns
    ] = scaler.transform(
        train_features
    )


    validation_df.loc[
        :,
        feature_columns
    ] = scaler.transform(
        validation_features
    )


    test_df.loc[
        :,
        feature_columns
    ] = scaler.transform(
        test_features
    )


    # ========================================================
    # CREATE SEQUENCES
    # ========================================================

    print()
    print(
        f"Creating "
        f"{SEQUENCE_LENGTH}-day sequences..."
    )


    X_train, y_train = create_sequences(
        train_df,
        feature_columns,
        TARGET,
        SEQUENCE_LENGTH
    )


    X_validation, y_validation = create_sequences(
        validation_df,
        feature_columns,
        TARGET,
        SEQUENCE_LENGTH
    )


    X_test, y_test = create_sequences(
        test_df,
        feature_columns,
        TARGET,
        SEQUENCE_LENGTH
    )


    print()
    print(
        f"Training sequences   : "
        f"{len(X_train):,}"
    )

    print(
        f"Validation sequences : "
        f"{len(X_validation):,}"
    )

    print(
        f"Testing sequences    : "
        f"{len(X_test):,}"
    )


    print(
        f"Input shape : "
        f"{X_train.shape}"
    )


    # ========================================================
    # BUILD LSTM
    # ========================================================

    print()
    print(
        f"Building LSTM model for "
        f"{TARGET}..."
    )


    model = Sequential([

        LSTM(
            128,
            return_sequences=True,
            input_shape=(
                SEQUENCE_LENGTH,
                len(feature_columns)
            )
        ),

        Dropout(0.2),

        LSTM(
            64,
            return_sequences=False
        ),

        Dropout(0.2),

        Dense(
            32,
            activation="relu"
        ),

        Dense(
            1
        )
    ])


    model.compile(

        optimizer="adam",

        loss="mse"
    )


    # ========================================================
    # EARLY STOPPING
    # ========================================================

    early_stopping = EarlyStopping(

        monitor="val_loss",

        patience=5,

        restore_best_weights=True
    )


    # ========================================================
    # TRAIN
    # ========================================================

    print()
    print(
        f"Training LSTM for {TARGET}..."
    )


    history = model.fit(

        X_train,

        y_train,

        validation_data=(

            X_validation,

            y_validation
        ),

        epochs=EPOCHS,

        batch_size=BATCH_SIZE,

        callbacks=[
            early_stopping
        ],

        verbose=1
    )


    print()
    print(
        "Training completed."
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    validation_predictions = (

        model.predict(
            X_validation,
            verbose=0
        )
        .flatten()
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
    # TEST
    # ========================================================

    test_predictions = (

        model.predict(
            X_test,
            verbose=0
        )
        .flatten()
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

        f"{TARGET}.keras"
    )


    scaler_file = os.path.join(

        MODEL_FOLDER,

        f"{TARGET}_scaler.pkl"
    )


    features_file = os.path.join(

        MODEL_FOLDER,

        f"{TARGET}_features.pkl"
    )


    history_file = os.path.join(

        MODEL_FOLDER,

        f"{TARGET}_history.pkl"
    )


    model.save(
        model_file
    )


    joblib.dump(
        scaler,
        scaler_file
    )


    joblib.dump(
        feature_columns,
        features_file
    )


    joblib.dump(
        history.history,
        history_file
    )


    print()
    print(
        f"Model saved : "
        f"{model_file}"
    )

    print(
        f"Scaler saved : "
        f"{scaler_file}"
    )

    print(
        f"Features saved : "
        f"{features_file}"
    )


    # ========================================================
    # STORE RESULT
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


    # ========================================================
    # CLEAN MEMORY
    # ========================================================

    del (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
        train_df,
        validation_df,
        test_df,
        target_df
    )


# ============================================================
# COMPARISON TABLE
# ============================================================

comparison_df = pd.DataFrame(
    comparison_results
)


# ============================================================
# PRINT TABLE
# ============================================================

print()
print("#" * 70)
print("LSTM COMPARISON TABLE")
print("#" * 70)

print()

print(
    comparison_df.to_string(
        index=False,
        float_format=lambda x:
        f"{x:.6f}"
    )
)


# ============================================================
# SAVE TABLE
# ============================================================

comparison_df.to_csv(

    RESULT_FILE,

    index=False
)


# ============================================================
# FINAL MESSAGE
# ============================================================

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
    "All 8 LSTM models trained successfully."
)
