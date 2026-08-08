from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

Path("data/raw").mkdir(
    parents=True,
    exist_ok=True
)

with open(
    "data/raw/fomc_page.html",
    "w",
    encoding="utf-8"
) as file:
    file.write(response.text)

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

page_text = soup.get_text(
    separator=" ",
    strip=True
)

ingestion_time = datetime.now(
    timezone.utc
).isoformat()

print("Source: Federal Reserve")
print("Source URL:", URL)
print("Fetched Time UTC:", ingestion_time)
print("Text Preview:")
print(page_text[:1000])
with open(
    "data/raw/fomc_text.txt",
    "w",
    encoding="utf-8"
) as file:
    file.write(page_text)

print("Text saved successfully.")
import re
import pandas as pd
from datetime import datetime, timezone


# Find only the 2023 section
start_marker = "2023 FOMC Meetings"
end_marker = "2022 FOMC Meetings"

start_index = page_text.find(start_marker)
end_index = page_text.find(end_marker)

section_2023 = page_text[start_index:end_index]

print("\n2023 Section:\n")
print(section_2023[:1500])
meeting_pattern = (
    r"(Jan/Feb 31-1|March 21-22|May 2-3|June 13-14|"
    r"July 25-26|September 19-20|Oct/Nov 31-1|December 12-13)"
)

meetings = re.findall(meeting_pattern, section_2023)

print("\nExtracted Meetings:")
print(meetings)
ingestion_time = datetime.now(timezone.utc).isoformat()

records = []

for meeting in meetings:
    record = {
        "id": f"fomc_2023_{meeting.replace(' ', '_').replace('/', '_')}",
        "source": "Federal Reserve",
        "source_type": "Official Calendar",
        "source_url": URL,
        "title": f"FOMC Meeting {meeting}",
        "description": f"Federal Open Market Committee meeting held on {meeting}, 2023.",
        "full_text": meeting,
        "event_year": 2023,
        "event_date_text": meeting,
        "published_time_utc": None,
        "ingestion_time_utc": ingestion_time,
        "country": "United States",
        "region": "North America",
        "language": "en",
        "asset_class": "Multi-Asset",
        "market": "United States",
        "sector": "Monetary Policy",
        "event_type": "FOMC Meeting",
        "importance_score": 95,
        "sentiment_score": None,
        "confidence_score": 0.95,
        "keywords": "FOMC, Federal Reserve, interest rate, monetary policy",
        "named_entities": "Federal Reserve, FOMC",
        "related_assets": "USD, Gold, US Bonds, S&P 500",
        "raw_response": meeting
    }

    records.append(record)
    df = pd.DataFrame(records)

print("\nStructured Data:")
print(df.head())
from pathlib import Path

Path("data/processed").mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    "data/processed/fomc_events_2023.csv",
    index=False
)


print("\nCSV saved successfully:")
print("data/processed/fomc_events_2023.csv")