from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/budget_events.csv"
)

VALID_CSV_FILE = Path(
    "data/processed/budget_events_valid.csv"
)

VALID_JSON_FILE = Path(
    "data/processed/budget_events_valid.json"
)

INVALID_CSV_FILE = Path(
    "data/invalid/invalid_budget_events.csv"
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
    "fiscal_year",
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
    "Upcoming",
}


ALLOWED_EVENT_TYPES = {
    "Federal Budget Announcement",
}


def validate_row(
    row: pd.Series,
) -> list[str]:
    """Validate one budget record."""

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
        errors.append(
            "Invalid event_date"
        )

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
        errors.append(
            "Invalid source_url"
        )

    if (
        row.get("event_status")
        not in ALLOWED_STATUSES
    ):
        errors.append(
            "Invalid event_status"
        )

    if (
        row.get("event_type")
        not in ALLOWED_EVENT_TYPES
    ):
        errors.append(
            "Invalid event_type"
        )

    if str(
        row.get("country", "")
    ).strip() != "Pakistan":
        errors.append(
            "Country must be Pakistan"
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
            "importance_score must be 0-100"
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
            "confidence_score must be 0-1"
        )

    fiscal_year = str(
        row.get("fiscal_year", "")
    )

    if not fiscal_year.startswith(
        ("2023", "2024", "2025")
    ):
        errors.append(
            "Invalid fiscal_year"
        )

    optional_numeric_columns = [
        "forecast_value",
        "actual_value",
        "surprise_percentage",
        "sentiment_score",
    ]

    for column in optional_numeric_columns:
        value = row.get(column)

        if pd.notna(value):
            converted = pd.to_numeric(
                value,
                errors="coerce",
            )

            if pd.isna(converted):
                errors.append(
                    f"Invalid numeric value: {column}"
                )

    return errors


def validate_budget_data() -> None:
    """
    Validate budget data and automatically save
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
        "========== BUDGET VALIDATION SUMMARY =========="
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
    validate_budget_data()