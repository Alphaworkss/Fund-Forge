"""
preprocess.py

FundForge
MUFAP NAV Machine Learning Preprocessing

Reads the cleaned MUFAP historical NAV CSV,
cleans the data fund-wise, removes invalid records,
and creates a model-ready dataset.
"""

import os
import pandas as pd


# -------------------------------------------------------
# File Paths
# -------------------------------------------------------

INPUT_FILE = os.path.join(
    "data",
    "MUFAP_Historical_NAV.csv"
)

OUTPUT_FOLDER = "training_data"

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "MUFAP_NAV_Preprocessed.csv"
)


# -------------------------------------------------------
# Main Preprocessing Function
# -------------------------------------------------------

def preprocess():

    print("=" * 70)
    print("FundForge - MUFAP NAV Preprocessing")
    print("=" * 70)

    # ---------------------------------------------------
    # Load Dataset
    # ---------------------------------------------------

    print("\nLoading CSV...")

    df = pd.read_csv(
        INPUT_FILE,
        low_memory=False
    )

    print(f"Original Rows : {len(df):,}")
    print(f"Original Columns : {len(df.columns)}")

    # ---------------------------------------------------
    # Required Columns
    # ---------------------------------------------------

    required_columns = [
        "AMC",
        "FundID",
        "Sector",
        "FundType",
        "CategoryID",
        "Fund",
        "Category",
        "Inception_Date",
        "Offer",
        "Repurchase",
        "NAV",
        "Validity_Date",
        "Front_End_Load",
        "Back_End_Load",
        "Contingent_Load",
        "Market_Price",
        "Trustee"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        print("\nERROR")
        print("Missing columns:")

        for col in missing_columns:
            print("-", col)

        return

    # ---------------------------------------------------
    # Remove Scrape_Time
    # ---------------------------------------------------

    if "Scrape_Time" in df.columns:

        df.drop(
            columns=["Scrape_Time"],
            inplace=True
        )

    # ---------------------------------------------------
    # Convert Dates
    # ---------------------------------------------------

    print("\nConverting dates...")

    df["Validity_Date"] = pd.to_datetime(
        df["Validity_Date"],
        errors="coerce"
    )

    df["Inception_Date"] = pd.to_datetime(
        df["Inception_Date"],
        errors="coerce"
    )

    # ---------------------------------------------------
    # Remove Invalid Dates
    # ---------------------------------------------------

    invalid_dates = df["Validity_Date"].isna().sum()

    print(
        f"Invalid Validity Dates Removed : {invalid_dates}"
    )

    df = df[
        df["Validity_Date"].notna()
    ].copy()

    # ---------------------------------------------------
    # Convert Numeric Columns
    # ---------------------------------------------------

    numeric_columns = [

        "Offer",

        "Repurchase",

        "NAV",

        "Front_End_Load",

        "Back_End_Load",

        "Contingent_Load",

        "Market_Price"

    ]

    print("\nConverting numeric columns...")

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # ---------------------------------------------------
    # Remove Rows Without NAV
    # ---------------------------------------------------

    missing_nav = df["NAV"].isna().sum()

    print(
        f"Rows Without NAV Removed : {missing_nav}"
    )

    df = df[
        df["NAV"].notna()
    ].copy()

    # ---------------------------------------------------
    # Remove Invalid NAV Values
    # ---------------------------------------------------

    invalid_nav = (
        df["NAV"] <= 0
    ).sum()

    print(
        f"Invalid NAV Rows Removed : {invalid_nav}"
    )

    df = df[
        df["NAV"] > 0
    ].copy()

    # ---------------------------------------------------
    # Sort Dataset
    # ---------------------------------------------------

    print("\nSorting data...")

    df.sort_values(
        [
            "FundID",
            "Validity_Date"
        ],
        inplace=True
    )

    # ---------------------------------------------------
    # Remove Duplicate Fund/Date Records
    # ---------------------------------------------------

    before_duplicates = len(df)

    df.drop_duplicates(
        subset=[
            "FundID",
            "Validity_Date"
        ],
        keep="last",
        inplace=True
    )

    duplicates_removed = (
        before_duplicates - len(df)
    )

    print(
        f"Duplicate Fund/Date Rows Removed : "
        f"{duplicates_removed}"
    )

    # ---------------------------------------------------
    # Reset Index
    # ---------------------------------------------------

    df.reset_index(
        drop=True,
        inplace=True
    )

    # ---------------------------------------------------
    # Create Output Folder
    # ---------------------------------------------------

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    # ---------------------------------------------------
    # Save
    # ---------------------------------------------------

    print("\nSaving preprocessed dataset...")

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ---------------------------------------------------
    # Summary
    # ---------------------------------------------------

    print("\n" + "=" * 70)
    print("PREPROCESSING COMPLETED")
    print("=" * 70)

    print(
        f"Final Rows       : {len(df):,}"
    )

    print(
        f"Total Funds      : {df['FundID'].nunique():,}"
    )

    print(
        f"Total AMCs       : {df['AMC'].nunique():,}"
    )

    print(
        f"Earliest Date    : "
        f"{df['Validity_Date'].min().date()}"
    )

    print(
        f"Latest Date      : "
        f"{df['Validity_Date'].max().date()}"
    )

    print(
        f"\nSaved To         : {OUTPUT_FILE}"
    )

    print("=" * 70)


# -------------------------------------------------------
# Run
# -------------------------------------------------------

if __name__ == "__main__":

    preprocess()