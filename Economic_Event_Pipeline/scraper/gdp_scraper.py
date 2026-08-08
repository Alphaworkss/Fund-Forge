from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


API_URL = "https://apps.bea.gov/api/data/"

SOURCE_URL = (
    "https://www.bea.gov/data/gdp/"
    "gross-domestic-product"
)

# Paste your BEA API key between the quotation marks.
BEA_API_KEY = "40653C96-25F0-416E-B135-A1CF872D4774"

RAW_FILE = Path(
    "data/raw/gdp_raw_response.json"
)

CSV_OUTPUT_FILE = Path(
    "data/processed/gdp_events.csv"
)

JSON_OUTPUT_FILE = Path(
    "data/processed/gdp_events.json"
)


def create_id(time_period: str) -> str:
    """Create a stable unique ID for each GDP quarter."""

    value = f"BEA|GDP|{time_period}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def safe_float(value) -> float | None:
    """Convert BEA data values safely into numbers."""

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
        cleaned_value = str(value).replace(",", "").strip()
        return float(cleaned_value)

    except (TypeError, ValueError):
        return None


def quarter_end_date(
    time_period: str,
) -> str | None:
    """
    Convert 2023Q1 into the quarter-end reference date.
    """

    if len(time_period) != 6 or "Q" not in time_period:
        return None

    year = time_period[:4]
    quarter = time_period[-1]

    quarter_dates = {
        "1": f"{year}-03-31",
        "2": f"{year}-06-30",
        "3": f"{year}-09-30",
        "4": f"{year}-12-31",
    }

    return quarter_dates.get(quarter)


def collect_gdp_data() -> pd.DataFrame:
    """Collect quarterly real GDP growth data from BEA."""

    if (
        not BEA_API_KEY
        or BEA_API_KEY == "PASTE_YOUR_BEA_API_KEY_HERE"
    ):
        raise ValueError(
            "Please paste your BEA API key "
            "inside BEA_API_KEY."
        )

    parameters = {
        "UserID": BEA_API_KEY,
        "method": "GetData",
        "DataSetName": "NIPA",
        "TableName": "T10101",
        "Frequency": "Q",
        "Year": "2023,2024,2025,2026",
        "ResultFormat": "JSON",
    }

    response = requests.get(
        API_URL,
        params=parameters,
        timeout=60,
    )

    response.raise_for_status()

    raw_data = response.json()

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

    results = (
        raw_data
        .get("BEAAPI", {})
        .get("Results", {})
    )

    if "Error" in results:
        raise ValueError(
            f"BEA API error: {results['Error']}"
        )

    api_rows = results.get("Data", [])

    if not api_rows:
        raise ValueError(
            "No GDP records were returned by BEA."
        )

    # Line 1 of table T10101 represents real GDP.
    gdp_rows = [
        row
        for row in api_rows
        if str(row.get("LineNumber")) == "1"
        and "Q" in str(row.get("TimePeriod", ""))
    ]

    gdp_rows.sort(
        key=lambda row: row.get("TimePeriod", "")
    )

    ingestion_time = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []

    previous_value = None

    for row in gdp_rows:
        time_period = row.get("TimePeriod")
        actual_value = safe_float(
            row.get("DataValue")
        )

        event_date = quarter_end_date(
            time_period
        )

        event_status = (
            "Released"
            if actual_value is not None
            else "Missing Official Value"
        )

        record = {
            "id": create_id(time_period),

            "source": (
                "U.S. Bureau of Economic Analysis"
            ),

            "source_type": "Official API",

            "source_url": SOURCE_URL,

            "title": (
                f"US Real GDP Growth - {time_period}"
            ),

            "description": (
                "Quarterly percentage change in "
                "real gross domestic product "
                "published by the U.S. Bureau "
                "of Economic Analysis."
            ),

            "full_text": (
                f"Real GDP growth for {time_period}: "
                f"{actual_value} percent."
            ),

            # This is the quarter reference date,
            # not the publication date.
            "event_date": event_date,

            "reference_period": time_period,

            "event_status": event_status,

            # Exact release date can later be added
            # from the BEA release calendar.
            "published_time_utc": None,

            "ingestion_time_utc": ingestion_time,

            "country": "United States",
            "region": "North America",
            "language": "en",

            "asset_class": "Multi-Asset",
            "market": "United States",
            "sector": "Macroeconomics",
            "event_type": "GDP Release",

            "previous_value": previous_value,
            "forecast_value": None,
            "actual_value": actual_value,

            "value_unit": "Percent Annual Rate",

            "surprise_percentage": None,

            "importance_score": 95,
            "sentiment_score": None,
            "confidence_score": 0.98,

            "sector_impact": (
                "Equities, Bonds, Banking, "
                "Commodities, Foreign Exchange"
            ),

            "historical_impact": (
                "GDP releases may affect economic "
                "growth expectations, interest-rate "
                "expectations, USD, bonds, equities "
                "and commodities."
            ),

            "time_until_event_minutes": None,

            "keywords": (
                "GDP, economic growth, real GDP, "
                "BEA, economy"
            ),

            "named_entities": (
                "U.S. Bureau of Economic Analysis"
            ),

            "related_assets": (
                "USD, Gold, US Treasury Bonds, "
                "S&P 500"
            ),

            "raw_response": json.dumps(
                row,
                ensure_ascii=False,
            ),
        }

        records.append(record)

        if actual_value is not None:
            previous_value = actual_value

    return pd.DataFrame(records)


def main() -> None:
    """Run the GDP collection process."""

    print("Starting GDP data collection...")

    data = collect_gdp_data()

    CSV_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        CSV_OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    data.to_json(
        JSON_OUTPUT_FILE,
        orient="records",
        indent=2,
        force_ascii=False,
    )

    print(
        "\nGDP collection completed successfully."
    )

    print("Rows collected:", len(data))

    print("\nCSV output:")
    print(CSV_OUTPUT_FILE)

    print("\nJSON output:")
    print(JSON_OUTPUT_FILE)

    print("\nPreview:")

    preview_columns = [
        "title",
        "event_date",
        "reference_period",
        "previous_value",
        "actual_value",
        "event_status",
        "ingestion_time_utc",
    ]

    print(
        data[preview_columns]
        .tail(12)
        .to_string(index=False)
    )


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