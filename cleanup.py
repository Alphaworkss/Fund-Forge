import pandas as pd

CSV = "data/MUFAP_Historical_NAV.csv"

print("Loading CSV...")

df = pd.read_csv(CSV, low_memory=False)

print("Rows Before :", len(df))

# --------------------------
# Dates
# --------------------------

df["Validity_Date"] = pd.to_datetime(
    df["Validity_Date"],
    errors="coerce"
)

df["Inception_Date"] = pd.to_datetime(
    df["Inception_Date"],
    errors="coerce"
)

# --------------------------
# Remove duplicates
# --------------------------

df.drop_duplicates(
    subset=[
        "AMC",
        "Fund",
        "Validity_Date"
    ],
    inplace=True
)

# --------------------------
# Sort
# --------------------------

df.sort_values(
    [
        "AMC",
        "Fund",
        "Validity_Date"
    ],
    inplace=True
)

# --------------------------
# Save
# --------------------------

df.to_csv(
    CSV,
    index=False,
    encoding="utf-8-sig"
)

print("Rows After :", len(df))
print("Cleanup Completed.")