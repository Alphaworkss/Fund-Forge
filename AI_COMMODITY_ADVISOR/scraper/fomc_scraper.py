import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


FOMC_URL = (
    "https://www.federalreserve.gov/"
    "monetarypolicy/fomccalendars.htm"
)


def create_event_id(
    source: str,
    event_name: str,
    event_date: str
) -> str:
    unique_text = (
        f"{source}|{event_name}|{event_date}"
    )

    return hashlib.sha256(
        unique_text.encode("utf-8")
    ).hexdigest()[:16]


def scrape_fomc_calendar():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 Economic Event "
            "Pipeline Internship Project"
        )
    }

    response = requests.get(
        FOMC_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    Path("data/raw").mkdir(
        parents=True,
        exist_ok=True
    )

    Path("data/processed").mkdir(
        parents=True,
        exist_ok=True
    )

    raw_file_path = Path(
        "data/raw/fomc_calendar_raw.html"
    )

    raw_file_path.write_text(
        response.text,
        encoding="utf-8"
    )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    ingestion_time_utc = datetime.now(
        timezone.utc
    ).isoformat()

    records = []

    headings = soup.find_all(
        ["h3", "h4"]
    )

    for heading in headings:
        heading_text = heading.get_text(
            " ",
            strip=True
        )

        year_match = re.search(
            r"\b(20\d{2})\b",
            heading_text
        )

        if (
            "FOMC Meetings" not in heading_text
            or year_match is None
        ):
            continue

        year = int(
            year_match.group(1)
        )

        current_element = heading.find_next()

        while current_element:
            if (
                current_element.name
                in ["h3", "h4"]
                and current_element != heading
            ):
                break

            text = current_element.get_text(
                " ",
                strip=True
            )

            date_match = re.search(
                r"("
                r"January|February|March|April|"
                r"May|June|July|August|September|"
                r"October|November|December"
                r")\s+(\d{1,2})(?:-(\d{1,2}))?",
                text
            )

            if date_match:
                month_name = date_match.group(1)

                start_day = int(
                    date_match.group(2)
                )

                end_day = date_match.group(3)

                event_day = (
                    int(end_day)
                    if end_day
                    else start_day
                )

                event_date = datetime.strptime(
                    (
                        f"{year}-"
                        f"{month_name}-"
                        f"{event_day}"
                    ),
                    "%Y-%B-%d"
                ).date()

                event_date_text = (
                    event_date.isoformat()
                )

                event_name = "FOMC Meeting"

                event_id = create_event_id(
                    "Federal Reserve",
                    event_name,
                    event_date_text
                )

                now_utc = datetime.now(
                    timezone.utc
                ).date()

                if event_date > now_utc:
                    event_status = "Upcoming"
                else:
                    event_status = "Completed"

                record = {
                    "id": event_id,
                    "source": (
                        "Federal Reserve"
                    ),
                    "source_url": FOMC_URL,
                    "event_name": event_name,
                    "event_type": (
                        "Monetary Policy Meeting"
                    ),
                    "country": (
                        "United States"
                    ),
                    "event_date": (
                        event_date_text
                    ),
                    "published_time_utc": None,
                    "ingestion_time_utc": (
                        ingestion_time_utc
                    ),
                    "previous_value": None,
                    "forecast_value": None,
                    "actual_value": None,
                    "surprise_percentage": None,
                    "importance_score": 95,
                    "affected_assets": (
                        "USD, Gold, US Bonds, "
                        "US Equities"
                    ),
                    "event_status": (
                        event_status
                    ),
                    "raw_response": text
                }

                records.append(record)

            current_element = (
                current_element.find_next()
            )

    dataframe = pd.DataFrame(
        records
    )

    if dataframe.empty:
        print(
            "No records were extracted."
        )
        return dataframe

    dataframe = dataframe.drop_duplicates(
        subset=["id"]
    )

    output_path = Path(
        "data/processed/fomc_events.csv"
    )

    dataframe.to_csv(
        output_path,
        index=False
    )

    print(
        "Raw webpage saved:",
        raw_file_path
    )

    print(
        "Processed file saved:",
        output_path
    )

    print(
        "Total records:",
        len(dataframe)
    )

    print(
        dataframe[
            [
                "event_name",
                "event_date",
                "source",
                "ingestion_time_utc",
                "event_status"
            ]
        ].head(10)
    )

    return dataframe


if __name__ == "__main__":
    scrape_fomc_calendar()