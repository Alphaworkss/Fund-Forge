"""
Historical data pull for MODEL TRAINING: 3 years of monthly temperature +
rainfall for every curated Pakistan location.

Uses NASA POWER's daily endpoint (already proven reliable in this project)
and aggregates to monthly with pandas, rather than NASA's separate monthly
endpoint - this avoids risking another API-response-format mistake, since
the daily endpoint's shape is already confirmed working in this project.

PMD is NOT included here: its feed only contains CURRENTLY ACTIVE alerts -
there is no historical archive available through it. If you need
historical flood/drought EVENT records (not just weather readings) for
training, that needs a different source entirely (e.g. a disaster
database) - ask if you want that added later.

This is a SEPARATE script from main.py on purpose: main.py is the live/
current daily pipeline (run often, small output), this is the one-time-ish
bulk historical pull (run rarely, larger output, takes longer).

Run: python fetch_historical.py
Output: storage/output/historical_weather_data.xlsx
  - "Monthly Data" sheet: location, year, month, metric_type, value, unit, collected_at
  - "Monthly Flags" sheet: location, year, month, flag_type, value, collected_at
"""
import os
import pandas as pd
from config.settings import PAKISTAN_LOCATIONS, HEATWAVE_THRESHOLD_C, DROUGHT_LOW_RAINFALL_MM_30D
from ingestion.nasa_power import get_power_data, power_to_dataframe
from cleaning.clean import clean
from normalization.normalize import normalize
from storage.excel_writer import _strip_timezones

YEARS_BACK = 3


def collect_historical_daily() -> pd.DataFrame:
    """Pull YEARS_BACK years of daily data for every curated location."""
    end = pd.Timestamp.now("UTC")
    start = end - pd.DateOffset(years=YEARS_BACK)
    frames = []
    for loc in PAKISTAN_LOCATIONS:
        print(f"  fetching {YEARS_BACK}-year history for {loc['name']}...")
        raw = get_power_data(
            lat=loc["lat"], lon=loc["lon"],
            start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"),
        )
        df = power_to_dataframe(raw, location=loc["name"])
        if not df.empty:
            frames.append(df)
        else:
            print(f"    WARNING: no data returned for {loc['name']}")
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    return normalize(combined, source="NASA_POWER")


def aggregate_monthly(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse daily readings into monthly averages (temperature) and
    monthly totals (rainfall) per location."""
    df = daily_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month

    rows = []
    temp = df[df.metric_type == "temperature_c"]
    monthly_temp = temp.groupby(["location", "year", "month"])["value"].mean().reset_index()
    for _, r in monthly_temp.iterrows():
        rows.append({
            "location": r["location"], "year": int(r["year"]), "month": int(r["month"]),
            "metric_type": "temperature_c_avg", "value": round(r["value"], 2), "unit": "C",
        })

    rain = df[df.metric_type == "rainfall_mm"]
    monthly_rain = rain.groupby(["location", "year", "month"])["value"].sum().reset_index()
    for _, r in monthly_rain.iterrows():
        rows.append({
            "location": r["location"], "year": int(r["year"]), "month": int(r["month"]),
            "metric_type": "rainfall_mm_total", "value": round(r["value"], 2), "unit": "mm",
        })

    return pd.DataFrame(rows)


def build_monthly_flags(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple starting-point flags at monthly resolution. NOTE: the daily
    heatwave threshold (40C, config.settings.HEATWAVE_THRESHOLD_C) is a
    single-day peak threshold and too strict for a MONTHLY AVERAGE, so
    'hot_month' uses a lower bar (threshold - 10) as a rough starting
    point - inspect the real distribution in your data and tune this once
    you have it, rather than trusting this number blindly.
    """
    rows = []
    temp = monthly_df[monthly_df.metric_type == "temperature_c_avg"]
    for _, r in temp.iterrows():
        rows.append({
            "location": r["location"], "year": r["year"], "month": r["month"],
            "flag_type": "hot_month", "value": bool(r["value"] >= HEATWAVE_THRESHOLD_C - 10),
        })

    rain = monthly_df[monthly_df.metric_type == "rainfall_mm_total"]
    for _, r in rain.iterrows():
        rows.append({
            "location": r["location"], "year": r["year"], "month": r["month"],
            "flag_type": "dry_month", "value": bool(r["value"] <= DROUGHT_LOW_RAINFALL_MM_30D),
        })

    return pd.DataFrame(rows)


def run_historical_pipeline():
    collected_at = pd.Timestamp.now("UTC").isoformat()
    print(f"Historical pull started at {collected_at} ({YEARS_BACK} years back)")
    print("This will take a few minutes - one API call per location.")

    daily = collect_historical_daily()
    if daily.empty:
        print("No data collected - check source connectivity.")
        return

    print("Cleaning...")
    cleaned = clean(daily)

    print("Aggregating to monthly...")
    monthly = aggregate_monthly(cleaned)
    monthly["collected_at"] = collected_at

    flags = build_monthly_flags(monthly)
    flags["collected_at"] = collected_at

    path = "storage/output/historical_weather_data.xlsx"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    monthly_out = _strip_timezones(monthly)
    flags_out = _strip_timezones(flags)

    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            monthly_out.to_excel(writer, sheet_name="Monthly Data", index=False)
            flags_out.to_excel(writer, sheet_name="Monthly Flags", index=False)
    except PermissionError:
        fallback = path.replace(".xlsx", f"_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        print(f"WARNING: {path} is open elsewhere. Saving to {fallback} instead - close the original and rerun to update it directly.")
        with pd.ExcelWriter(fallback, engine="openpyxl") as writer:
            monthly_out.to_excel(writer, sheet_name="Monthly Data", index=False)
            flags_out.to_excel(writer, sheet_name="Monthly Flags", index=False)
        path = fallback

    print(f"Wrote {path}")
    print(f"  Monthly Data: {len(monthly_out)} rows")
    print(f"  Monthly Flags: {len(flags_out)} rows")


if __name__ == "__main__":
    run_historical_pipeline()
