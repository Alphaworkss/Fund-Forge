"""
csv_handler.py

Handles saving scraped NAV data into a single CSV file.
"""

import os

DATA_FOLDER = "data"

CSV_FILE = os.path.join(
    DATA_FOLDER,
    "MUFAP_Historical_NAV.csv"
)


def save_dataframe(df):
    """
    Append dataframe directly to CSV.
    Much faster than reading/re-writing
    the entire CSV every time.
    """

    if df.empty:
        print("No data to save.")
        return

    os.makedirs(DATA_FOLDER, exist_ok=True)

    file_exists = os.path.exists(CSV_FILE)

    df.to_csv(
        CSV_FILE,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig"
    )

    if file_exists:
        print(f"Appended {len(df)} rows.")
    else:
        print(f"Created CSV with {len(df)} rows.")