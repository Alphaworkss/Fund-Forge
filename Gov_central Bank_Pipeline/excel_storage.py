import os
import pandas as pd

EXCEL_COLUMNS = [
    "id", "source", "source_type", "url", "title", "description",
    "full_text", "published_time", "fetched_date", "fetched_time",
    "ingestion_time", "country", "region",
    "language", "sector", "event_type", "importance_score",
    "sentiment_score", "confidence_score", "keywords",
]


def _listify(value):
    """Turn a list into a semicolon-separated string for Excel storage."""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return value


def load_existing_ids(path: str) -> set:
    """Read IDs already saved so we can skip duplicates on re-runs."""
    if not os.path.exists(path):
        return set()
    df = pd.read_excel(path, engine="openpyxl")
    if "id" not in df.columns:
        return set()
    return set(df["id"].astype(str).tolist())


def append_records(path: str, records: list):
    """Append new records to the Excel file, creating it if it doesn't exist."""
    if not records:
        return 0

    rows = []
    for r in records:
        row = {col: _listify(r.get(col)) for col in EXCEL_COLUMNS}
        rows.append(row)

    new_df = pd.DataFrame(rows, columns=EXCEL_COLUMNS)

    if os.path.exists(path):
        existing_df = pd.read_excel(path, engine="openpyxl")
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined.drop_duplicates(subset="id", keep="first", inplace=True)
    else:
        combined = new_df

    combined.to_excel(path, index=False, engine="openpyxl")
    return len(new_df)