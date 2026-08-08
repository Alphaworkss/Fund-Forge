from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


API_URL = (
    "https://api.bls.gov/publicAPI/v2/timeseries/data/"
)

SOURCE_URL = "https://www.bls.gov/ces/"

SERIES_ID = "CES0000000001"

RAW_FILE = Path(
    "data/raw/nfp_raw_response.json"
)

CSV_OUTPUT_FILE = Path(
    "data/processed/nfp_events.csv"
)

JSON_OUTPUT_FILE = Path(
    "data/processed/nfp_events.json"
)


def create_id(year: str, period: str) -> str:
    """Create a unique and repeatable ID."""

    value = f"BLS|NFP|{year}|{period}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def safe_float(value) -> float | None:
    """Convert values safely to float."""

    if value in {
        None,
        "",
        "-",
        "N/A",
        "NA",
        "null",
    }:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def collect_nfp_data() -> pd.DataFrame:
    """
    Download total nonfarm employment and calculate
    monthly payroll changes.
    """

    payload = {
        "seriesid": [SERIES_ID],
        "startyear": "2023",
        "endyear": "2026",
    }

    response = requests.post(
        API_URL,
        json=payload,
        timeout=30,
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

    api_status = raw_data.get("status")

    if api_status != "REQUEST_SUCCEEDED":
        raise ValueError(
            "BLS API request failed: "
            f"{raw_data.get('message')}"
        )

    series_list = (
        raw_data
        .get("Results", {})
        .get("series", [])
    )

    if not series_list:
        raise ValueError(
            "No NFP series returned by the BLS API."
        )

    observations = series_list[0].get(
        "data",
        [],
    )

    monthly_observations = []

    for observation in observations:
        period = observation.get("period")

        # M13 is an annual-average record.
        if period == "M13":
            continue

        if (
            not period
            or not period.startswith("M")
        ):
            continue

        employment_level = safe_float(
            observation.get("value")
        )

        monthly_observations.append(
            {
                "year": observation.get("year"),
                "period": period,
                "period_name": observation.get(
                    "periodName"
                ),
                "employment_level": (
                    employment_level
                ),
                "raw_observation": observation,
            }
        )

    # Oldest to newest for monthly change calculation.
    monthly_observations.sort(
        key=lambda item: (
            int(item["year"]),
            int(item["period"][1:]),
        )
    )

    ingestion_time = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []

    previous_employment_level = None
    previous_payroll_change = None

    for observation in monthly_observations:

        year = observation["year"]
        period = observation["period"]
        month_name = observation["period_name"]

        employment_level = observation[
            "employment_level"
        ]

        payroll_change = None

        if (
            employment_level is not None
            and previous_employment_level is not None
        ):
            payroll_change = round(
                employment_level
                - previous_employment_level,
                3,
            )

        event_status = (
            "Released"
            if payroll_change is not None
            else "Missing Previous Observation"
        )

        month_number = period[1:]

        event_date = (
            f"{year}-{month_number}-01"
        )

        record = {
            "id": create_id(
                year,
                period,
            ),

            "source": (
                "U.S. Bureau of Labor Statistics"
            ),

            "source_type": "Official API",

            "source_url": SOURCE_URL,

            "title": (
                "US Non-Farm Payrolls - "
                f"{month_name} {year}"
            ),

            "description": (
                "Monthly change in total nonfarm "
                "payroll employment calculated from "
                "the official BLS Current Employment "
                "Statistics series."
            ),

            "full_text": (
                f"Total nonfarm employment for "
                f"{month_name} {year}: "
                f"{employment_level} thousand. "
                f"Monthly payroll change: "
                f"{payroll_change} thousand."
            ),

            # This is the reference month.
            "event_date": event_date,

            "event_status": event_status,

            # Exact release date will later come
            # from the BLS release calendar.
            "published_time_utc": None,

            "ingestion_time_utc": (
                ingestion_time
            ),

            "country": "United States",

            "region": "North America",

            "language": "en",

            "asset_class": "Multi-Asset",

            "market": "United States",

            "sector": "Labour Market",

            "event_type": (
                "Non-Farm Payroll Release"
            ),

            # Previous month's payroll change.
            "previous_value": (
                previous_payroll_change
            ),

            # BLS does not supply market forecasts.
            "forecast_value": None,

            # Current month's payroll change.
            "actual_value": payroll_change,

            "value_unit": (
                "Thousands of Jobs"
            ),

            "surprise_percentage": None,

            "importance_score": 95,

            "sentiment_score": None,

            "confidence_score": 0.98,

            "sector_impact": (
                "Equities, Bonds, Banking, "
                "Commodities, Foreign Exchange"
            ),

            "historical_impact": (
                "Non-Farm Payroll releases may "
                "affect interest-rate expectations, "
                "USD, Treasury yields, equities "
                "and gold."
            ),

            "time_until_event_minutes": None,

            "keywords": (
                "NFP, nonfarm payrolls, employment, "
                "jobs, labour market, BLS"
            ),

            "named_entities": (
                "U.S. Bureau of Labor Statistics"
            ),

            "related_assets": (
                "USD, Gold, US Treasury Bonds, "
                "S&P 500"
            ),

            "employment_level": (
                employment_level
            ),

            "raw_response": json.dumps(
                observation[
                    "raw_observation"
                ],
                ensure_ascii=False,
            ),
        }

        records.append(record)

        if employment_level is not None:
            previous_employment_level = (
                employment_level
            )

        if payroll_change is not None:
            previous_payroll_change = (
                payroll_change
            )

    return pd.DataFrame(records)


def main() -> None:
    """Run the NFP collection pipeline."""

    print("Starting NFP data collection...")

    data = collect_nfp_data()

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
        "\nNFP collection completed successfully."
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
        "employment_level",
        "previous_value",
        "actual_value",
        "event_status",
        "ingestion_time_utc",
    ]

    print(
        data[preview_columns]
        .tail(10)
        .to_string(index=False)
    )

    print("\nMissing actual values:")
    print(
        data["actual_value"].isna().sum()
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