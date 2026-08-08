from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

import pandas as pd
import requests


API_URL = "https://www.alphavantage.co/query"

API_KEY = "LR6AHGBLMCHXUD5Z"

RAW_FOLDER = Path("data/raw/earnings")

CSV_OUTPUT_FILE = Path(
    "data/processed/earnings_events.csv"
)

JSON_OUTPUT_FILE = Path(
    "data/processed/earnings_events.json"
)


# Five-company sample for the first version.
COMPANIES = {
    "AAPL": {
        "company_name": "Apple Inc.",
        "country": "United States",
        "sector": "Technology",
        "market": "NASDAQ",
        "sector_etf": "XLK",
    },
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "country": "United States",
        "sector": "Technology",
        "market": "NASDAQ",
        "sector_etf": "XLK",
    },
    "AMZN": {
        "company_name": "Amazon.com Inc.",
        "country": "United States",
        "sector": "Consumer Discretionary",
        "market": "NASDAQ",
        "sector_etf": "XLY",
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "country": "United States",
        "sector": "Communication Services",
        "market": "NASDAQ",
        "sector_etf": "XLC",
    },
    "NVDA": {
        "company_name": "NVIDIA Corporation",
        "country": "United States",
        "sector": "Technology",
        "market": "NASDAQ",
        "sector_etf": "XLK",
    },
}


def safe_float(value) -> float | None:
    """Convert API values safely into float."""

    if value in (
        None,
        "",
        "-",
        "None",
        "null",
        "N/A",
        "NA",
    ):
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def create_id(
    symbol: str,
    reported_date: str,
) -> str:
    """Create one stable ID for each earnings event."""

    value = f"ALPHA_VANTAGE|EARNINGS|{symbol}|{reported_date}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def calculate_surprise_percentage(
    actual_value: float | None,
    forecast_value: float | None,
) -> float | None:
    """
    Calculate earnings surprise if the API does not
    provide a usable surprise percentage.
    """

    if (
        actual_value is None
        or forecast_value is None
        or forecast_value == 0
    ):
        return None

    return round(
        (
            (actual_value - forecast_value)
            / abs(forecast_value)
        )
        * 100,
        4,
    )


def calculate_sentiment(
    surprise_percentage: float | None,
) -> float | None:
    """
    Create a simple normalized event sentiment score.

    Positive earnings surprise = positive score.
    Negative earnings surprise = negative score.
    """

    if surprise_percentage is None:
        return None

    score = surprise_percentage / 20

    return round(
        max(-1.0, min(1.0, score)),
        4,
    )


def determine_importance(
    symbol: str,
) -> int:
    """Assign importance based on selected major companies."""

    high_importance = {
        "AAPL",
        "MSFT",
        "AMZN",
        "GOOGL",
        "NVDA",
    }

    if symbol in high_importance:
        return 90

    return 75


def fetch_company_earnings(
    symbol: str,
) -> dict:
    """Download one company's earnings history."""

    parameters = {
        "function": "EARNINGS",
        "symbol": symbol,
        "apikey": API_KEY,
    }

    response = requests.get(
        API_URL,
        params=parameters,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    if "Error Message" in data:
        raise ValueError(
            f"{symbol}: {data['Error Message']}"
        )

    if "Information" in data:
        raise ValueError(
            f"{symbol}: API information message: "
            f"{data['Information']}"
        )

    if "Note" in data:
        raise ValueError(
            f"{symbol}: API rate-limit message: "
            f"{data['Note']}"
        )

    return data


def collect_earnings_events() -> pd.DataFrame:
    """Collect three years of quarterly earnings events."""

    if (
        not API_KEY
        or API_KEY
        == "PASTE_YOUR_ALPHA_VANTAGE_KEY_HERE"
    ):
        raise ValueError(
            "Paste your Alpha Vantage API key "
            "inside the API_KEY variable."
        )

    RAW_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    current_time = datetime.now(
        timezone.utc
    )

    ingestion_time = current_time.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Exact rolling three-year cutoff.
    cutoff_date = (
        pd.Timestamp(current_time.date())
        - pd.DateOffset(years=3)
    )

    records = []

    for position, (
        symbol,
        company,
    ) in enumerate(
        COMPANIES.items(),
        start=1,
    ):
        print(
            f"Fetching {symbol} earnings "
            f"({position}/{len(COMPANIES)})..."
        )

        raw_data = fetch_company_earnings(
            symbol
        )

        raw_file = (
            RAW_FOLDER
            / f"{symbol}_earnings_raw.json"
        )

        raw_file.write_text(
            json.dumps(
                raw_data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        quarterly_earnings = raw_data.get(
            "quarterlyEarnings",
            [],
        )

        if not quarterly_earnings:
            print(
                f"No quarterly earnings found for {symbol}."
            )
            continue

        # Oldest to newest so previous EPS can be created.
        quarterly_earnings = sorted(
            quarterly_earnings,
            key=lambda row: row.get(
                "reportedDate",
                "",
            ),
        )

        previous_reported_eps = None

        for earning in quarterly_earnings:
            reported_date = earning.get(
                "reportedDate"
            )

            parsed_date = pd.to_datetime(
                reported_date,
                errors="coerce",
            )

            if pd.isna(parsed_date):
                continue

            if parsed_date < cutoff_date:
                continue

            reported_eps = safe_float(
                earning.get("reportedEPS")
            )

            estimated_eps = safe_float(
                earning.get("estimatedEPS")
            )

            api_surprise = safe_float(
                earning.get("surprise")
            )

            surprise_percentage = safe_float(
                earning.get(
                    "surprisePercentage"
                )
            )

            if surprise_percentage is None:
                surprise_percentage = (
                    calculate_surprise_percentage(
                        reported_eps,
                        estimated_eps,
                    )
                )

            sentiment_score = calculate_sentiment(
                surprise_percentage
            )

            event_status = (
                "Released"
                if reported_eps is not None
                else "Missing Official Value"
            )

            importance_score = (
                determine_importance(symbol)
            )

            title = (
                f"{company['company_name']} "
                f"Quarterly Earnings - {reported_date}"
            )

            description = (
                f"Quarterly earnings release for "
                f"{company['company_name']} ({symbol}). "
                f"Reported EPS: {reported_eps}; "
                f"estimated EPS: {estimated_eps}; "
                f"surprise percentage: "
                f"{surprise_percentage}."
            )

            record = {
                "id": create_id(
                    symbol,
                    reported_date,
                ),

                "source": "Alpha Vantage",

                "source_type": (
                    "Financial Data API"
                ),

                "source_url": (
                    "https://www.alphavantage.co/"
                ),

                "url": (
                    "https://www.alphavantage.co/"
                ),

                "title": title,

                "description": description,

                "full_text": description,

                "event_name": (
                    f"{company['company_name']} "
                    "Quarterly Earnings"
                ),

                "event_date": reported_date,

                "event_status": event_status,

                # Exact earnings announcement time
                # is not supplied by this endpoint.
                "published_time_utc": (
                    f"{reported_date}T00:00:00Z"
                ),

                "ingestion_time_utc": (
                    ingestion_time
                ),

                "country": company["country"],

                "region": "North America",

                "language": "en",

                "asset_class": "Equities",

                "market": company["market"],

                "sector": company["sector"],

                "event_type": (
                    "Quarterly Earnings Release"
                ),

                # Previous quarter's reported EPS.
                "previous_value": (
                    previous_reported_eps
                ),

                # Analyst consensus EPS.
                "forecast_value": estimated_eps,

                # Company's reported EPS.
                "actual_value": reported_eps,

                "value_unit": (
                    "Earnings Per Share"
                ),

                "surprise_value": api_surprise,

                "surprise_percentage": (
                    surprise_percentage
                ),

                "importance": importance_score,

                "importance_score": (
                    importance_score
                ),

                "sentiment_score": (
                    sentiment_score
                ),

                "confidence_score": 0.95,

                "sector_impact": (
                    f"{company['sector']}, "
                    "Equities, Market Indices, "
                    "Options and Derivatives"
                ),

                "affected_assets": (
                    f"{symbol}, "
                    f"{company['sector_etf']}, "
                    "NASDAQ-100, S&P 500"
                ),

                "historical_impact": (
                    "Earnings surprises may affect the "
                    "company's share price, sector peers, "
                    "equity indices, volatility and "
                    "investor sentiment."
                ),

                # Historical event: future countdown
                # is not applicable.
                "time_until_event": None,

                "time_until_event_minutes": None,

                "keywords": (
                    f"{symbol}, earnings, EPS, "
                    "quarterly results, analyst estimate, "
                    "earnings surprise"
                ),

                "named_entities": (
                    f"{company['company_name']}, "
                    "Alpha Vantage"
                ),

                "related_assets": (
                    f"{symbol}, "
                    f"{company['sector_etf']}, "
                    "NASDAQ-100, S&P 500"
                ),

                "symbol": symbol,

                "company_name": (
                    company["company_name"]
                ),

                "fiscal_date_ending": earning.get(
                    "fiscalDateEnding"
                ),

                "raw_response": json.dumps(
                    earning,
                    ensure_ascii=False,
                ),
            }

            records.append(record)

            if reported_eps is not None:
                previous_reported_eps = (
                    reported_eps
                )

        # Small delay to reduce API throttling risk.
        sleep(15)

    data = pd.DataFrame(records)

    if data.empty:
        raise ValueError(
            "No three-year earnings events were collected."
        )

    data = data.drop_duplicates(
        subset=["id"],
        keep="last",
    )

    data = data.sort_values(
        by=[
            "event_date",
            "symbol",
        ]
    ).reset_index(drop=True)

    return data


def main() -> None:
    """Run the complete earnings collection process."""

    print(
        "Starting earnings event collection..."
    )

    data = collect_earnings_events()

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
        "\nEarnings collection completed successfully."
    )

    print(
        "Rows collected:",
        len(data),
    )

    print("\nRows per company:")

    print(
        data["symbol"].value_counts()
    )

    print("\nCSV output:")
    print(CSV_OUTPUT_FILE)

    print("\nJSON output:")
    print(JSON_OUTPUT_FILE)

    preview_columns = [
        "event_name",
        "event_date",
        "symbol",
        "previous_value",
        "forecast_value",
        "actual_value",
        "surprise_percentage",
        "event_status",
        "ingestion_time_utc",
    ]

    print("\nPreview:")

    print(
        data[preview_columns]
        .tail(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    try:
        main()

    except requests.RequestException as error:
        print("\nNetwork or API error:")
        print(error)

    except ValueError as error:
        print("\nData processing error:")
        print(error)

    except Exception as error:
        print("\nUnexpected error:")
        print(error)