"""
export_excel.py — Excel export

Exports the current contents of the wallet-metrics database to an
Excel workbook (wallet_metrics.xlsx by default) — one sheet per table
— for anyone on the team who'd rather look at a spreadsheet than query
SQLite directly.

Same design choice as ../GitHub/export_excel.py: regenerates the whole
file from SQLite on every run rather than merging into an existing
.xlsx — SQLite already handles dedup/upserts (see storage.py).

IMPORTANT: close wallet_metrics.xlsx in Excel before running this —
Excel locks the file while it's open, and writing to it will raise
PermissionError.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

EXCEL_PATH = str(Path(__file__).resolve().parent / "wallet_metrics.xlsx")


def export_to_excel(conn: sqlite3.Connection, excel_path: str = EXCEL_PATH) -> bool:
    raw_df = pd.read_sql_query("SELECT * FROM wallet_metrics_raw ORDER BY coin, date, metric", conn)
    features_df = pd.read_sql_query(
        "SELECT * FROM wallet_metrics_features ORDER BY coin, date, metric", conn
    )
    common_df = pd.read_sql_query("SELECT * FROM wallet_metrics_common ORDER BY id", conn)

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            raw_df.to_excel(writer, sheet_name="raw", index=False)
            features_df.to_excel(writer, sheet_name="features", index=False)
            common_df.to_excel(writer, sheet_name="common", index=False)
        logger.info(
            "Exported %d raw rows, %d feature rows, and %d common-schema rows to %s",
            len(raw_df), len(features_df), len(common_df), excel_path,
        )
        return True
    except PermissionError:
        logger.error(
            "Could not write %s — it's probably still open in Excel. Close it and re-run.",
            excel_path,
        )
        return False
