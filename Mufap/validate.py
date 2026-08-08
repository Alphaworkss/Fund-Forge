"""
validate.py

Validates the final MUFAP Historical NAV dataset.
"""

import pandas as pd

CSV_FILE = "data/MUFAP_Historical_NAV.csv"

print("=" * 60)
print("Loading CSV...")
print("=" * 60)

df = pd.read_csv(
    CSV_FILE,
    low_memory=False
)

# -------------------------------------------------------
# Convert Date Columns
# -------------------------------------------------------

df["Validity_Date"] = pd.to_datetime(
    df["Validity_Date"],
    errors="coerce"
)

df["Inception_Date"] = pd.to_datetime(
    df["Inception_Date"],
    errors="coerce"
)

# -------------------------------------------------------
# Dataset Summary
# -------------------------------------------------------

print("\n" + "=" * 60)
print("DATASET SUMMARY")
print("=" * 60)

print(f"TOTAL ROWS            : {len(df):,}")
print(f"TOTAL AMCs            : {df['AMC'].nunique()}")
print(f"TOTAL FUNDS           : {df['Fund'].nunique()}")

print(f"\nEARLIEST DATE         : {df['Validity_Date'].min().date()}")
print(f"LATEST DATE           : {df['Validity_Date'].max().date()}")

# -------------------------------------------------------
# Missing Values
# -------------------------------------------------------

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing = df.isna().sum()
print(missing[missing > 0])

# -------------------------------------------------------
# Duplicate Records
# -------------------------------------------------------

duplicates = df.duplicated(
    subset=[
        "AMC",
        "Fund",
        "Validity_Date"
    ]
).sum()

print("\n" + "=" * 60)
print("DUPLICATE CHECK")
print("=" * 60)

print(f"Duplicate Rows : {duplicates}")

# -------------------------------------------------------
# Invalid Dates
# -------------------------------------------------------

invalid_dates = df["Validity_Date"].isna().sum()

print("\n" + "=" * 60)
print("DATE VALIDATION")
print("=" * 60)

print(f"Invalid Validity Dates : {invalid_dates}")

if invalid_dates > 0:

    print("\nRows with Invalid Dates:\n")

    print(
        df.loc[
            df["Validity_Date"].isna(),
            ["AMC", "Fund", "Validity_Date"]
        ].head(20)
    )

# -------------------------------------------------------
# Funds Per AMC
# -------------------------------------------------------

print("\n" + "=" * 60)
print("FUNDS PER AMC")
print("=" * 60)

print(
    df.groupby("AMC")["Fund"]
      .nunique()
      .sort_values(ascending=False)
)

# -------------------------------------------------------
# Rows Per AMC
# -------------------------------------------------------

print("\n" + "=" * 60)
print("ROWS PER AMC")
print("=" * 60)

print(
    df.groupby("AMC")
      .size()
      .sort_values(ascending=False)
)

# -------------------------------------------------------
# Rows Per Fund
# -------------------------------------------------------

print("\n" + "=" * 60)
print("TOP 20 LARGEST FUNDS")
print("=" * 60)

print(
    df.groupby("Fund")
      .size()
      .sort_values(ascending=False)
      .head(20)
)

print("\n" + "=" * 60)
print("VALIDATION COMPLETED")
print("=" * 60)