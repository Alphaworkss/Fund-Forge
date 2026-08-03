from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_FOLDER = (
    PROJECT_ROOT / "data" / "processed"
)

DATABASE_FOLDER = (
    PROJECT_ROOT / "data" / "database"
)

DATABASE_FILE = (
    DATABASE_FOLDER / "economic_events.db"
)


# These columns should be numeric wherever available.
NUMERIC_COLUMNS = [
    "previous_value",
    "forecast_value",
    "actual_value",
    "surprise_value",
    "surprise_percentage",
    "importance",
    "importance_score",
    "sentiment_score",
    "confidence_score",
    "time_until_event",
    "time_until_event_minutes",
    "employment_level",
    "document_count",
]


def normalize_column_name(column: str) -> str:
    """
    Convert column names into a consistent SQLite-friendly format.
    """

    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def find_valid_csv_files() -> list[Path]:
    """
    Find all validated CSV files from the processed folder.
    """

    files = sorted(
        PROCESSED_FOLDER.glob("*_valid.csv")
    )

    return [
        file
        for file in files
        if file.is_file()
    ]


def load_valid_datasets(
    files: list[Path],
) -> pd.DataFrame:
    """
    Load all valid CSV datasets and combine them
    using a union of their columns.
    """

    datasets = []

    for file in files:
        print(f"Loading: {file.name}")

        try:
            data = pd.read_csv(
                file,
                encoding="utf-8-sig",
            )

        except UnicodeDecodeError:
            data = pd.read_csv(
                file,
                encoding="utf-8",
            )

        if data.empty:
            print(
                f"Skipped empty file: {file.name}"
            )
            continue

        # Normalize all column names.
        data.columns = [
            normalize_column_name(column)
            for column in data.columns
        ]

        # Record the original validated file.
        data["source_file"] = file.name

        # Record when this database load occurred.
        data["database_loaded_time_utc"] = (
            datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        )

        datasets.append(data)

    if not datasets:
        raise ValueError(
            "No non-empty valid CSV files were found."
        )

    # Different sources can have different columns.
    # Pandas automatically creates the union of all columns.
    combined_data = pd.concat(
        datasets,
        ignore_index=True,
        sort=False,
    )

    return combined_data


def clean_combined_data(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Perform final cleaning before saving to SQLite.
    """

    cleaned = data.copy()

    # Convert selected fields to numbers.
    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(
                cleaned[column],
                errors="coerce",
            )

    # Remove rows without an ID.
    if "id" in cleaned.columns:
        cleaned["id"] = (
            cleaned["id"]
            .astype("string")
            .str.strip()
        )

        cleaned = cleaned[
            cleaned["id"].notna()
            & (cleaned["id"] != "")
        ]

        # Keep the newest occurrence of a duplicate ID.
        cleaned = cleaned.drop_duplicates(
            subset=["id"],
            keep="last",
        )

    # Normalize blank strings to NULL.
    cleaned = cleaned.replace(
        {
            "": None,
            "nan": None,
            "NaN": None,
            "None": None,
        }
    )

    return cleaned.reset_index(drop=True)


def save_summary_table(
    connection: sqlite3.Connection,
    data: pd.DataFrame,
) -> None:
    """
    Create a table showing row counts by source and event type.
    """

    summary_parts = []

    if "source" in data.columns:
        source_summary = (
            data.groupby(
                "source",
                dropna=False,
            )
            .size()
            .reset_index(
                name="record_count"
            )
        )

        source_summary[
            "summary_type"
        ] = "source"

        source_summary = (
            source_summary.rename(
                columns={
                    "source": "summary_value"
                }
            )
        )

        summary_parts.append(
            source_summary[
                [
                    "summary_type",
                    "summary_value",
                    "record_count",
                ]
            ]
        )

    if "event_type" in data.columns:
        event_summary = (
            data.groupby(
                "event_type",
                dropna=False,
            )
            .size()
            .reset_index(
                name="record_count"
            )
        )

        event_summary[
            "summary_type"
        ] = "event_type"

        event_summary = (
            event_summary.rename(
                columns={
                    "event_type": "summary_value"
                }
            )
        )

        summary_parts.append(
            event_summary[
                [
                    "summary_type",
                    "summary_value",
                    "record_count",
                ]
            ]
        )

    if summary_parts:
        summary_data = pd.concat(
            summary_parts,
            ignore_index=True,
        )

        summary_data.to_sql(
            "dataset_summary",
            connection,
            if_exists="replace",
            index=False,
        )


def save_pipeline_run(
    connection: sqlite3.Connection,
    total_files: int,
    total_rows: int,
) -> None:
    """
    Save one database-loading run in an audit table.
    """

    run_data = pd.DataFrame(
        [
            {
                "run_time_utc": (
                    datetime.now(
                        timezone.utc
                    ).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                ),
                "valid_files_loaded": total_files,
                "records_loaded": total_rows,
                "status": "SUCCESS",
            }
        ]
    )

    run_data.to_sql(
        "pipeline_runs",
        connection,
        if_exists="append",
        index=False,
    )


def save_to_database(
    data: pd.DataFrame,
    total_files: int,
) -> None:
    """
    Save all combined records to the SQLite database.
    """

    DATABASE_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        DATABASE_FILE
    ) as connection:

        # Save the latest combined validated dataset.
        data.to_sql(
            "economic_events",
            connection,
            if_exists="replace",
            index=False,
        )

        # Add an index for faster ID searches.
        if "id" in data.columns:
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_economic_events_id
                ON economic_events(id)
                """
            )

        # Add indexes useful for prediction/dashboard queries.
        if "event_date" in data.columns:
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_economic_events_date
                ON economic_events(event_date)
                """
            )

        if "event_type" in data.columns:
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_economic_events_type
                ON economic_events(event_type)
                """
            )

        if "country" in data.columns:
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_economic_events_country
                ON economic_events(country)
                """
            )

        save_summary_table(
            connection,
            data,
        )

        save_pipeline_run(
            connection,
            total_files=total_files,
            total_rows=len(data),
        )

        connection.commit()


def show_database_summary() -> None:
    """
    Display tables and record counts after saving.
    """

    with sqlite3.connect(
        DATABASE_FILE
    ) as connection:

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """,
            connection,
        )

        total_records = pd.read_sql_query(
            """
            SELECT COUNT(*) AS total_records
            FROM economic_events
            """,
            connection,
        )

        print("\nSQLite tables:")
        print(
            tables.to_string(
                index=False
            )
        )

        print("\nRecords in economic_events:")
        print(
            total_records.to_string(
                index=False
            )
        )

        if "dataset_summary" in tables[
            "name"
        ].tolist():
            source_counts = pd.read_sql_query(
                """
                SELECT
                    summary_value AS source,
                    record_count
                FROM dataset_summary
                WHERE summary_type = 'source'
                ORDER BY record_count DESC
                """,
                connection,
            )

            print("\nRecords by source:")
            print(
                source_counts.to_string(
                    index=False
                )
            )


def main() -> None:
    """
    Load all validated files into SQLite.
    """

    print("=" * 60)
    print("SAVING VALIDATED DATA TO SQLITE")
    print("=" * 60)

    valid_files = find_valid_csv_files()

    if not valid_files:
        print(
            "No *_valid.csv files were found in:"
        )
        print(PROCESSED_FOLDER)
        return

    print(
        f"\nValid files found: {len(valid_files)}"
    )

    for file in valid_files:
        print(f"- {file.name}")

    combined_data = load_valid_datasets(
        valid_files
    )

    cleaned_data = clean_combined_data(
        combined_data
    )

    save_to_database(
        cleaned_data,
        total_files=len(valid_files),
    )

    print("\nSQLite database saved successfully:")
    print(DATABASE_FILE)

    print(
        "\nTotal valid records saved:",
        len(cleaned_data),
    )

    show_database_summary()

    print("\nDATABASE PROCESS COMPLETED")


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print("\nDatabase process failed:")
        print(type(error).__name__)
        print(error)