from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


def parse_nav_table(table_html, amc_name):

    if not table_html:
        return pd.DataFrame()

    soup = BeautifulSoup(table_html, "html.parser")

    table = soup.find("table")

    if table is None:
        return pd.DataFrame()

    rows = table.find_all("tr")

    records = []

    for row in rows:

        cols = [
            td.get_text(" ", strip=True)
            for td in row.find_all("td")
        ]

        # Historical rows contain exactly 13 columns
        if len(cols) != 13:
            continue

        records.append({

            "AMC": amc_name,
            "Sector": cols[0],
            "Fund": cols[1],
            "Category": cols[2],
            "Inception_Date": cols[3],
            "Offer": cols[4],
            "Repurchase": cols[5],
            "NAV": cols[6],
            "Validity_Date": cols[7],
            "Front_End_Load": cols[8],
            "Back_End_Load": cols[9],
            "Contingent_Load": cols[10],
            "Market_Price": cols[11],
            "Trustee": cols[12],
            "Scrape_Time": datetime.now()

        })

    df = pd.DataFrame(records)

    if df.empty:
        print("No historical rows found.")
        return df

    # -----------------------------
    # Convert numeric columns
    # -----------------------------

    numeric = [
        "Offer",
        "Repurchase",
        "NAV",
        "Front_End_Load",
        "Back_End_Load",
        "Contingent_Load",
        "Market_Price"
    ]

    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # Convert dates
    # -----------------------------

    df["Inception_Date"] = pd.to_datetime(
        df["Inception_Date"],
        errors="coerce"
    )

    df["Validity_Date"] = pd.to_datetime(
        df["Validity_Date"],
        errors="coerce"
    ).dt.normalize()


    # -----------------------------
    # Remove duplicate rows
    # -----------------------------

    before = len(df)

    df.drop_duplicates(
        subset=[
            "Fund",
            "Validity_Date"
        ],
        inplace=True
    )

    after = len(df)

   
    df.sort_values(
        "Validity_Date",
        inplace=True
    )

    df.reset_index(
        drop=True,
        inplace=True
    )

    return df