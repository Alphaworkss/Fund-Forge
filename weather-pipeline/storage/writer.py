"""
Storage stage: write the normalized, cleaned data out. Parquet is the
default (compact, fast, easy for other teams to read). SQLite/Postgres
is available if the team wants something queryable/shared.
"""
import os
import pandas as pd
from sqlalchemy import create_engine


def write_parquet(df: pd.DataFrame, path: str = "storage/output/weather_records.parquet"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Parquet (pyarrow) requires consistent column types. Some rows are
    # free-text alerts (value is str) while other rows are numeric readings.
    # To avoid conversion errors we serialize the 'value' column to string
    # for parquet output. Numeric consumers can still read from SQLite or
    # re-cast the column when needed.
    df_copy = df.copy()
    if "value" in df_copy.columns:
        df_copy["value"] = df_copy["value"].astype(str)

    df_copy.to_parquet(path, partition_cols=["source"], index=False)
    print(f"Wrote {len(df_copy)} rows to {path}")


def write_sqlite(df: pd.DataFrame, db_path: str = "sqlite:///storage/output/weather.db",
                  table: str = "weather_records"):
    os.makedirs(os.path.dirname(db_path.replace("sqlite:///", "")) or ".", exist_ok=True)
    engine = create_engine(db_path)
    df.to_sql(table, engine, if_exists="replace", index=False)
    print(f"Wrote {len(df)} rows to {db_path} (table: {table})")
