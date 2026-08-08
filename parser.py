from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def clean(text):

    if text is None:
        return ""

    return text.replace("\n", " ").replace("\t", " ").strip()


def timestamp():

    return datetime.now()


# ========================================================
# PERFORMANCE SUMMARY
# ========================================================

def parse_performance(html):

    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id="table_id")

    if table is None:
        print("Performance table not found.")
        return pd.DataFrame()

    rows = []

    body = table.find("tbody")

    if body is None:
        print("Performance tbody missing.")
        return pd.DataFrame()

    for tr in body.find_all("tr"):

        if "fund-block" not in tr.get("class", []):
            continue

        tds = tr.find_all("td")

        if len(tds) < 14:
            continue

        link = tr.find("a")

        fund_id = ""

        fund_name = ""

        if link:

            fund_name = clean(link.text)

            href = link.get("href", "")

            if "FundID=" in href:

                fund_id = href.split("FundID=")[1]

        row = {

            "Timestamp": timestamp(),

            "FundID": fund_id,

            "Fund Name": fund_name,

            "Date": clean(tds[4].text),

            "NAV": clean(tds[5].text),

            "15 Days": clean(tds[6].text),

            "30 Days": clean(tds[7].text),

            "90 Days": clean(tds[8].text),

            "180 Days": clean(tds[9].text),

            "270 Days": clean(tds[10].text),

            "365 Days": clean(tds[11].text),

            "730 Days": clean(tds[12].text),

            "1095 Days": clean(tds[13].text),

            "Since Inception": clean(tds[14].text) if len(tds) > 14 else ""

        }

        rows.append(row)

    df = pd.DataFrame(rows)

    print(df.head())

    print(df.shape)

    return df


# ========================================================
# DAILY NAV
# ========================================================

def parse_nav(html):

    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id="table_id")

    if table is None:
        print("NAV table not found.")
        return pd.DataFrame()

    headers = []

    thead = table.find("thead")

    for th in thead.find_all("th"):
        headers.append(clean(th.text))

    body = table.find("tbody")

    rows = []

    for tr in body.find_all("tr"):

        values = [clean(td.text) for td in tr.find_all("td")]

        if len(values) == 0:
            continue

        while len(values) < len(headers):
            values.append("")

        row = dict(zip(headers, values))

        row["Timestamp"] = timestamp()

        link = tr.find("a")

        if link:

            href = link.get("href", "")

            if "FundID=" in href:
                row["FundID"] = href.split("FundID=")[1]

            row["Fund Name"] = clean(link.text)

        rows.append(row)

    df = pd.DataFrame(rows)

    print(df.head())

    print(df.shape)

    return df


# ========================================================
# AUM
# ========================================================

def parse_aum(html):

    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id="table_id")

    if table is None:
        print("AUM table not found.")
        return pd.DataFrame()

    headers = []

    thead = table.find("thead")

    for th in thead.find_all("th"):
        headers.append(clean(th.text))

    body = table.find("tbody")

    rows = []

    for tr in body.find_all("tr"):

        values = [clean(td.text) for td in tr.find_all("td")]

        if len(values) == 0:
            continue

        while len(values) < len(headers):
            values.append("")

        row = dict(zip(headers, values))

        row["Timestamp"] = timestamp()

        link = tr.find("a")

        if link:

            href = link.get("href", "")

            if "FundID=" in href:
                row["FundID"] = href.split("FundID=")[1]

            row["Fund Name"] = clean(link.text)

        rows.append(row)

    df = pd.DataFrame(rows)

    print(df.head())

    print(df.shape)

    return df