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


BUDGET_PAGES = {
    "2023-24": {
        "url": "https://www.finance.gov.pk/fb_2023_24.html",
        "event_date": "2023-06-09",
    },
    "2024-25": {
        "url": "https://www.finance.gov.pk/fb_2024_25.html",
        "event_date": "2024-06-12",
    },
    "2025-26": {
        "url": "https://www.finance.gov.pk/fb_2025_26.html",
        "event_date": "2025-06-10",
    },
}

RAW_FOLDER = Path("data/raw/budget")

CSV_OUTPUT_FILE = Path(
    "data/processed/budget_events.csv"
)

JSON_OUTPUT_FILE = Path(
    "data/processed/budget_events.json"
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
    fiscal_year: str,
    event_date: str,
) -> str:
    """Create stable unique ID."""

    value = (
        f"PAKISTAN|FEDERAL_BUDGET|"
        f"{fiscal_year}|{event_date}"
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:20]


def calculate_status(
    event_date: str,
) -> str:
    """Return Released or Upcoming."""

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
    """Calculate minutes remaining until event."""

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


def extract_document_links(
    soup: BeautifulSoup,
    page_url: str,
) -> list[dict]:
    """Extract official budget document links."""

    documents = []

    useful_keywords = (
        "budget in brief",
        "annual budget statement",
        "finance bill",
        "budget speech",
        "explanatory memorandum",
        "demands for grants",
    )

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

        lower_text = link_text.lower()

        if not any(
            keyword in lower_text
            for keyword in useful_keywords
        ):
            continue

        document_url = urljoin(
            page_url,
            anchor["href"],
        )

        documents.append(
            {
                "document_title": link_text,
                "document_url": document_url,
            }
        )

    unique_documents = {}

    for document in documents:
        unique_documents[
            document["document_url"]
        ] = document

    return list(
        unique_documents.values()
    )


def collect_budget_events() -> pd.DataFrame:
    """Collect three years of Pakistan budget events."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    RAW_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    ingestion_time = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []

    previous_fiscal_year = None

    for fiscal_year, page_info in BUDGET_PAGES.items():

        page_url = page_info["url"]
        event_date = page_info["event_date"]

        print(
            f"Fetching Federal Budget {fiscal_year}..."
        )

        response = requests.get(
            page_url,
            headers=headers,
            timeout=60,
        )

        response.raise_for_status()

        raw_file = (
            RAW_FOLDER
            / f"budget_{fiscal_year.replace('-', '_')}.html"
        )

        raw_file.write_text(
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
        ) or ""

        document_links = extract_document_links(
            soup,
            page_url,
        )

        event_name = (
            f"Pakistan Federal Budget {fiscal_year}"
        )

        title = (
            f"Federal Budget Announcement FY {fiscal_year}"
        )

        event_status = calculate_status(
            event_date
        )

        importance_score = 95

        record = {
            "id": create_id(
                fiscal_year,
                event_date,
            ),

            "source": (
                "Finance Division, "
                "Government of Pakistan"
            ),

            "source_type": (
                "Official Government Budget Portal"
            ),

            "source_url": page_url,

            "url": page_url,

            "title": title,

            "description": (
                f"Official Pakistan Federal Budget "
                f"documents for fiscal year {fiscal_year}."
            ),

            "full_text": page_text[:5000],

            "event_name": event_name,

            "event_date": event_date,

            "fiscal_year": fiscal_year,

            "event_status": event_status,

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

            "sector": "Fiscal Policy",

            "event_type": (
                "Federal Budget Announcement"
            ),

            # Previous fiscal-year reference.
            "previous_value": previous_fiscal_year,

            # Numeric forecast/actual values are not
            # consistently available on the index page.
            "forecast_value": None,

            "actual_value": None,

            "value_unit": None,

            "surprise_percentage": None,

            "importance": importance_score,

            "importance_score": (
                importance_score
            ),

            "sentiment_score": None,

            "confidence_score": 0.98,

            "sector_impact": (
                "Banking, Energy, Agriculture, "
                "Manufacturing, Construction, "
                "Consumer Goods, Technology"
            ),

            "affected_assets": (
                "PKR, KSE-100, Pakistan Government Bonds, "
                "Banking Stocks, Energy Stocks, "
                "Cement Stocks"
            ),

            "historical_impact": (
                "Federal budget announcements may affect "
                "taxation expectations, government borrowing, "
                "PKR, equity sectors, government bonds, "
                "inflation expectations and business confidence."
            ),

            "time_until_event": (
                calculate_time_until_event(
                    event_date
                )
            ),

            "time_until_event_minutes": (
                calculate_time_until_event(
                    event_date
                )
            ),

            "keywords": (
                "Pakistan federal budget, fiscal policy, "
                "taxation, government expenditure, revenue, "
                "budget deficit"
            ),

            "named_entities": (
                "Finance Division, Government of Pakistan, "
                "Federal Board of Revenue"
            ),

            "related_assets": (
                "PKR, KSE-100, Pakistan Government Bonds, "
                "Banking Stocks, Energy Stocks"
            ),

            "document_count": len(
                document_links
            ),

            "document_links": json.dumps(
                document_links,
                ensure_ascii=False,
            ),

            "raw_response": json.dumps(
                {
                    "fiscal_year": fiscal_year,
                    "page_url": page_url,
                    "event_date": event_date,
                    "document_links": document_links,
                    "page_text": page_text,
                },
                ensure_ascii=False,
            ),
        }

        records.append(record)

        previous_fiscal_year = fiscal_year

    data = pd.DataFrame(records)

    if data.empty:
        raise ValueError(
            "No budget events were collected."
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
    """Run complete budget pipeline."""

    print(
        "Starting Pakistan Budget collection..."
    )

    data = collect_budget_events()

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
        "\nBudget collection completed successfully."
    )

    print(
        "Rows collected:",
        len(data),
    )

    print("\nCSV output:")
    print(CSV_OUTPUT_FILE)

    print("\nJSON output:")
    print(JSON_OUTPUT_FILE)

    preview_columns = [
        "event_name",
        "event_date",
        "fiscal_year",
        "event_status",
        "document_count",
        "ingestion_time_utc",
    ]

    print("\nPreview:")

    print(
        data[preview_columns]
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