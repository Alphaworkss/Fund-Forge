from pathlib import Path

import pandas as pd
import yfinance as yf


# Find the main project folder.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent

# Create the local data folder path.
DATA_FOLDER = PROJECT_FOLDER / "data"

# Combined output files.
COMBINED_CSV_FILE = DATA_FOLDER / "five_commodities_combined.csv"
COMBINED_EXCEL_FILE = DATA_FOLDER / "five_commodities_combined.xlsx"


# Yahoo Finance commodity tickers.
COMMODITIES = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F",
    "Corn": "ZC=F"
}

def clean_columns(data: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Yahoo Finance column headings into simple column names.
    """

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


def download_one_commodity(
    commodity_name: str,
    ticker: str,
) -> pd.DataFrame:
    """
    Download three years of daily data for one commodity.
    """

    print(f"\nDownloading {commodity_name} ({ticker})...")

    data = yf.download(
        ticker,
        period="3y",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if data.empty:
        print(f"No data was returned for {commodity_name}.")
        return pd.DataFrame()

    data = clean_columns(data)

    # Convert the Date index into a normal column.
    data = data.reset_index()

    # Add identifying columns.
    data.insert(1, "Commodity", commodity_name)
    data.insert(2, "Ticker", ticker)

    print(f"{len(data)} rows downloaded successfully.")

    return data


def main() -> None:
    """
    Download all five commodities and save local files.
    """

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    all_commodities = []

    for commodity_name, ticker in COMMODITIES.items():

        data = download_one_commodity(
            commodity_name,
            ticker,
        )

        if data.empty:
            continue

        # Create a safe filename such as Crude_Oil.csv.
        safe_name = commodity_name.replace(" ", "_")

        individual_file = DATA_FOLDER / f"{safe_name}.csv"

        data.to_csv(
            individual_file,
            index=False,
        )

        print(f"Individual file saved: {individual_file.name}")

        all_commodities.append(data)

    if not all_commodities:
        print("\nNo commodity data was downloaded.")
        return

    combined_data = pd.concat(
        all_commodities,
        ignore_index=True,
    )

    # Arrange the dataset by commodity and date.
    combined_data = combined_data.sort_values(
        by=["Commodity", "Date"],
    ).reset_index(drop=True)

    # Save one combined CSV file.
    combined_data.to_csv(
        COMBINED_CSV_FILE,
        index=False,
    )

    # Save one combined Excel file.
    combined_data.to_excel(
        COMBINED_EXCEL_FILE,
        index=False,
        sheet_name="Commodity Data",
    )

    print("\n-----------------------------------")
    print("Download completed successfully.")
    print("-----------------------------------")

    print("Total rows:", len(combined_data))

    print("\nRows by commodity:")
    print(combined_data["Commodity"].value_counts())

    print("\nCombined CSV:")
    print(COMBINED_CSV_FILE)

    print("\nCombined Excel:")
    print(COMBINED_EXCEL_FILE)


if __name__ == "__main__":
    main()