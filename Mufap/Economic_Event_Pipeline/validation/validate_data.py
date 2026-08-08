from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/fomc_events_2023_cleaned.csv"
)

VALID_CSV_FILE = Path(
    "data/processed/fomc_events_2023_valid.csv"
)

VALID_JSON_FILE = Path(
    "data/processed/fomc_events_2023_valid.json"
)

INVALID_FILE = Path(
    "data/invalid/invalid_fomc_events.csv"
)


REQUIRED_COLUMNS = [
    "id",
    "source",
    "source_type",
    "source_url",
    "title",
    "event_start_date",
    "event_end_date",
    "event_status",
    "ingestion_time_utc",
    "country",
    "event_type",
    "importance_score",
    "confidence_score",
    "raw_response",
]


ALLOWED_STATUSES = {
    "Upcoming",
    "Released",
    "Awaiting Actual",
}


def validate_row(row: pd.Series) -> list[str]:
    """Return all validation errors for one row."""

    errors = []

    for column in REQUIRED_COLUMNS:
        value = row.get(column)

        if pd.isna(value) or str(value).strip() == "":
            errors.append(
                f"Missing required value: {column}"
            )

    start_date = pd.to_datetime(
        row.get("event_start_date"),
        errors="coerce",
    )

    end_date = pd.to_datetime(
        row.get("event_end_date"),
        errors="coerce",
    )

    ingestion_time = pd.to_datetime(
        row.get("ingestion_time_utc"),
        utc=True,
        errors="coerce",
    )

    if pd.isna(start_date):
        errors.append("Invalid event_start_date")

    if pd.isna(end_date):
        errors.append("Invalid event_end_date")

    if pd.isna(ingestion_time):
        errors.append("Invalid ingestion_time_utc")

    if (
        not pd.isna(start_date)
        and not pd.isna(end_date)
        and end_date < start_date
    ):
        errors.append(
            "event_end_date is earlier than event_start_date"
        )

    importance = pd.to_numeric(
        row.get("importance_score"),
        errors="coerce",
    )

    if pd.isna(importance) or not 0 <= importance <= 100:
        errors.append(
            "importance_score must be between 0 and 100"
        )

    confidence = pd.to_numeric(
        row.get("confidence_score"),
        errors="coerce",
    )

    if pd.isna(confidence) or not 0 <= confidence <= 1:
        errors.append(
            "confidence_score must be between 0 and 1"
        )

    source_url = str(row.get("source_url", ""))

    if not source_url.startswith(
        ("http://", "https://")
    ):
        errors.append("Invalid source_url")

    if row.get("event_status") not in ALLOWED_STATUSES:
        errors.append("Invalid event_status")

    return errors


def validate_dataset() -> None:
    """Validate all rows and save valid/invalid outputs."""

    if not INPUT_FILE.exists():
        print("Input file not found:")
        print(INPUT_FILE)
        return

    VALID_CSV_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    INVALID_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    duplicate_ids = data["id"].duplicated(
        keep=False
    )

    valid_rows = []
    invalid_rows = []

    for index, row in data.iterrows():

        errors = validate_row(row)

        if duplicate_ids.iloc[index]:
            errors.append("Duplicate ID")

        row_dictionary = row.to_dict()

        if errors:
            row_dictionary[
                "validation_errors"
            ] = " | ".join(errors)

            invalid_rows.append(row_dictionary)

        else:
            valid_rows.append(row_dictionary)

    valid_data = pd.DataFrame(valid_rows)
    invalid_data = pd.DataFrame(invalid_rows)

    valid_data.to_csv(
        VALID_CSV_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    valid_data.to_json(
        VALID_JSON_FILE,
        orient="records",
        indent=2,
        date_format="iso",
    )

    invalid_data.to_csv(
        INVALID_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("========== VALIDATION SUMMARY ==========")
    print("Total rows:", len(data))
    print("Valid rows:", len(valid_data))
    print("Invalid rows:", len(invalid_data))

    print("\nValid CSV:")
    print(VALID_CSV_FILE)

    print("\nValid JSON:")
    print(VALID_JSON_FILE)

    print("\nInvalid records:")
    print(INVALID_FILE)

    if len(invalid_data) == 0:
        print("\nOVERALL STATUS: PASSED")
    else:
        print("\nOVERALL STATUS: FAILED")


if __name__ == "__main__":
    validate_dataset()