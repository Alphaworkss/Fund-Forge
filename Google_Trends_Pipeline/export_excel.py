"""
export_excel.py — Excel export

Exports the current contents of the database to an Excel workbook
(alt_data.xlsx by default), one sheet for the finished features and one
for the raw collected data, for anyone on the team who'd rather look at
a spreadsheet than query SQLite directly.

Design choice: this regenerates the WHOLE Excel file from SQLite on
every run, rather than trying to append/merge new rows into an existing
.xlsx. SQLite already handles deduplication and upserts correctly (see
storage.py) — re-exporting the full current dataset each time is simpler
and safer than reimplementing that merge logic against Excel, and the
end result is the same: an Excel file that reflects the latest state
every time the pipeline runs.

IMPORTANT: close alt_data.xlsx in Excel before the pipeline runs. Excel
locks the file while it's open, and Python can't write to a locked file
— you'll get a PermissionError if you forget and it's still open.
"""

import logging
import sqlite3

import pandas as pd

logger = logging.getLogger(__name__)

EXCEL_PATH = "alt_data.xlsx"


def export_to_excel(conn: sqlite3.Connection, excel_path: str = EXCEL_PATH) -> None:
    features_df = pd.read_sql_query(
        "SELECT * FROM google_trends_features ORDER BY keyword, date", conn
    )
    raw_df = pd.read_sql_query(
        "SELECT * FROM google_trends_raw ORDER BY keyword, date", conn
    )
    common_df = pd.read_sql_query(
        "SELECT * FROM google_trends_common ORDER BY id", conn
    )

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            features_df.to_excel(writer, sheet_name="features", index=False)
            raw_df.to_excel(writer, sheet_name="raw", index=False)
            common_df.to_excel(writer, sheet_name="common", index=False)
        logger.info(
            "Exported %d feature rows and %d common-schema rows to %s",
            len(features_df), len(common_df), excel_path,
        )
    except PermissionError:
        logger.error(
            "Could not write %s — it's probably still open in Excel. "
            "Close it and re-run.",
            excel_path,
        )
        