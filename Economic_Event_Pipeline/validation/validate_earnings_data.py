from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/earnings_events.csv"
)

VALID_CSV_FILE = Path(
    "data/processed/earnings_events_valid.csv"
)

VALID_JSON_FILE = Path(
    "data/processed/earnings_events_valid.json"
)

INVALID_CSV_FILE = Path(
    "data/invalid/invalid_earnings_events.csv"
)


REQUIRED_COLUMNS = [
    "id",
    "source",
    "source_type",
    "source_url",
    "title",
    "description",
    "full_text",
    "event_name",
    "event_date",
    "event_status",
    "published_time_utc",
    "ingestion_time_utc",
    "country",
    "region",
    "language",
    "asset_class",
    "market",
    "sector",
    "event_type",
    "forecast_value",
    "actual_value",
    "surprise_percentage",
    "importance_score",
    "sector_impact",
    "affected_assets",
    "historical_impact",
    "keywords",
    "named_entities",
    "related_assets",
    "confidence_score",
    "raw_response",
]


ALLOWED_STATUSES = {
    "Released",
    "Missing Official Value",
}


ALLOWED_EVENT_TYPES = {
    "Quarterly Earnings Release",
}


def validate_row(
    row: pd.Series,
) -> list[str]:
    """Validate one earnings event."""

    errors = []

    for column in REQUIRED_COLUMNS:
        value = row.get(column)

        if (
            pd.isna(value)
            or str(value).strip() == ""
        ):
            errors.append(
                f"Missing required value: {column}"
            )

    event_date = pd.to_datetime(
        row.get("event_date"),
        errors="coerce",
    )

    if pd.isna(event_date):
        errors.append("Invalid event_date")

    published_time = pd.to_datetime(
        row.get("published_time_utc"),
        utc=True,
        errors="coerce",
    )

    if pd.isna(published_time):
        errors.append(
            "Invalid published_time_utc"
        )

    ingestion_time = pd.to_datetime(
        row.get("ingestion_time_utc"),
        utc=True,
        errors="coerce",
    )

    if pd.isna(ingestion_time):
        errors.append(
            "Invalid ingestion_time_utc"
        )

    source_url = str(
        row.get("source_url", "")
    )

    if not source_url.startswith(
        ("https://", "http://")
    ):
        errors.append("Invalid source_url")

    if (
        row.get("event_status")
        not in ALLOWED_STATUSES
    ):
        errors.append("Invalid event_status")

    if (
        row.get("event_type")
        not in ALLOWED_EVENT_TYPES
    ):
        errors.append("Invalid event_type")

    numeric_required = [
        "forecast_value",
        "actual_value",
        "surprise_percentage",
        "importance_score",
        "confidence_score",
    ]

    for column in numeric_required:
        numeric_value = pd.to_numeric(
            row.get(column),
            errors="coerce",
        )

        if pd.isna(numeric_value):
            errors.append(
                f"Missing or invalid numeric value: {column}"
            )

    importance = pd.to_numeric(
        row.get("importance_score"),
        errors="coerce",
    )

    if (
        not pd.isna(importance)
        and not 0 <= importance <= 100
    ):
        errors.append(
            "importance_score must be 0-100"
        )

    confidence = pd.to_numeric(
        row.get("confidence_score"),
        errors="coerce",
    )

    if (
        not pd.isna(confidence)
        and not 0 <= confidence <= 1
    ):
        errors.append(
            "confidence_score must be 0-1"
        )

    return errors


def validate_earnings_data() -> None:
    """
    Validate earnings data and automatically save
    valid CSV, valid JSON and invalid CSV.
    """

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
        print("Missing required columns:")
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
    ].duplicated(
        keep=False
    )

    valid_rows = []
    invalid_rows = []

    for index, row in data.iterrows():

        errors = validate_row(row)

        if duplicate_ids.iloc[index]:
            errors.append("Duplicate ID")

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
        "========== EARNINGS VALIDATION SUMMARY =========="
    )

    print("Total rows:", len(data))
    print("Valid rows:", len(valid_data))
    print("Invalid rows:", len(invalid_data))

    print("\nValid CSV:")
    print(VALID_CSV_FILE)

    print("\nValid JSON:")
    print(VALID_JSON_FILE)

    print("\nInvalid CSV:")
    print(INVALID_CSV_FILE)

    if len(invalid_data) == 0:
        print("\nOVERALL STATUS: PASSED")

    else:
        print(
            "\nSTATUS: COMPLETED WITH "
            "INVALID RECORDS QUARANTINED"
        )


if __name__ == "__main__":
    validate_earnings_data()