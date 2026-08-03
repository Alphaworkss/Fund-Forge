from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import sleep

import pandas as pd
import yfinance as yf


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_FOLDER / "data"

LIVE_CSV_FILE = DATA_FOLDER / "live_commodity_prices.csv"
LIVE_EXCEL_FILE = DATA_FOLDER / "live_commodity_prices.xlsx"
LOG_FILE = DATA_FOLDER / "live_updater_log.txt"


COMMODITIES = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F",
    "Corn": "ZC=F"
}


# 300 seconds = 5 minutes
UPDATE_INTERVAL_SECONDS = 300


def write_log(message: str) -> None:
    """Print a message and save it in a log file."""

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"

    print(log_message)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(log_message + "\n")


def clean_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Convert Yahoo Finance columns into simple names."""

    data = data.copy()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [
            column[0] if isinstance(column, tuple) else column
            for column in data.columns
        ]

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]

    return data


def safe_float(value):
    """Convert a value into float safely."""

    if pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_latest_commodity(
    commodity_name: str,
    ticker: str,
) -> dict | None:
    """Fetch the latest available one-minute row."""

    data = yf.download(
        ticker,
        period="1d",
        interval="1m",
        auto_adjust=False,
        progress=False,
        threads=False,
        prepost=True,
    )

    if data.empty:
        write_log(
            f"No data returned for {commodity_name} ({ticker})."
        )
        return None

    data = clean_columns(data)
    data = data.dropna(how="all")

    if data.empty:
        return None

    latest_row = data.iloc[-1]
    market_timestamp = data.index[-1]

    return {
        "Fetched At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Market Timestamp": str(market_timestamp),
        "Commodity": commodity_name,
        "Ticker": ticker,
        "Open": safe_float(latest_row.get("Open")),
        "High": safe_float(latest_row.get("High")),
        "Low": safe_float(latest_row.get("Low")),
        "Close": safe_float(latest_row.get("Close")),
        "Adj Close": safe_float(latest_row.get("Adj Close")),
        "Volume": safe_float(latest_row.get("Volume")),
    }


def fetch_all_commodities() -> pd.DataFrame:
    """Fetch the latest row for all five commodities."""

    records = []

    for commodity_name, ticker in COMMODITIES.items():
        write_log(f"Fetching {commodity_name} ({ticker})...")

        try:
            record = fetch_latest_commodity(
                commodity_name,
                ticker,
            )

            if record is not None:
                records.append(record)

        except Exception as error:
            write_log(
                f"Error fetching {commodity_name}: {error}"
            )

    return pd.DataFrame(records)


def remove_duplicates(data: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate market timestamps."""

    if data.empty:
        return data

    data = data.drop_duplicates(
        subset=[
            "Commodity",
            "Ticker",
            "Market Timestamp",
        ],
        keep="last",
    )

    data = data.sort_values(
        by=["Market Timestamp", "Commodity"]
    ).reset_index(drop=True)

    return data


def save_live_data(new_data: pd.DataFrame) -> None:
    """Append new data and update CSV and Excel files."""

    if new_data.empty:
        write_log("No new data available.")
        return

    if LIVE_CSV_FILE.exists():
        existing_data = pd.read_csv(LIVE_CSV_FILE)

        combined_data = pd.concat(
            [existing_data, new_data],
            ignore_index=True,
        )
    else:
        combined_data = new_data.copy()

    combined_data = remove_duplicates(combined_data)

    combined_data.to_csv(
        LIVE_CSV_FILE,
        index=False,
    )

    try:
        combined_data.to_excel(
            LIVE_EXCEL_FILE,
            index=False,
            sheet_name="Live Commodity Prices",
        )

    except PermissionError:
        write_log(
            "Excel file is open. Close live_commodity_prices.xlsx "
            "and run the updater again."
        )

    write_log(
        f"Data saved successfully. Total rows: {len(combined_data)}"
    )


def run_once() -> None:
    """Run one complete update cycle."""

    write_log("Starting update cycle.")

    latest_data = fetch_all_commodities()

    if not latest_data.empty:
        print("\nLatest available prices:")
        print(
            latest_data[
                [
                    "Commodity",
                    "Ticker",
                    "Market Timestamp",
                    "Close",
                ]
            ]
        )

    save_live_data(latest_data)

    write_log("Update cycle completed.")


def run_continuously() -> None:
    """Keep updating prices every five minutes."""

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    write_log("Live commodity updater started.")
    write_log(
        f"Update interval: {UPDATE_INTERVAL_SECONDS} seconds."
    )

    while True:
        try:
            run_once()

        except KeyboardInterrupt:
            write_log("Updater stopped by user.")
            break

        except Exception as error:
            write_log(f"Unexpected error: {error}")

        write_log("Waiting for next update...")
        sleep(UPDATE_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_continuously()