"""
train_transformer.py

FundForge
Transformer models for MUFAP NAV prediction

Trains Transformer models for:
    NAV_15D
    NAV_30D
    NAV_90D
    NAV_180D
    NAV_270D
    NAV_365D
    NAV_730D
    NAV_1095D

Creates:
    models/MUFAP/transformer_NAV/
    training_results/MUFAP/transformer_NAV_comparison.csv
"""

import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from tensorflow.keras import (
    Model,
    Input
)

from tensorflow.keras.layers import (
    Dense,
    Dropout,
    LayerNormalization,
    MultiHeadAttention,
    Add,
    GlobalAveragePooling1D
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
    "transformer_NAV"
)

RESULT_FOLDER = os.path.join(
    "training_results",
    "MUFAP"
)

RESULT_FILE = os.path.join(
    RESULT_FOLDER,
    "transformer_NAV_comparison.csv"
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

PATIENCE = 5


# ============================================================
# REPRODUCIBILITY
# ============================================================

np.random.seed(42)
tf.random.set_seed(42)


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
print("FundForge - Transformer MUFAP NAV Training")
print("#" * 70)


# ============================================================
# LOAD DATASET
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

df = df.dropna(
    subset=["Validity_Date"]
)

print(
    f"Invalid dates removed : {invalid_dates:,}"
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    ["Fund", "Validity_Date"]
).reset_index(
    drop=True
)


# ============================================================
# SELECT NUMERIC FEATURES
# ============================================================

exclude_columns = [
    "AMC",
    "Fund",
    "Validity_Date",

    "NAV_15D",
    "NAV_30D",
    "NAV_90D",
    "NAV_180D",
    "NAV_270D",
    "NAV_365D",
    "NAV_730D",
    "NAV_1095D"
]


print()
print("Selecting numeric features...")


candidate_features = [
    col
    for col in df.columns
    if col not in exclude_columns
]


numeric_features = []

for col in candidate_features:

    converted = pd.to_numeric(
        df[col],
        errors="coerce"
    )

    if converted.notna().sum() > 0:

        df[col] = converted

        numeric_features.append(col)


feature_columns = numeric_features


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
# CONVERT TARGETS
# ============================================================

for target in TARGETS:

    df[target] = pd.to_numeric(
        df[target],
        errors="coerce"
    )


# ============================================================
# RESULTS
# ============================================================

results = []


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
    # COPY DATA
    # ========================================================

    data = df[
        [
            "Fund",
            "Validity_Date"
        ]
        +
        feature_columns
        +
        [TARGET]
    ].copy()


    # ========================================================
    # REMOVE MISSING TARGET
    # ========================================================

    before = len(data)

    data = data.dropna(
        subset=[TARGET]
    )

    print()
    print(
        f"Rows after target filtering : "
        f"{len(data):,}"
    )


    # ========================================================
    # HANDLE MISSING FEATURES
    # ========================================================

    print(
        "Handling missing feature values..."
    )


    # Remove columns that contain no usable values
    valid_features = [
        col
        for col in feature_columns
        if data[col].notna().sum() > 0
    ]


    # Fill missing values using forward/backward fill
    data[valid_features] = (
        data.groupby("Fund")[valid_features]
        .transform(
            lambda x:
            x.ffill().bfill()
        )
    )


    # Remaining missing values
    remaining_missing = (
        data[valid_features]
        .isna()
        .any(axis=1)
        .sum()
    )


    print(
        f"Remaining rows with missing features : "
        f"{remaining_missing:,}"
    )


    data = data.dropna(
        subset=valid_features
    )


    print(
        f"Final Rows : {len(data):,}"
    )


    if len(data) == 0:

        print(
            f"WARNING: No data available for "
            f"{TARGET}. Skipping."
        )

        continue


    # ========================================================
    # CHRONOLOGICAL SPLIT
    # ========================================================

    print()
    print(
        "Creating chronological split..."
    )


    unique_dates = sorted(
        data["Validity_Date"].unique()
    )


    n_dates = len(unique_dates)


    if n_dates < 10:

        print(
            f"WARNING: Not enough dates for "
            f"{TARGET}. Skipping."
        )

        continue


    train_end_index = int(
        n_dates * 0.60
    )

    validation_end_index = int(
        n_dates * 0.80
    )


    # Make sure indices are valid

    train_end_index = min(
        train_end_index,
        n_dates - 2
    )

    validation_end_index = min(
        validation_end_index,
        n_dates - 1
    )


    train_end_date = unique_dates[
        train_end_index
    ]

    validation_end_date = unique_dates[
        validation_end_index
    ]


    train_df = data[
        data["Validity_Date"] < train_end_date
    ].copy()


    validation_df = data[
        (data["Validity_Date"] >= train_end_date)
        &
        (data["Validity_Date"] < validation_end_date)
    ].copy()


    test_df = data[
        data["Validity_Date"] >= validation_end_date
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
    # SCALE FEATURES
    # ========================================================

    print()
    print(
        "Scaling features..."
    )


    scaler = StandardScaler()


    train_values = train_df[
        valid_features
    ].astype(
        np.float32
    )

    validation_values = validation_df[
        valid_features
    ].astype(
        np.float32
    )

    test_values = test_df[
        valid_features
    ].astype(
        np.float32
    )


    scaler.fit(
        train_values
    )


    train_df.loc[:, valid_features] = (
        scaler.transform(
            train_values
        )
    )

    validation_df.loc[:, valid_features] = (
        scaler.transform(
            validation_values
        )
    )

    test_df.loc[:, valid_features] = (
        scaler.transform(
            test_values
        )
    )


    # ========================================================
    # CREATE SEQUENCES
    # ========================================================

    print()
    print(
        f"Creating {SEQUENCE_LENGTH}-day sequences..."
    )


    def create_sequences(data):

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
                valid_features
            ].values.astype(
                np.float32
            )


            targets = group[
                TARGET
            ].values.astype(
                np.float32
            )


            if len(group) <= SEQUENCE_LENGTH:

                continue


            for i in range(
                SEQUENCE_LENGTH,
                len(group)
            ):

                X.append(
                    values[
                        i - SEQUENCE_LENGTH:i
                    ]
                )

                y.append(
                    targets[i]
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


    X_train, y_train = create_sequences(
        train_df
    )

    X_validation, y_validation = create_sequences(
        validation_df
    )

    X_test, y_test = create_sequences(
        test_df
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


    if len(X_train) == 0:

        print(
            f"WARNING: No training sequences "
            f"for {TARGET}. Skipping."
        )

        continue


    print(
        f"Input shape : "
        f"{X_train.shape}"
    )


    # ========================================================
    # TRANSFORMER BLOCK
    # ========================================================

    def transformer_block(
        inputs,
        head_size=32,
        num_heads=2,
        ff_dim=128,
        dropout=0.1
    ):

        attention_output = MultiHeadAttention(
            num_heads=num_heads,
            key_dim=head_size
        )(
            inputs,
            inputs
        )


        attention_output = Dropout(
            dropout
        )(
            attention_output
        )


        x = Add()([
            inputs,
            attention_output
        ])


        x = LayerNormalization(
            epsilon=1e-6
        )(
            x
        )


        ff = Dense(
            ff_dim,
            activation="relu"
        )(
            x
        )


        ff = Dropout(
            dropout
        )(
            ff
        )


        ff = Dense(
            inputs.shape[-1]
        )(
            ff
        )


        x = Add()([
            x,
            ff
        ])


        return LayerNormalization(
            epsilon=1e-6
        )(
            x
        )


    # ========================================================
    # BUILD TRANSFORMER
    # ========================================================

    print()
    print(
        "Building Transformer model..."
    )


    input_shape = (
        X_train.shape[1],
        X_train.shape[2]
    )


    inputs = Input(
        shape=input_shape
    )


    x = transformer_block(
        inputs
    )


    x = transformer_block(
        x
    )


    x = GlobalAveragePooling1D()(
        x
    )


    x = Dense(
        64,
        activation="relu"
    )(
        x
    )


    x = Dropout(
        0.2
    )(
        x
    )


    x = Dense(
        32,
        activation="relu"
    )(
        x
    )


    outputs = Dense(
        1
    )(
        x
    )


    model = Model(
        inputs,
        outputs
    )


    model.compile(
        optimizer="adam",
        loss="mse"
    )


    model.summary()


    # ========================================================
    # EARLY STOPPING
    # ========================================================

    early_stopping = EarlyStopping(
        monitor="val_loss",
        patience=PATIENCE,
        restore_best_weights=True
    )


    # ========================================================
    # TRAIN
    # ========================================================

    print()
    print(
        "Training Transformer..."
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
    # EVALUATION
    # ========================================================

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


        if np.any(mask):

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
    # VALIDATION
    # ========================================================

    print()
    print(
        "=" * 60
    )

    print(
        f"VALIDATION RESULTS - {TARGET}"
    )

    print(
        "=" * 60
    )


    validation_predictions = model.predict(
        X_validation,
        verbose=0
    ).flatten()


    validation_mae, \
    validation_rmse, \
    validation_mape, \
    validation_r2 = evaluate_model(
        y_validation,
        validation_predictions
    )


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


    # ========================================================
    # TEST
    # ========================================================

    print()
    print(
        "=" * 60
    )

    print(
        f"TEST RESULTS - {TARGET}"
    )

    print(
        "=" * 60
    )


    test_predictions = model.predict(
        X_test,
        verbose=0
    ).flatten()


    test_mae, \
    test_rmse, \
    test_mape, \
    test_r2 = evaluate_model(
        y_test,
        test_predictions
    )


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

    print()
    print(
        "Saving Transformer model..."
    )


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
        valid_features,
        features_file
    )


    joblib.dump(
        history.history,
        history_file
    )


    print()
    print(
        f"Model saved    : {model_file}"
    )

    print(
        f"Scaler saved   : {scaler_file}"
    )

    print(
        f"Features saved : {features_file}"
    )

    print(
        f"History saved  : {history_file}"
    )


    # ========================================================
    # STORE RESULTS
    # ========================================================

    results.append({

        "Target": TARGET,

        "Test_MAE":
            test_mae,

        "Test_RMSE":
            test_rmse,

        "Test_MAPE":
            test_mape,

        "Test_R2":
            test_r2

    })


# ============================================================
# COMPARISON TABLE
# ============================================================

results_df = pd.DataFrame(
    results
)


print()
print("#" * 70)
print("TRANSFORMER COMPARISON TABLE")
print("#" * 70)

print()

print(
    results_df.to_string(
        index=False
    )
)


# ============================================================
# SAVE COMPARISON
# ============================================================

results_df.to_csv(
    RESULT_FILE,
    index=False
)


print()
print(
    "#" * 70
)

print(
    "TRAINING COMPLETED"
)

print(
    "#" * 70
)

print()
print(
    "Comparison table saved to:"
)

print(
    RESULT_FILE
)

print()
print(
    "All Transformer models trained successfully."
)