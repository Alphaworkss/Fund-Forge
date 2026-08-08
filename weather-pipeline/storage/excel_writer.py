"""
Writes the final, human-readable Excel workbook. This is the file you'll
actually open and look at - the parquet output (storage/writer.py) is a
separate, optional raw-data store for larger volumes if you ever need it.

Every sheet includes a 'collected_at' column recording exactly when this
script fetched/scraped the data, so you always know how fresh it is.
"""
import os
import pandas as pd
from config.settings import EXCEL_PATH


def _strip_timezones(df: pd.DataFrame) -> pd.DataFrame:
    """Excel/openpyxl rejects timezone-aware datetime columns outright.
    Convert any tz-aware datetime column to naive UTC before writing."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) and df[col].dt.tz is not None:
            df[col] = df[col].dt.tz_convert("UTC").dt.tz_localize(None)
    return df


def write_excel(weather_df: pd.DataFrame, alerts_df: pd.DataFrame,
                 flags_df: pd.DataFrame, path: str = EXCEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    weather_df = _strip_timezones(weather_df)
    alerts_df = _strip_timezones(alerts_df)
    flags_df = _strip_timezones(flags_df)

    try:
        _write_workbook(weather_df, alerts_df, flags_df, path)
    except PermissionError:
        # Windows locks the file while it's open in Excel. Rather than
        # crash the whole pipeline, save to a timestamped fallback name so
        # no data is lost - close the original file and rerun to update it.
        fallback = path.replace(".xlsx", f"_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        print(f"WARNING: {path} is open in Excel (or another program) and couldn't be overwritten.")
        print(f"         Close it, then rerun to update it directly. Saving to {fallback} instead.")
        _write_workbook(weather_df, alerts_df, flags_df, fallback)
        print(f"Wrote Excel workbook to {fallback}")
        print(f"  Weather Data: {len(weather_df)} rows")
        print(f"  PMD Alerts: {len(alerts_df)} rows")
        print(f"  Climate Risk Flags: {len(flags_df)} rows")
        return

    print(f"Wrote Excel workbook to {path}")
    print(f"  Weather Data: {len(weather_df)} rows")
    print(f"  PMD Alerts: {len(alerts_df)} rows")
    print(f"  Climate Risk Flags: {len(flags_df)} rows")


def _write_workbook(weather_df, alerts_df, flags_df, path):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        weather_df.to_excel(writer, sheet_name="Weather Data", index=False)
        alerts_df.to_excel(writer, sheet_name="PMD Alerts", index=False)
        flags_df.to_excel(writer, sheet_name="Climate Risk Flags", index=False)
