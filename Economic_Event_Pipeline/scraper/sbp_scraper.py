from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


SBP_URL = "https://www.sbp.org.pk/m_policy/mon.asp"
SBP_BASE_URL = "https://www.sbp.org.pk/"

RAW_HTML_FILE = Path(
    "data/raw/sbp_monetary_policy_page.html"
)

RAW_TEXT_FILE = Path(
    "data/raw/sbp_monetary_policy_text.txt"
)

CSV_OUTPUT_FILE = Path(
    "data/processed/sbp_events.csv"
)

JSON_OUTPUT_FILE = Path(
    "data/processed/sbp_events.json"
)


def clean_text(value: str | None) -> str | None:
    """Remove repeated spaces and line breaks."""

    if value is None:
        return None

    cleaned = re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()

    return cleaned or None


def create_id(
    event_date: str,
    title: str,
) -> str:
    """Create a stable unique ID."""

    value = f"SBP|{event_date}|{title}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def parse_date_from_text(
    text: str,
) -> str | None:
    """
    Extract dates such as:
    Jun 16, 2025
    June 16, 2025
    16 June 2025
    """

    date_patterns = [
        # Jun 16, 2025 or June 16, 2025
        r"\b("
        r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
        r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?"
        r")\s+(\d{1,2}),?\s+(\d{4})\b",

        # 16 June 2025
        r"\b(\d{1,2})\s+("
        r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
        r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?"
        r")\s+(\d{4})\b",
    ]

    month_formats = [
        "%b %d %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for pattern in date_patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        date_text = " ".join(
            match.groups()
        )

        for date_format in month_formats:
            try:
                parsed = datetime.strptime(
                    date_text,
                    date_format,
                )

                return parsed.strftime(
                    "%Y-%m-%d"
                )

            except ValueError:
                continue

    return None


def determine_event_status(
    event_date: str,
) -> str:
    """Classify an event as Released or Upcoming."""

    parsed_date = pd.to_datetime(
        event_date,
        errors="coerce",
    )

    if pd.isna(parsed_date):
        return "Invalid"

    today = pd.Timestamp.now(
        tz="UTC"
    ).tz_localize(None).normalize()

    if parsed_date <= today:
        return "Released"

    return "Upcoming"


def calculate_time_until_event(
    event_date: str,
) -> int | None:
    """Calculate approximate minutes until event date."""

    event_time = pd.to_datetime(
        event_date,
        utc=True,
        errors="coerce",
    )

    if pd.isna(event_time):
        return None

    difference = (
        event_time.to_pydatetime()
        - datetime.now(timezone.utc)
    )

    return int(
        difference.total_seconds() / 60
    )


def is_statement_link(
    link_text: str,
) -> bool:
    """Check whether an anchor represents an SBP statement."""

    text = link_text.lower()

    required_phrase = (
        "monetary policy statement"
    )

    excluded_phrases = (
        "urdu",
        "compendium",
        "information compendium",
    )

    return (
        required_phrase in text
        and not any(
            phrase in text
            for phrase in excluded_phrases
        )
    )


def collect_sbp_events() -> pd.DataFrame:
    """Collect official SBP monetary-policy statements."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(
        SBP_URL,
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

    page_text = clean_text(
        soup.get_text(
            separator=" ",
            strip=True,
        )
    )

    RAW_TEXT_FILE.write_text(
        page_text or "",
        encoding="utf-8",
    )

    ingestion_time = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        link_text = clean_text(
            anchor.get_text(
                " ",
                strip=True,
            )
        )

        if not link_text:
            continue

        if not is_statement_link(
            link_text
        ):
            continue

        # Include nearby row text because the date may sit
        # outside the anchor itself.
        parent_row = anchor.find_parent(
            ["tr", "li", "p", "div"]
        )

        context_text = link_text

        if parent_row is not None:
            context_text = clean_text(
                parent_row.get_text(
                    " ",
                    strip=True,
                )
            ) or link_text

        event_date = parse_date_from_text(
            context_text
        )

        if event_date is None:
            event_date = parse_date_from_text(
                link_text
            )

        if event_date is None:
            continue

        statement_url = urljoin(
            SBP_BASE_URL,
            anchor.get("href"),
        )

        # Keep approximately three years plus current year.
        event_year = int(
            event_date[:4]
        )

        if event_year < 2023:
            continue

        event_status = determine_event_status(
            event_date
        )

        title = (
            f"SBP Monetary Policy Statement - "
            f"{event_date}"
        )

        record = {
            "id": create_id(
                event_date,
                title,
            ),

            "source": "State Bank of Pakistan",

            "source_type": (
                "Official Publication Calendar"
            ),

            "source_url": SBP_URL,

            "document_url": statement_url,

            "title": title,

            "description": (
                "Official monetary-policy statement "
                "published by the State Bank of Pakistan."
            ),

            "full_text": context_text,

            "event_date": event_date,

            "event_status": event_status,

            # The statement date is used as the
            # official publication date.
            "published_time_utc": (
                f"{event_date}T00:00:00Z"
            ),

            "ingestion_time_utc": (
                ingestion_time
            ),

            "country": "Pakistan",

            "region": "South Asia",

            "language": "en",

            "asset_class": "Multi-Asset",

            "market": "Pakistan",

            "sector": "Monetary Policy",

            "event_type": (
                "SBP Monetary Policy Statement"
            ),

            "previous_value": None,

            "forecast_value": None,

            "actual_value": None,

            "value_unit": (
                "Policy Rate Percentage"
            ),

            "surprise_percentage": None,

            "importance_score": 95,

            "sentiment_score": None,

            "confidence_score": 0.95,

            "sector_impact": (
                "Banking, Equities, Bonds, "
                "Foreign Exchange, Real Estate, "
                "Consumer Finance"
            ),

            "historical_impact": (
                "SBP monetary-policy decisions may "
                "affect PKR, government securities, "
                "banking stocks, equity valuations, "
                "borrowing costs and inflation expectations."
            ),

            "time_until_event_minutes": (
                calculate_time_until_event(
                    event_date
                )
            ),

            "keywords": (
                "SBP, monetary policy, policy rate, "
                "interest rate, inflation, Pakistan"
            ),

            "named_entities": (
                "State Bank of Pakistan, "
                "Monetary Policy Committee"
            ),

            "related_assets": (
                "PKR, Pakistan Government Bonds, "
                "KSE-100, Banking Stocks, Gold"
            ),

            "raw_response": json.dumps(
                {
                    "link_text": link_text,
                    "context_text": context_text,
                    "statement_url": statement_url,
                },
                ensure_ascii=False,
            ),
        }

        records.append(record)

    data = pd.DataFrame(records)

    if data.empty:
        raise ValueError(
            "No SBP monetary-policy statements were extracted. "
            "The page structure may have changed, or the "
            "website may be blocking automated access."
        )

    data = data.drop_duplicates(
        subset=["id"],
        keep="last",
    )

    data = data.sort_values(
        by="event_date"
    ).reset_index(drop=True)

    return data


def main() -> None:
    """Run the complete SBP collection process."""

    print(
        "Starting SBP monetary-policy collection..."
    )

    data = collect_sbp_events()

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
        "\nSBP collection completed successfully."
    )

    print(
        "Rows collected:",
        len(data),
    )

    print("\nCSV output:")
    print(CSV_OUTPUT_FILE)

    print("\nJSON output:")
    print(JSON_OUTPUT_FILE)

    print("\nPreview:")

    preview_columns = [
        "title",
        "event_date",
        "event_status",
        "document_url",
        "ingestion_time_utc",
    ]

    print(
        data[
            preview_columns
        ]
        .tail(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    try:
        main()

    except requests.RequestException as error:
        print(
            "\nNetwork or website error:"
        )
        print(error)

    except ValueError as error:
        print(
            "\nData extraction error:"
        )
        print(error)

    except Exception as error:
        print(
            "\nUnexpected error:"
        )
        print(error)