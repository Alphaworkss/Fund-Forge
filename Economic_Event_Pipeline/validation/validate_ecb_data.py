from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/processed/ecb_events.csv"
)

VALID_CSV_FILE = Path(
    "data/processed/ecb_events_valid.csv"
)

VALID_JSON_FILE = Path(
    "data/processed/ecb_events_valid.json"
)

INVALID_CSV_FILE = Path(
    "data/invalid/invalid_ecb_events.csv"
)


REQUIRED_COLUMNS = [
    "id",
    "source",
    "source_type",
    "source_url",
    "title",
    "event_date",
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
}


ALLOWED_EVENT_TYPES = {
    "ECB Monetary Policy Meeting",
    "ECB Non-Monetary Policy Meeting",
    "ECB General Council Meeting",
    "ECB Governing Council Event",
}


def validate_row(
    row: pd.Series,
) -> list[str]:
    """Validate one ECB record."""

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

    status = row.get("event_status")

    if status not in ALLOWED_STATUSES:
        errors.append("Invalid event_status")

    event_type = row.get("event_type")

    if event_type not in ALLOWED_EVENT_TYPES:
        errors.append("Invalid event_type")

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

    return errors


def validate_ecb_data() -> None:
    """
    Validate ECB data and automatically save
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
    ].duplicated(keep=False)

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
        "========== ECB VALIDATION SUMMARY =========="
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
    validate_ecb_data()