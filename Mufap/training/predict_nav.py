
"""
predict_nav.py

FundForge
MUFAP NAV Prediction

Uses existing trained models only.

Prediction logic
----------------
LightGBM horizons:
    NAV_15D
    NAV_270D
    NAV_730D

LSTM horizons:
    NAV_30D
    NAV_90D
    NAV_180D
    NAV_365D
    NAV_1095D

For LSTM horizons:
    - If a fund has >= 30 historical rows:
        Existing trained LSTM model is used.
    - If a fund has < 30 historical rows:
        A fallback NAV prediction is generated.
        The LSTM is NOT used.

Fallback:
    Latest available NAV.

This avoids fabricating a 30-row LSTM sequence for funds
that do not have sufficient historical data.

Output:
    predictions/MUFAP/MUFAP_NAV_PREDICTIONS.csv
"""

import os
import warnings

import joblib
import numpy as np
import pandas as pd

from tensorflow.keras.models import load_model


warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

DATA_FILE = os.path.join(
    "training_data",
    "MUFAP_NAV_Features.csv"
)


BEST_MODELS_FILE = os.path.join(
    "training_results",
    "MUFAP",
    "MUFAP_NAV_BEST_MODELS.csv"
)


MODEL_BASE_FOLDER = os.path.join(
    "models",
    "MUFAP"
)


OUTPUT_FOLDER = os.path.join(
    "predictions",
    "MUFAP"
)


OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "MUFAP_NAV_PREDICTIONS.csv"
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


# ------------------------------------------------------------
# LSTM configuration
# ------------------------------------------------------------

SEQUENCE_LENGTH = 30
# Minimum history required before trusting ANY trained model.
# Funds with less history use the latest NAV as fallback.
MIN_MODEL_HISTORY = 30

# LSTM horizons requiring a 30-row sequence

LSTM_HORIZONS = {

    "NAV_30D",
    "NAV_90D",
    "NAV_180D",
    "NAV_365D",
    "NAV_1095D"

}


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print()
print("#" * 70)
print("FundForge - MUFAP NAV Prediction")
print("#" * 70)

print()
print("IMPORTANT:")
print("Existing trained models will be used.")
print("NO models will be retrained.")


# ============================================================
# LOAD DATA
# ============================================================

print()
print("Loading feature dataset...")

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


df = df.dropna(
    subset=["Validity_Date"]
).copy()


# ============================================================
# FUNDID CLEANING
# ============================================================

if "FundID" not in df.columns:

    raise ValueError(
        "FundID column is missing from the feature dataset."
    )


df["FundID"] = (
    df["FundID"]
    .astype(str)
    .str.strip()
)


df = df[
    (df["FundID"] != "")
    & (df["FundID"].str.lower() != "nan")
].copy()


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    [
        "FundID",
        "Validity_Date"
    ]
).reset_index(
    drop=True
)


# ============================================================
# LOAD BEST MODEL TABLE
# ============================================================

print()
print("Loading best model configuration...")

best_models = pd.read_csv(
    BEST_MODELS_FILE
)


print()
print("Best models:")

print(
    best_models[
        [
            "Target",
            "Best_Model"
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# FEATURE COLUMNS
# ============================================================

exclude_columns = [

    "AMC",
    "Fund",
    "FundID",
    "Validity_Date",

    # Identification / descriptive fields
    # are retained only if the trained model
    # explicitly expects them.

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


candidate_features = [

    col

    for col in df.columns

    if col not in exclude_columns
]


# ============================================================
# CONVERT POSSIBLE NUMERIC FEATURES
# ============================================================

for col in candidate_features:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


print()
print(
    f"Candidate Features : "
    f"{len(candidate_features)}"
)


# ============================================================
# FIND CURRENT NAV COLUMN
# ============================================================

possible_nav_columns = [

    "NAV",
    "Net Asset Value",
    "NAV_Value",
    "Current_NAV",
    "Current NAV",
    "NAVValue"
]


current_nav_column = None


for column in possible_nav_columns:

    if column in df.columns:

        current_nav_column = column

        break


if current_nav_column is None:

    raise ValueError(
        "Current NAV column could not be found."
    )


# Make sure NAV is numeric

df[current_nav_column] = pd.to_numeric(
    df[current_nav_column],
    errors="coerce"
)


# ============================================================
# LATEST DATE
# ============================================================

latest_date = df[
    "Validity_Date"
].max()


print()
print(
    f"Latest Dataset Date : "
    f"{latest_date.date()}"
)


# ============================================================
# UNIQUE FUNDIDS
# ============================================================

fund_ids = (

    df[
        "FundID"
    ]
    .dropna()
    .unique()
)


print()
print(
    f"Unique FundIDs : "
    f"{len(fund_ids):,}"
)


# ============================================================
# HELPER: LOAD LIGHTGBM
# ============================================================

def load_lightgbm_model(
    horizon
):

    model_file = os.path.join(

        MODEL_BASE_FOLDER,

        "lightgbm_NAV",

        f"{horizon}.pkl"
    )


    feature_file = os.path.join(

        MODEL_BASE_FOLDER,

        "lightgbm_NAV",

        f"{horizon}_features.pkl"
    )


    if not os.path.exists(model_file):

        raise FileNotFoundError(
            f"LightGBM model not found:\n"
            f"{model_file}"
        )


    if not os.path.exists(feature_file):

        raise FileNotFoundError(
            f"LightGBM feature file not found:\n"
            f"{feature_file}"
        )


    model = joblib.load(
        model_file
    )


    features = joblib.load(
        feature_file
    )


    return (
        model,
        features
    )


# ============================================================
# HELPER: LOAD LSTM
# ============================================================

def load_lstm_model(
    horizon
):

    model_file = os.path.join(

        MODEL_BASE_FOLDER,

        "lstm_NAV",

        f"{horizon}.keras"
    )


    scaler_file = os.path.join(

        MODEL_BASE_FOLDER,

        "lstm_NAV",

        f"{horizon}_scaler.pkl"
    )


    feature_file = os.path.join(

        MODEL_BASE_FOLDER,

        "lstm_NAV",

        f"{horizon}_features.pkl"
    )


    if not os.path.exists(model_file):

        raise FileNotFoundError(
            f"LSTM model not found:\n"
            f"{model_file}"
        )


    if not os.path.exists(scaler_file):

        raise FileNotFoundError(
            f"LSTM scaler not found:\n"
            f"{scaler_file}"
        )


    if not os.path.exists(feature_file):

        raise FileNotFoundError(
            f"LSTM feature file not found:\n"
            f"{feature_file}"
        )


    model = load_model(
        model_file
    )


    scaler = joblib.load(
        scaler_file
    )


    features = joblib.load(
        feature_file
    )


    return (
        model,
        scaler,
        features
    )


# ============================================================
# LOAD ALL EXISTING MODELS ONCE
# ============================================================

print()
print("#" * 70)
print("LOADING EXISTING MODELS")
print("#" * 70)


loaded_models = {}


for target in TARGETS:

    model_row = best_models[
        best_models[
            "Target"
        ] == target
    ]


    if len(model_row) == 0:

        raise ValueError(
            f"No best model found for {target}"
        )


    best_model = str(
        model_row.iloc[0]["Best_Model"]
    ).strip()


    print(
        f"{target:<12} -> "
        f"{best_model}"
    )


    if best_model.lower() == "lightgbm":

        model, features = (
            load_lightgbm_model(
                target
            )
        )


        loaded_models[target] = {

            "type":
                "lightgbm",

            "model":
                model,

            "features":
                features
        }


    elif best_model.lower() == "lstm":

        model, scaler, features = (
            load_lstm_model(
                target
            )
        )


        loaded_models[target] = {

            "type":
                "lstm",

            "model":
                model,

            "scaler":
                scaler,

            "features":
                features
        }


    else:

        raise ValueError(
            f"Unsupported model '{best_model}' "
            f"for {target}"
        )


print()
print(
    f"Models loaded : "
    f"{len(loaded_models)}"
)


# ============================================================
# FALLBACK FUNCTION
# ============================================================

def fallback_prediction(
    fund_df
):
    """
    Fallback for funds with insufficient history.

    Uses the latest valid NAV.

    This is deliberately simple and conservative:
    it does NOT fabricate historical observations
    for the LSTM.
    """

    valid_nav = fund_df[
        current_nav_column
    ].dropna()


    if len(valid_nav) == 0:

        return np.nan


    latest_nav = float(
        valid_nav.iloc[-1]
    )


    if not np.isfinite(latest_nav):

        return np.nan


    if latest_nav <= 0:

        return np.nan


    return latest_nav


# ============================================================
# PREDICTION STORAGE
# ============================================================

prediction_results = []


# ============================================================
# COUNTERS
# ============================================================

processed_funds = 0
skipped_funds = 0

model_prediction_counts = {
    target: 0
    for target in TARGETS
}


fallback_prediction_counts = {
    target: 0
    for target in TARGETS
}


missing_prediction_counts = {
    target: 0
    for target in TARGETS
}


# ============================================================
# GENERATE PREDICTIONS
# ============================================================

print()
print("#" * 70)
print("GENERATING NAV PREDICTIONS")
print("#" * 70)


for fund_index, fund_id in enumerate(
    fund_ids,
    start=1
):

    # --------------------------------------------------------
    # FUND DATA
    # --------------------------------------------------------

    fund_df = df[
        df["FundID"] == fund_id
    ].copy()


    fund_df = fund_df.sort_values(
        "Validity_Date"
    ).reset_index(
        drop=True
    )


    if len(fund_df) == 0:

        skipped_funds += 1

        continue


    processed_funds += 1


    # --------------------------------------------------------
    # LATEST ROW
    # --------------------------------------------------------

    latest_row = fund_df.iloc[-1]


    fund_name = latest_row.get(
        "Fund",
        ""
    )


    category = latest_row.get(
        "Category",
        ""
    )


    history_count = len(
        fund_df
    )


    latest_nav = latest_row[
        current_nav_column
    ]


    # --------------------------------------------------------
    # HEADER FOR FUND
    # --------------------------------------------------------

    print()
    print(
        f"[{fund_index}/{len(fund_ids)}] "
        f"{fund_name}"
    )

    print(
        f"  FundID   : {fund_id}"
    )

    print(
        f"  Category : {category}"
    )

    print(
        f"  History  : {history_count} rows"
    )

    print(
        f"  Latest   : "
        f"{latest_row['Validity_Date'].date()}"
    )

    print(
        f"  NAV      : "
        f"{latest_nav}"
    )


    # --------------------------------------------------------
    # RESULT ROW
    # --------------------------------------------------------

    result = {

        "AMC":
            latest_row.get(
                "AMC",
                ""
            ),

        "FundID":
            fund_id,

        "Fund":
            fund_name,

        "Category":
            category,

        "Latest_Date":
            latest_row[
                "Validity_Date"
            ],

        "Current_NAV":
            latest_nav
    }


    # ========================================================
    # ALL HORIZONS
    # ========================================================

    for target in TARGETS:

        prediction_column = (
            f"Predicted_{target}"
        )


        change_column = (
            f"Change_{target}_Percent"
        )


        method_column = (
            f"Prediction_Method_{target}"
        )


        status_column = (
            f"Prediction_Status_{target}"
        )


        prediction = np.nan


        model_info = (
            loaded_models[target]
        )


        model_type = model_info[
            "type"
        ]
                # ====================================================
        # UNIVERSAL INSUFFICIENT HISTORY CHECK
        # ====================================================
        #
        # Do not allow ANY trained model to predict for a
        # fund with insufficient historical observations.
        #
        # This is especially important for LightGBM because
        # LightGBM does not require a sequence and would
        # otherwise produce a prediction from a single row.
        #

        if history_count < MIN_MODEL_HISTORY:

            prediction = fallback_prediction(
                fund_df
            )

            if pd.isna(prediction):

                result[
                    prediction_column
                ] = np.nan

                result[
                    method_column
                ] = "Unavailable"

                result[
                    status_column
                ] = (
                    f"Insufficient history "
                    f"({history_count} rows) "
                    f"and no valid NAV"
                )

                missing_prediction_counts[
                    target
                ] += 1

                print(
                    f"  {target}: "
                    f"SKIPPED - only "
                    f"{history_count} rows "
                    f"(need {MIN_MODEL_HISTORY})"
                )

            else:

                result[
                    prediction_column
                ] = prediction

                result[
                    method_column
                ] = "Fallback_Latest_NAV"

                result[
                    status_column
                ] = (
                    f"Fallback - only "
                    f"{history_count} rows "
                    f"(need {MIN_MODEL_HISTORY})"
                )

                fallback_prediction_counts[
                    target
                ] += 1

                print(
                    f"  {target}: "
                    f"{prediction:.6f} "
                    f"(fallback - only "
                    f"{history_count} rows)"
                )

            continue


        # ====================================================
        # LIGHTGBM
        # ====================================================

        if model_type == "lightgbm":

            model = model_info[
                "model"
            ]


            features = model_info[
                "features"
            ]


            missing_features = [

                feature

                for feature in features

                if feature not in fund_df.columns
            ]


            if missing_features:

                print(
                    f"  {target}: "
                    f"SKIPPED - missing features"
                )


                result[
                    prediction_column
                ] = np.nan


                result[
                    method_column
                ] = "Unavailable"


                result[
                    status_column
                ] = (
                    "Missing model features"
                )


                missing_prediction_counts[
                    target
                ] += 1


                continue


            try:

                X_latest = (

                    latest_row[
                        features
                    ]
                    .to_frame()
                    .T
                )


                X_latest = X_latest.apply(
                    pd.to_numeric,
                    errors="coerce"
                )


                # Same missing-value handling
                # used for prediction input.

                X_latest = (
                    X_latest
                    .ffill(axis=0)
                    .bfill(axis=0)
                    .fillna(0)
                )


                prediction = model.predict(
                    X_latest
                )[0]


                prediction = float(
                    prediction
                )


                if not np.isfinite(
                    prediction
                ):

                    raise ValueError(
                        "Model returned "
                        "non-finite prediction"
                    )


                result[
                    prediction_column
                ] = prediction


                result[
                    method_column
                ] = "LightGBM"


                result[
                    status_column
                ] = "Model prediction"


                model_prediction_counts[
                    target
                ] += 1


                print(
                    f"  {target}: "
                    f"{prediction:.6f}"
                )


            except Exception as e:

                print(
                    f"  {target}: "
                    f"SKIPPED - "
                    f"{type(e).__name__}: {e}"
                )


                result[
                    prediction_column
                ] = np.nan


                result[
                    method_column
                ] = "Unavailable"


                result[
                    status_column
                ] = (
                    f"Model error: "
                    f"{type(e).__name__}"
                )


                missing_prediction_counts[
                    target
                ] += 1


        # ====================================================
        # LSTM
        # ====================================================

        elif model_type == "lstm":

            # ------------------------------------------------
            # INSUFFICIENT HISTORY
            # ------------------------------------------------

            if history_count < SEQUENCE_LENGTH:

                prediction = (
                    fallback_prediction(
                        fund_df
                    )
                )


                if pd.isna(
                    prediction
                ):

                    result[
                        prediction_column
                    ] = np.nan


                    result[
                        method_column
                    ] = "Unavailable"


                    result[
                        status_column
                    ] = (
                        "Insufficient history "
                        "and no valid NAV"
                    )


                    missing_prediction_counts[
                        target
                    ] += 1


                    print(
                        f"  {target}: "
                        f"SKIPPED - insufficient "
                        f"history and no valid NAV"
                    )


                else:

                    result[
                        prediction_column
                    ] = prediction


                    result[
                        method_column
                    ] = "Fallback_Latest_NAV"


                    result[
                        status_column
                    ] = (
                        f"Fallback - only "
                        f"{history_count} rows "
                        f"(need {SEQUENCE_LENGTH})"
                    )


                    fallback_prediction_counts[
                        target
                    ] += 1


                    print(
                        f"  {target}: "
                        f"{prediction:.6f} "
                        f"(fallback - "
                        f"{history_count} rows)"
                    )


                continue


            # ------------------------------------------------
            # LOAD MODEL INFORMATION
            # ------------------------------------------------

            model = model_info[
                "model"
            ]


            scaler = model_info[
                "scaler"
            ]


            features = model_info[
                "features"
            ]


            # ------------------------------------------------
            # FEATURE CHECK
            # ------------------------------------------------

            missing_features = [

                feature

                for feature in features

                if feature not in fund_df.columns
            ]


            if missing_features:

                # ------------------------------------------------
                # If the fund has enough rows but model features
                # are missing, use fallback as a safe alternative.
                # ------------------------------------------------

                prediction = (
                    fallback_prediction(
                        fund_df
                    )
                )


                if pd.isna(
                    prediction
                ):

                    result[
                        prediction_column
                    ] = np.nan


                    result[
                        method_column
                    ] = "Unavailable"


                    result[
                        status_column
                    ] = (
                        "Missing LSTM features "
                        "and no valid NAV"
                    )


                    missing_prediction_counts[
                        target
                    ] += 1


                    print(
                        f"  {target}: "
                        f"SKIPPED - missing features"
                    )


                else:

                    result[
                        prediction_column
                    ] = prediction


                    result[
                        method_column
                    ] = "Fallback_Latest_NAV"


                    result[
                        status_column
                    ] = (
                        "Fallback - missing "
                        "LSTM features"
                    )


                    fallback_prediction_counts[
                        target
                    ] += 1


                    print(
                        f"  {target}: "
                        f"{prediction:.6f} "
                        f"(fallback - missing features)"
                    )


                continue


            # ------------------------------------------------
            # BUILD 30-ROW SEQUENCE
            # ------------------------------------------------

            try:

                sequence_df = fund_df[
                    features
                ].tail(
                    SEQUENCE_LENGTH
                ).copy()


                sequence_df = sequence_df.apply(

                    pd.to_numeric,

                    errors="coerce"
                )


                # ------------------------------------------------
                # Fill missing values.
                #
                # Do NOT fill the sequence with artificial rows.
                # Only missing feature values inside the existing
                # 30 observations are handled.
                # ------------------------------------------------

                sequence_df = (

                    sequence_df
                    .ffill()
                    .bfill()
                    .fillna(0)
                )


                # ------------------------------------------------
                # SCALE USING SAVED TRAINING SCALER
                # ------------------------------------------------

                scaled_sequence = (
                    scaler.transform(
                        sequence_df
                    )
                )


                X_sequence = np.asarray(

                    scaled_sequence,

                    dtype=np.float32

                ).reshape(

                    1,

                    SEQUENCE_LENGTH,

                    len(features)

                )


                prediction = model.predict(

                    X_sequence,

                    verbose=0

                ).flatten()[0]


                prediction = float(
                    prediction
                )


                if not np.isfinite(
                    prediction
                ):

                    raise ValueError(
                        "LSTM returned "
                        "non-finite prediction"
                    )


                result[
                    prediction_column
                ] = prediction


                result[
                    method_column
                ] = "LSTM"


                result[
                    status_column
                ] = "Model prediction"


                model_prediction_counts[
                    target
                ] += 1


                print(
                    f"  {target}: "
                    f"{prediction:.6f}"
                )


            except Exception as e:

                # ------------------------------------------------
                # Safe fallback if the LSTM cannot process an
                # otherwise sufficiently long fund.
                # ------------------------------------------------

                prediction = (
                    fallback_prediction(
                        fund_df
                    )
                )


                if pd.isna(
                    prediction
                ):

                    result[
                        prediction_column
                    ] = np.nan


                    result[
                        method_column
                    ] = "Unavailable"


                    result[
                        status_column
                    ] = (
                        f"LSTM error: "
                        f"{type(e).__name__}; "
                        f"no valid NAV fallback"
                    )


                    missing_prediction_counts[
                        target
                    ] += 1


                    print(
                        f"  {target}: "
                        f"SKIPPED - "
                        f"{type(e).__name__}: {e}"
                    )


                else:

                    result[
                        prediction_column
                    ] = prediction


                    result[
                        method_column
                    ] = "Fallback_Latest_NAV"


                    result[
                        status_column
                    ] = (
                        f"Fallback after LSTM "
                        f"error: "
                        f"{type(e).__name__}"
                    )


                    fallback_prediction_counts[
                        target
                    ] += 1


                    print(
                        f"  {target}: "
                        f"{prediction:.6f} "
                        f"(fallback after LSTM error)"
                    )


    # ========================================================
    # CALCULATE PERCENT CHANGE
    # ========================================================

    current_nav = result.get(
        "Current_NAV",
        np.nan
    )


    for target in TARGETS:

        prediction_column = (
            f"Predicted_{target}"
        )


        change_column = (
            f"Change_{target}_Percent"
        )


        prediction = result.get(
            prediction_column,
            np.nan
        )


        if (

            pd.isna(prediction)

            or pd.isna(current_nav)

            or current_nav <= 0

        ):

            result[
                change_column
            ] = np.nan

        else:

            result[
                change_column
            ] = (

                (
                    prediction
                    - current_nav
                )
                /
                current_nav
            ) * 100.0


    # ========================================================
    # STORE FUND RESULT
    # ========================================================

    prediction_results.append(
        result
    )


# ============================================================
# CREATE FINAL DATAFRAME
# ============================================================

predictions_df = pd.DataFrame(
    prediction_results
)


# ============================================================
# SORT RESULTS
# ============================================================

if not predictions_df.empty:

    sort_columns = [

        column

        for column in [
            "AMC",
            "Fund",
            "FundID"
        ]

        if column in predictions_df.columns
    ]


    if sort_columns:

        predictions_df = (
            predictions_df
            .sort_values(sort_columns)
            .reset_index(drop=True)
        )


# ============================================================
# SAVE CSV
# ============================================================

predictions_df.to_csv(

    OUTPUT_FILE,

    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("#" * 70)
print("PREDICTION SUMMARY")
print("#" * 70)

print()

print(
    f"FundIDs processed : "
    f"{processed_funds}"
)

print(
    f"FundIDs skipped   : "
    f"{skipped_funds}"
)


print()
print("Predictions by horizon:")


total_predictions = 0


for target in TARGETS:

    model_count = (
        model_prediction_counts[
            target
        ]
    )


    fallback_count = (
        fallback_prediction_counts[
            target
        ]
    )


    missing_count = (
        missing_prediction_counts[
            target
        ]
    )


    total_count = (
        model_count
        + fallback_count
    )


    total_predictions += (
        total_count
    )


    print(

        f"{target:<12} "

        f"Model: {model_count:4d} | "

        f"Fallback: {fallback_count:4d} | "

        f"Missing: {missing_count:4d}"

    )


print()
print(
    f"Total predictions : "
    f"{total_predictions:,}"
)


print(
    f"Expected maximum : "
    f"{processed_funds * len(TARGETS):,}"
)


print(
    f"Output rows       : "
    f"{len(predictions_df):,}"
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print()
print(
    "Existing trained models were used."
)

print(
    "No models were retrained."
)

print()
print(
    "Fallback policy:"
)

print(
    "LSTM horizons with insufficient "
    "history use the latest available NAV."
)

print()
print(
    "Prediction file saved to:"
)

print(
    OUTPUT_FILE
)

print()
print("#" * 70)
print("PREDICTION COMPLETED")
print("#" * 70)
print()
