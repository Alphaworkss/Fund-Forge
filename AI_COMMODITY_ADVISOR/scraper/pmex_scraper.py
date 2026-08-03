from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


URL = "https://mportal.pmex.com.pk/mt5bonew/Home/OHLCReport"

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_FOLDER / "data"

ALL_DATA_FILE = DATA_FOLDER / "pmex_all_data.xlsx"
FINAL_FILE = DATA_FOLDER / "five_commodities.xlsx"


COMMODITY_KEYWORDS = {
    "Gold": ["GOLD"],
    "Silver": ["SILVER"],
    "Crude Oil": ["CRUDE", "WTI"],
    "Natural Gas": ["NGAS", "NATGAS", "NATURALGAS"],
    "Copper": ["COPPER"],
}


def identify_commodity(symbol):
    """Identify the commodity using its PMEX symbol."""

    symbol = str(symbol).upper().replace(" ", "")

    for commodity, keywords in COMMODITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in symbol:
                return commodity

    return None


def main():
    """Open PMEX, extract the OHLC table and save it to Excel."""

    DATA_FOLDER.mkdir(exist_ok=True)

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    try:
        print("Opening PMEX OHLC Report...")

        driver.get(URL)

        print("Please select a date range manually.")
        print("Then click the Show button on the website.")

        input(
            "After the table appears completely, "
            "return here and press Enter..."
        )

        sleep(3)

        print("Reading the table...")

        tables = pd.read_html(
            StringIO(driver.page_source)
        )

        print("Tables found:", len(tables))

        if not tables:
            raise ValueError("No table was found.")

        market_table = None

        for table in tables:

            columns_text = " ".join(
                str(column).lower()
                for column in table.columns
            )

            if (
                "symbol" in columns_text
                and "open" in columns_text
                and "close" in columns_text
            ):
                market_table = table.copy()
                break

        if market_table is None:
            raise ValueError(
                "The PMEX OHLC table could not be identified."
            )

        market_table.columns = [
            str(column).strip()
            for column in market_table.columns
        ]

        print("Columns found:")
        print(market_table.columns.tolist())

        market_table.to_excel(
            ALL_DATA_FILE,
            index=False,
            sheet_name="All PMEX Data"
        )

        symbol_column = next(
            column
            for column in market_table.columns
            if "symbol" in column.lower()
        )

        market_table["Commodity"] = market_table[
            symbol_column
        ].apply(identify_commodity)

        final_data = market_table[
            market_table["Commodity"].notna()
        ].copy()

        if final_data.empty:
            raise ValueError(
                "The five selected commodities were not found."
            )

        final_data.insert(
            0,
            "Scraped At",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        column_order = final_data.columns.tolist()
        column_order.remove("Commodity")
        column_order.insert(1, "Commodity")

        final_data = final_data[column_order]

        final_data.to_excel(
            FINAL_FILE,
            index=False,
            sheet_name="Five Commodities"
        )

        print("\nScraping completed successfully.")
        print("Rows collected:", len(final_data))

        print("\nCommodities found:")
        print(final_data["Commodity"].value_counts())

        print("\nFiles saved:")
        print(ALL_DATA_FILE)
        print(FINAL_FILE)

    except Exception as error:
        print("\nScraping failed.")
        print("Error:", error)

    finally:
        input("\nPress Enter to close Chrome...")
        driver.quit()


if __name__ == "__main__":
    main()