from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


ECB_URL = (
    "https://www.ecb.europa.eu/"
    "press/calendars/mgcgc/html/index.en.html"
)

RAW_HTML_FILE = Path(
    "data/raw/ecb_calendar_page.html"
)

RAW_TEXT_FILE = Path(
    "data/raw/ecb_calendar_text.txt"
)

CSV_OUTPUT_FILE = Path(
    "data/processed/ecb_events.csv"
)

JSON_OUTPUT_FILE = Path(
    "data/processed/ecb_events.json"
)


def create_id(
    event_date: str,
    event_title: str,
) -> str:
    """Create a stable unique ID for every ECB event."""

    value = f"ECB|{event_date}|{event_title}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def clean_text(
    value: str | None,
) -> str | None:
    """Remove repeated spaces and line breaks."""

    if value is None:
        return None

    cleaned = re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()

    return cleaned or None


def parse_date(
    date_text: str,
) -> str | None:
    """
    Convert a date such as 29/10/2026
    into ISO format: 2026-10-29.
    """

    try:
        parsed_date = datetime.strptime(
            date_text.strip(),
            "%d/%m/%Y",
        )

        return parsed_date.strftime(
            "%Y-%m-%d"
        )

    except ValueError:
        return None


def determine_event_type(
    description: str,
) -> str:
    """
    Classify an ECB calendar event.

    Important:
    Non-monetary must be checked before monetary,
    because the phrase 'non-monetary policy meeting'
    also contains the words 'monetary policy meeting'.
    """

    text = description.lower()

    if "non-monetary policy meeting" in text:
        return "ECB Non-Monetary Policy Meeting"

    if "monetary policy meeting" in text:
        return "ECB Monetary Policy Meeting"

    if "general council meeting" in text:
        return "ECB General Council Meeting"

    if "governing council" in text:
        return "ECB Governing Council Event"

    return "ECB Other Event"


def determine_importance(
    event_type: str,
) -> int:
    """Assign importance score according to event type."""

    if event_type == "ECB Monetary Policy Meeting":
        return 95

    if event_type == "ECB General Council Meeting":
        return 70

    if event_type == "ECB Non-Monetary Policy Meeting":
        return 60

    if event_type == "ECB Governing Council Event":
        return 65

    return 50


def determine_sector_impact(
    event_type: str,
) -> str:
    """Assign affected sectors according to event type."""

    if event_type == "ECB Monetary Policy Meeting":
        return (
            "Banking, Equities, Bonds, Commodities, "
            "Foreign Exchange"
        )

    if event_type == "ECB General Council Meeting":
        return "Banking, Monetary Policy, Financial Regulation"

    if event_type == "ECB Non-Monetary Policy Meeting":
        return "Banking, Financial Regulation, Institutional Policy"

    return "Banking, Policy"


def determine_historical_impact(
    event_type: str,
) -> str:
    """Describe the likely historical market impact."""

    if event_type == "ECB Monetary Policy Meeting":
        return (
            "ECB monetary policy meetings may affect "
            "interest-rate expectations, EUR, European "
            "government bonds, equities and gold."
        )

    if event_type == "ECB Non-Monetary Policy Meeting":
        return (
            "ECB non-monetary meetings generally have "
            "lower direct market impact and focus on "
            "institutional, regulatory or operational matters."
        )

    if event_type == "ECB General Council Meeting":
        return (
            "General Council meetings normally have lower "
            "direct market impact but may influence broader "
            "European central banking coordination."
        )

    return (
        "ECB institutional event with limited or "
        "uncertain direct market impact."
    )


def determine_related_assets(
    event_type: str,
) -> str:
    """Assign related assets according to event type."""

    if event_type == "ECB Monetary Policy Meeting":
        return (
            "EUR, Euro Stoxx 50, European Government Bonds, Gold"
        )

    return (
        "EUR, European Government Bonds, European Banking Stocks"
    )


def calculate_event_status(
    event_date: str,
) -> str:
    """Return Released for past events and Upcoming for future events."""

    parsed_event_date = pd.to_datetime(
        event_date,
        errors="coerce",
    )

    if pd.isna(parsed_event_date):
        return "Invalid"

    current_date = pd.Timestamp.now(
        tz="UTC"
    ).tz_localize(None).normalize()

    if parsed_event_date < current_date:
        return "Released"

    return "Upcoming"


def calculate_time_until_event(
    event_date: str,
) -> int | None:
    """
    Calculate the approximate number of minutes
    until the event date.

    Because the calendar does not always provide
    an exact event time, midnight UTC is used.
    """

    event_datetime = pd.to_datetime(
        event_date,
        utc=True,
        errors="coerce",
    )

    if pd.isna(event_datetime):
        return None

    current_time = datetime.now(
        timezone.utc
    )

    difference = (
        event_datetime.to_pydatetime()
        - current_time
    )

    return int(
        difference.total_seconds() / 60
    )


def extract_calendar_events(
    page_text: str,
) -> list[tuple[str, str]]:
    """
    Extract date-description pairs from the ECB page text.

    Example:
    29/10/2026 Governing Council of the ECB:
    monetary policy meeting...
    """

    pattern = re.compile(
        r"(\d{2}/\d{2}/\d{4})\s+"
        r"(.+?)"
        r"(?=\s+\d{2}/\d{2}/\d{4}\s+|$)",
        flags=re.DOTALL,
    )

    return pattern.findall(
        page_text
    )


def collect_ecb_events() -> pd.DataFrame:
    """Collect ECB Governing Council and General Council events."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(
        ECB_URL,
        headers=headers,
        timeout=60,
    )

    response.raise_for_status()

    RAW_HTML_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RAW_HTML_FILE.write_text(
        response.text,
        encoding="utf-8",
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    page_text = soup.get_text(
        separator=" ",
        strip=True,
    )

    page_text = clean_text(
        page_text
    )

    if page_text is None:
        raise ValueError(
            "ECB page text could not be extracted."
        )

    RAW_TEXT_FILE.write_text(
        page_text,
        encoding="utf-8",
    )

    ingestion_time = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    matches = extract_calendar_events(
        page_text
    )

    if not matches:
        raise ValueError(
            "No date and event pairs were found "
            "on the ECB calendar page."
        )

    records = []

    relevant_terms = (
        "governing council",
        "general council",
        "monetary policy meeting",
        "non-monetary policy meeting",
    )

    for date_text, description in matches:

        description = clean_text(
            description
        )

        if description is None:
            continue

        lower_description = (
            description.lower()
        )

        if not any(
            term in lower_description
            for term in relevant_terms
        ):
            continue

        event_date = parse_date(
            date_text
        )

        if event_date is None:
            continue

        event_type = determine_event_type(
            description
        )

        if event_type == "ECB Other Event":
            continue

        importance_score = determine_importance(
            event_type
        )

        event_status = calculate_event_status(
            event_date
        )

        title = description[:250]

        record = {
            "id": create_id(
                event_date,
                title,
            ),

            "source": (
                "European Central Bank"
            ),

            "source_type": (
                "Official Calendar"
            ),

            "source_url": ECB_URL,

            "title": title,

            "description": description,

            "full_text": description,

            "event_date": event_date,

            "event_status": event_status,

            "published_time_utc": None,

            "ingestion_time_utc": (
                ingestion_time
            ),

            "country": "Euro Area",

            "region": "Europe",

            "language": "en",

            "asset_class": "Multi-Asset",

            "market": "Euro Area",

            "sector": "Monetary Policy",

            "event_type": event_type,

            "previous_value": None,

            "forecast_value": None,

            "actual_value": None,

            "value_unit": None,

            "surprise_percentage": None,

            "importance_score": (
                importance_score
            ),

            "sentiment_score": None,

            "confidence_score": 0.95,

            "sector_impact": (
                determine_sector_impact(
                    event_type
                )
            ),

            "historical_impact": (
                determine_historical_impact(
                    event_type
                )
            ),

            "time_until_event_minutes": (
                calculate_time_until_event(
                    event_date
                )
            ),

            "keywords": (
                "ECB, European Central Bank, "
                "monetary policy, Governing Council, "
                "General Council, euro area"
            ),

            "named_entities": (
                "European Central Bank, "
                "ECB Governing Council, "
                "ECB General Council"
            ),

            "related_assets": (
                determine_related_assets(
                    event_type
                )
            ),

            "raw_response": json.dumps(
                {
                    "date_text": date_text,
                    "description": description,
                },
                ensure_ascii=False,
            ),
        }

        records.append(
            record
        )

    data = pd.DataFrame(
        records
    )

    if data.empty:
        raise ValueError(
            "No relevant ECB events were extracted. "
            "The ECB webpage structure may have changed."
        )

    data = data.drop_duplicates(
        subset=["id"],
        keep="last",
    )

    data = data.sort_values(
        by=[
            "event_date",
            "event_type",
        ]
    ).reset_index(
        drop=True
    )

    return data


def main() -> None:
    """Run the complete ECB collection process."""

    print(
        "Starting ECB calendar collection..."
    )

    data = collect_ecb_events()

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
        "\nECB collection completed successfully."
    )

    print(
        "Rows collected:",
        len(data),
    )

    print(
        "\nEvent types:"
    )

    print(
        data["event_type"].value_counts()
    )

    print(
        "\nCSV output:"
    )

    print(
        CSV_OUTPUT_FILE
    )

    print(
        "\nJSON output:"
    )

    print(
        JSON_OUTPUT_FILE
    )

    print(
        "\nPreview:"
    )

    preview_columns = [
        "title",
        "event_date",
        "event_type",
        "event_status",
        "importance_score",
        "ingestion_time_utc",
    ]

    print(
        data[
            preview_columns
        ]
        .head(25)
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    try:
        main()

    except requests.RequestException as error:
        print(
            "\nNetwork or website error:"
        )
        print(
            error
        )

    except ValueError as error:
        print(
            "\nData extraction error:"
        )
        print(
            error
        )

    except Exception as error:
        print(
            "\nUnexpected error:"
        )
        print(
            error
        )