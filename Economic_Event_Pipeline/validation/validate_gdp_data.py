from pathlib import Path
import pandas as pd


INPUT_FILE = Path(
    "data/processed/gdp_events.csv"
)

VALID_CSV_FILE = Path(
    "data/processed/gdp_events_valid.csv"
)

VALID_JSON_FILE = Path(
    "data/processed/gdp_events_valid.json"
)

INVALID_CSV_FILE = Path(
    "data/invalid/invalid_gdp_events.csv"
)


REQUIRED_COLUMNS = [
    "id",
    "source",
    "source_type",
    "source_url",
    "title",
    "event_date",
    "reference_period",
    "event_status",
    "ingestion_time_utc",
    "country",
    "event_type",
    "actual_value",
    "importance_score",
    "confidence_score",
    "raw_response",
]


ALLOWED_STATUSES = {
    "Released",
    "Missing Official Value",
}


def validate_row(row):
    errors = []

    for column in REQUIRED_COLUMNS:

        value = row.get(column)

        if pd.isna(value) or str(value).strip() == "":
            errors.append(
                f"Missing required value: {column}"
            )

    event_date = pd.to_datetime(
        row.get("event_date"),
        errors="coerce",
    )

    if pd.isna(event_date):
        errors.append("Invalid event_date")

    ingestion_time = pd.to_datetime(
        row.get("ingestion_time_utc"),
        utc=True,
        errors="coerce",
    )

    if pd.isna(ingestion_time):
        errors.append(
            "Invalid ingestion_time_utc"
        )

    actual_value = pd.to_numeric(
        row.get("actual_value"),
        errors="coerce",
    )

    if pd.isna(actual_value):
        errors.append(
            "Missing or invalid actual_value"
        )

    importance = pd.to_numeric(
        row.get("importance_score"),
        errors="coerce",
    )

    if (
        pd.isna(importance)
        or not 0 <= importance <= 100
    ):
        errors.append(
            "importance_score must be between 0 and 100"
        )

    confidence = pd.to_numeric(
        row.get("confidence_score"),
        errors="coerce",
    )

    if (
        pd.isna(confidence)
        or not 0 <= confidence <= 1
    ):
        errors.append(
            "confidence_score must be between 0 and 1"
        )

    source_url = str(
        row.get("source_url", "")
    )

    if not source_url.startswith(
        ("https://", "http://")
    ):
        errors.append("Invalid source_url")

    status = row.get("event_status")

    if status not in ALLOWED_STATUSES:
        errors.append("Invalid event_status")

    reference_period = str(
        row.get("reference_period", "")
    )

    if (
        len(reference_period) != 6
        or "Q" not in reference_period
    ):
        errors.append(
            "Invalid reference_period"
        )

    return errors


def validate_gdp_data():

    if not INPUT_FILE.exists():
        print("Input file not found:")
        print(INPUT_FILE)
        return

    data = pd.read_csv(INPUT_FILE)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        print(
            "Missing required columns:"
        )
        print(missing_columns)
        return

    VALID_CSV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    INVALID_CSV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    duplicate_ids = data[
        "id"
    ].duplicated(keep=False)

    valid_rows = []
    invalid_rows = []

    for index, row in data.iterrows():

        errors = validate_row(row)

        if duplicate_ids.iloc[index]:
            errors.append(
                "Duplicate ID"
            )

        record = row.to_dict()

        if errors:

            record[
                "validation_errors"
            ] = " | ".join(errors)

            invalid_rows.append(record)

        else:
            valid_rows.append(record)

    valid_data = pd.DataFrame(
        valid_rows
    )

    invalid_data = pd.DataFrame(
        invalid_rows
    )

    valid_data.to_csv(
        VALID_CSV_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    valid_data.to_json(
        VALID_JSON_FILE,
        orient="records",
        indent=2,
        force_ascii=False,
    )

    invalid_data.to_csv(
        INVALID_CSV_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n========== GDP VALIDATION SUMMARY =========="
    )

    print(
        "Total rows:",
        len(data)
    )

    print(
        "Valid rows:",
        len(valid_data)
    )

    print(
        "Invalid rows:",
        len(invalid_data)
    )

    print("\nValid CSV:")
    print(
        VALID_CSV_FILE
    )

    print("\nValid JSON:")
    print(
        VALID_JSON_FILE
    )

    print("\nInvalid CSV:")
    print(
        INVALID_CSV_FILE
    )

    if len(invalid_data) == 0:
        print(
            "\nOVERALL STATUS: PASSED"
        )
    else:
        print(
            "\nSTATUS: COMPLETED WITH INVALID RECORDS QUARANTINED"
        )


if __name__ == "__main__":
    validate_gdp_data()