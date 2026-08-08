"""
Single entry point for the pipeline.

Use this file as the only script you need to run manually or schedule.
It can fetch live data or historical data with the same code path:

        python main.py --mode live
        python main.py --mode historical --years-back 3

Live mode collects the configured sources, cleans and normalizes the rows,
derives risk flags, and writes one Excel workbook. Historical mode pulls
daily NASA POWER data and aggregates it to monthly output.

Some of the requested outputs are direct source fields and some are
derived indicators:
- Temperature and rainfall: NASA POWER
- Weather alerts: PMD live CAP feed, optional NOAA alerts for US zones
- Flood / heatwave / drought / agriculture impact / energy demand impact:
    derived from the cleaned weather series
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

from cleaning.clean import clean
from config.settings import DEFAULT_STATE, PAKISTAN_LOCATIONS
from features.extract_features import (
        agriculture_impact_score,
        energy_demand_impact_score,
        flag_drought,
        flag_flood_risk,
        flag_heatwave,
)
from ingestion.nasa_power import get_power_data, power_to_dataframe
from ingestion.noaa import alerts_to_dataframe as noaa_alerts_to_dataframe
from ingestion.noaa import get_active_alerts
from ingestion.pmd_scraper import (
        alerts_to_dataframe as pmd_alerts_to_dataframe,
        get_pmd_alerts,
)
from normalization.normalize import normalize
from storage.excel_writer import _strip_timezones, write_excel

DEFAULT_LIVE_SOURCES = ("nasa_power", "pmd")
AVAILABLE_LIVE_SOURCES = {"nasa_power", "pmd", "noaa"}


def collect_weather(days_back: int = 14) -> pd.DataFrame:
    """Pull recent daily temperature and rainfall for each curated location."""
    end = pd.Timestamp.now("UTC")
    start = end - pd.Timedelta(days=days_back)
    frames = []
    for loc in PAKISTAN_LOCATIONS:
        print(f"  fetching NASA POWER data for {loc['name']}...")
        raw = get_power_data(
            lat=loc["lat"], lon=loc["lon"],
            start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"),
        )
        df = power_to_dataframe(raw, location=loc["name"])
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    return normalize(combined, source="NASA_POWER")


def collect_alerts(sources: tuple[str, ...] = DEFAULT_LIVE_SOURCES, state: str = DEFAULT_STATE) -> pd.DataFrame:
    """Pull alert feeds requested by the live source list."""
    frames = []

    if "pmd" in sources:
        print("  fetching PMD alerts feed...")
        alerts = get_pmd_alerts()
        df = pmd_alerts_to_dataframe(alerts)
        if not df.empty:
            frames.append(normalize(df, source="PMD"))

    if "noaa" in sources:
        print(f"  fetching NOAA alerts for state {state}...")
        alerts = get_active_alerts(state)
        df = noaa_alerts_to_dataframe(alerts)
        if not df.empty:
            frames.append(normalize(df, source="NOAA"))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def build_flags(weather_df: pd.DataFrame, collected_at: str) -> pd.DataFrame:
    """Long-format table: one row per (location, date, flag_type)."""
    rows = []

    if (weather_df["metric_type"] == "temperature_c").any():
        heatwave = flag_heatwave(weather_df)
        for _, r in heatwave.iterrows():
            rows.append({
                "location": r["location"], "date": r["date"],
                "flag_type": "heatwave", "value": bool(r["heatwave"]),
                "collected_at": collected_at,
            })

        energy = energy_demand_impact_score(heatwave)
        for _, r in energy.iterrows():
            rows.append({
                "location": r["location"], "date": r["date"],
                "flag_type": "energy_demand_impact", "value": r["energy_demand_impact"],
                "collected_at": collected_at,
            })

    if (weather_df["metric_type"] == "rainfall_mm").any():
        flood = flag_flood_risk(weather_df)
        for _, r in flood.iterrows():
            rows.append({
                "location": r["location"], "date": r["timestamp"].date(),
                "flag_type": "flood_risk", "value": bool(r["flood_risk"]),
                "collected_at": collected_at,
            })

        drought = flag_drought(weather_df)
        agri = agriculture_impact_score(drought)
        for _, r in agri.iterrows():
            rows.append({
                "location": r["location"], "date": r["timestamp"].date(),
                "flag_type": "drought", "value": bool(r["drought"]),
                "collected_at": collected_at,
            })
            rows.append({
                "location": r["location"], "date": r["timestamp"].date(),
                "flag_type": "agriculture_impact", "value": r["agriculture_impact"],
                "collected_at": collected_at,
            })

    return pd.DataFrame(rows)


def run_pipeline(days_back: int = 14, sources: tuple[str, ...] = DEFAULT_LIVE_SOURCES, state: str = DEFAULT_STATE):
    collected_at = pd.Timestamp.now("UTC").isoformat()
    print(f"Pipeline run started at {collected_at}")

    print("Collecting weather data...")
    weather_raw = collect_weather(days_back=days_back)

    print("Collecting alerts...")
    alerts_raw = collect_alerts(sources=sources, state=state)

    frames = [f for f in [weather_raw, alerts_raw] if not f.empty]
    if not frames:
        print("No data collected - check source connectivity.")
        return

    combined = pd.concat(frames, ignore_index=True)
    cleaned = clean(combined)
    cleaned["collected_at"] = collected_at

    weather_df = cleaned[cleaned["source"] == "NASA_POWER"].copy()

    alerts_df = cleaned[cleaned["source"] == "PMD"].copy()
    alerts_df = alerts_df.rename(columns={"location": "title", "value": "description"})
    alerts_df = alerts_df[["title", "timestamp", "description", "collected_at"]]
    alerts_df = alerts_df.rename(columns={"timestamp": "published"})

    flags_df = build_flags(weather_df, collected_at)

    write_excel(weather_df, alerts_df, flags_df)
    print("Done.")


# Historical data pull for model training: daily NASA POWER data aggregated
# to monthly output. This stays in the same entry point so automation can use
# one script with different modes instead of a separate helper.
YEARS_BACK = 3


def collect_historical_daily(years_back: int = YEARS_BACK) -> pd.DataFrame:
    """Pull years_back years of daily data for every curated location."""
    end = pd.Timestamp.now("UTC")
    start = end - pd.DateOffset(years=years_back)
    frames = []
    for loc in PAKISTAN_LOCATIONS:
        print(f"  fetching {years_back}-year history for {loc['name']}...")
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
    """Collapse daily readings into monthly averages and totals."""
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
    """Simple starting-point flags at monthly resolution."""
    from config.settings import HEATWAVE_THRESHOLD_C, DROUGHT_LOW_RAINFALL_MM_30D

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


def run_historical_pipeline(years_back: int = YEARS_BACK):
    collected_at = pd.Timestamp.now("UTC").isoformat()
    print(f"Historical pull started at {collected_at} ({years_back} years back)")
    print("This will take a few minutes - one API call per location.")

    daily = collect_historical_daily(years_back=years_back)
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


def _parse_sources(raw_sources: list[str] | None) -> tuple[str, ...]:
    if not raw_sources:
        return DEFAULT_LIVE_SOURCES

    parsed = tuple(source.strip().lower() for source in raw_sources if source.strip())
    invalid = sorted(set(parsed) - AVAILABLE_LIVE_SOURCES)
    if invalid:
        raise ValueError(
            f"Unsupported source(s): {', '.join(invalid)}. "
            f"Valid options are: {', '.join(sorted(AVAILABLE_LIVE_SOURCES))}"
        )
    return parsed


def main():
    parser = argparse.ArgumentParser(description="Run the weather pipeline")
    parser.add_argument("--mode", choices=("live", "historical"), default="live")
    parser.add_argument("--days-back", type=int, default=14, help="Live mode lookback window in days")
    parser.add_argument("--years-back", type=int, default=YEARS_BACK, help="Historical mode lookback window in years")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=list(DEFAULT_LIVE_SOURCES),
        help="Live sources to include: nasa_power, pmd, noaa",
    )
    parser.add_argument(
        "--noaa-state",
        default=DEFAULT_STATE,
        help="NOAA state or zone code for live alerts",
    )
    args = parser.parse_args()

    if args.mode == "historical":
        run_historical_pipeline(years_back=args.years_back)
        return

    sources = _parse_sources(args.sources)
    run_pipeline(days_back=args.days_back, sources=sources, state=args.noaa_state)


if __name__ == "__main__":
    main()
