from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


CPI_API_URL = (
    "https://api.bls.gov/publicAPI/v2/timeseries/data/"
)

SOURCE_URL = "https://www.bls.gov/cpi/"

RAW_FILE = Path("data/raw/cpi_raw_response.json")
OUTPUT_FILE = Path("data/processed/cpi_events.csv")


def create_id(year: str, period: str) -> str:
    """
    Create one unique ID for every CPI month.
    """

    value = f"BLS|CPI|{year}|{period}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def safe_float(value) -> float | None:
    """
    Convert API values to float safely.

    BLS may return symbols such as "-", empty text,
    N/A or null when a value is unavailable.
    """

    if value in (
        None,
        "",
        "-",
        "N/A",
        "NA",
        "null",
    ):
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def calculate_previous_value(
    observations: list[dict],
) -> dict[tuple[str, str], float | None]:
    """
    Create a lookup containing the previous month's CPI value.

    The BLS API normally returns newest observations first,
    so observations are sorted chronologically before calculation.
    """

    ordered_observations = sorted(
        observations,
        key=lambda item: (
            int(item.get("year", 0)),
            int(str(item.get("period", "M00"))[1:]),
        ),
    )

    previous_lookup = {}
    previous_value = None

    for observation in ordered_observations:
        year = observation.get("year")
        period = observation.get("period")

        current_value = safe_float(
            observation.get("value")
        )

        previous_lookup[(year, period)] = previous_value

        if current_value is not None:
            previous_value = current_value

    return previous_lookup


def collect_cpi_data() -> pd.DataFrame:
    """
    Collect official CPI observations from the BLS API.
    """

    payload = {
        "seriesid": ["CUUR0000SA0"],
        "startyear": "2023",
        "endyear": "2026",
    }

    response = requests.post(
        CPI_API_URL,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    raw_data = response.json()

    # Save the original API response for debugging.
    RAW_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RAW_FILE.write_text(
        json.dumps(
            raw_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    status = raw_data.get("status")

    if status != "REQUEST_SUCCEEDED":
        message = raw_data.get(
            "message",
            ["Unknown BLS API error"],
        )

        raise ValueError(
            f"BLS API request failed: {message}"
        )

    series_list = (
        raw_data
        .get("Results", {})
        .get("series", [])
    )

    if not series_list:
        raise ValueError(
            "No CPI series was returned by the BLS API."
        )

    ingestion_time = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []

    for series_item in series_list:
        observations = series_item.get("data", [])

        previous_lookup = calculate_previous_value(
            observations
        )

        for observation in observations:
            period = observation.get("period")

            # M13 represents annual average, not a month.
            if period == "M13":
                continue

            if not period or not period.startswith("M"):
                continue

            year = observation.get("year")
            month_name = observation.get("periodName")

            month_number = period[1:]

            actual_value = safe_float(
                observation.get("value")
            )

            previous_value = previous_lookup.get(
                (year, period)
            )

            # The official BLS series provides actual index values.
            # Market forecast values are not available in this API.
            forecast_value = None
            surprise_percentage = None

            event_date = (
                f"{year}-{month_number}-01"
            )

            event_status = (
                "Released"
                if actual_value is not None
                else "Awaiting Actual"
            )

            record = {
                "id": create_id(year, period),

                "source": (
                    "U.S. Bureau of Labor Statistics"
                ),
                "source_type": "Official API",
                "source_url": SOURCE_URL,

                "title": (
                    f"US CPI - {month_name} {year}"
                ),

                "description": (
                    "Consumer Price Index for All Urban "
                    "Consumers, All Items, U.S. city "
                    f"average, for {month_name} {year}."
                ),

                "full_text": (
                    f"CPI-U All Items value for "
                    f"{month_name} {year}: "
                    f"{actual_value}"
                ),

                "event_date": event_date,
                "event_status": event_status,

                "published_time_utc": None,
                "ingestion_time_utc": ingestion_time,

                "country": "United States",
                "region": "North America",
                "language": "en",

                "asset_class": "Multi-Asset",
                "market": "United States",
                "sector": "Macroeconomics",
                "event_type": "CPI Release",

                "previous_value": previous_value,
                "forecast_value": forecast_value,
                "actual_value": actual_value,
                "value_unit": "Index Points",

                "surprise_percentage": (
                    surprise_percentage
                ),

                "importance_score": 90,
                "sentiment_score": None,
                "confidence_score": 0.98,

                "sector_impact": (
                    "Equities, Bonds, Commodities, "
                    "Foreign Exchange, Banking"
                ),

                "historical_impact": (
                    "CPI releases can affect inflation "
                    "expectations, interest-rate outlook, "
                    "USD, bonds, equities and gold."
                ),

                "time_until_event_minutes": None,

                "keywords": (
                    "CPI, inflation, consumer prices, "
                    "BLS, interest rates"
                ),

                "named_entities": (
                    "U.S. Bureau of Labor Statistics"
                ),

                "related_assets": (
                    "USD, Gold, US Treasury Bonds, "
                    "S&P 500"
                ),

                "raw_response": json.dumps(
                    observation,
                    ensure_ascii=False,
                ),
            }

            records.append(record)

    return pd.DataFrame(records)


def validate_basic_cpi_data(
    data: pd.DataFrame,
) -> None:
    """
    Perform basic checks before saving.
    """

    required_columns = [
        "id",
        "source",
        "source_url",
        "title",
        "event_date",
        "ingestion_time_utc",
        "country",
        "event_type",
        "actual_value",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if data.empty:
        raise ValueError(
            "The CPI dataset is empty."
        )

    duplicate_ids = data[
        "id"
    ].duplicated().sum()

    if duplicate_ids > 0:
        raise ValueError(
            f"Duplicate CPI IDs found: {duplicate_ids}"
        )

    invalid_dates = pd.to_datetime(
        data["event_date"],
        errors="coerce",
    ).isna().sum()

    if invalid_dates > 0:
        raise ValueError(
            f"Invalid event dates found: {invalid_dates}"
        )


def main() -> None:
    """
    Run the complete CPI collection process.
    """

    print("Starting CPI data collection...")

    data = collect_cpi_data()

    validate_basic_cpi_data(data)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    json_output_file = OUTPUT_FILE.with_suffix(
        ".json"
    )

    data.to_json(
        json_output_file,
        orient="records",
        indent=2,
        force_ascii=False,
    )

    print("\nCPI collection completed successfully.")
    print("Rows collected:", len(data))

    print("\nCSV output:")
    print(OUTPUT_FILE)

    print("\nJSON output:")
    print(json_output_file)

    print("\nPreview:")
    print(
        data[
            [
                "title",
                "event_date",
                "previous_value",
                "actual_value",
                "event_status",
                "ingestion_time_utc",
            ]
        ].head(10)
    )

    print("\nMissing actual values:")
    print(data["actual_value"].isna().sum())


if __name__ == "__main__":
    try:
        main()

    except requests.RequestException as error:
        print("\nNetwork/API error:")
        print(error)

    except (ValueError, KeyError) as error:
        print("\nData processing error:")
        print(error)

    except Exception as error:
        print("\nUnexpected error:")
        print(error)