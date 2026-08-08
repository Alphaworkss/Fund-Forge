"""
Automation orchestrator for the weather-pipeline.

Usage:
  # Run once immediately
  python automate.py --once

  # Run as a daemon process (keeps running) with daily job at configured time
  python automate.py --daemon

Environment (in .env or system env):
- RUN_ERA5 (optional) = "true" to enable the heavy Copernicus ERA5 fetch
- RUN_INTERVAL_HOURS (optional) = integer hours between runs if not using cron
- SCHEDULE_HOUR (optional) = hour of day (0-23) to run daily, default 6
- SCHEDULE_MINUTE (optional) = minute of hour to run daily, default 0
- LOOKBACK_DAYS (optional) = days of recent history to fetch, default 7

This script intentionally avoids OS task schedulers and runs an in-process scheduler
(APScheduler) so the same command works on Windows, macOS, or Linux.
"""

import importlib
import inspect
import argparse
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import os
import time

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import (
    DEFAULT_STATE, PAKISTAN_LOCATIONS, DEFAULT_LAT, DEFAULT_LON,
    PARQUET_PATH, EXCEL_PATH, SQLITE_PATH
)

# local stage modules
from ingestion import noaa, nasa_power, pmd_scraper, copernicus_ecmwf
from cleaning.clean import clean as clean_df
from normalization.normalize import normalize as normalize_df
from features.extract_features import (
    flag_heatwave, flag_flood_risk, flag_drought,
    agriculture_impact_score, energy_demand_impact_score,
)
from storage.writer import write_parquet, write_sqlite
from storage.excel_writer import write_excel


def _last_n_days_dates(n: int):
    end = datetime.utcnow().date()
    start = end - timedelta(days=n - 1)
    # return strings formatted how the ingestion modules expect (YYYYMMDD or ISO)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _build_excel_frames(normalized: pd.DataFrame, heatwaves: pd.DataFrame, floods: pd.DataFrame,
                        droughts: pd.DataFrame, agri: pd.DataFrame, energy: pd.DataFrame,
                        collected_at: str):
    weather_df = normalized[normalized["metric_type"].ne("alert")].copy() if not normalized.empty else pd.DataFrame()
    if not weather_df.empty:
        weather_df["collected_at"] = collected_at

    alerts_df = normalized[normalized["metric_type"].eq("alert")].copy() if not normalized.empty else pd.DataFrame()
    if not alerts_df.empty:
        alerts_df["collected_at"] = collected_at

    flag_rows = []
    if not heatwaves.empty:
        for _, row in heatwaves.iterrows():
            flag_rows.append({
                "location": row.get("location"),
                "date": row.get("date"),
                "flag_type": "heatwave",
                "value": bool(row.get("heatwave", False)),
                "collected_at": collected_at,
            })
    if not energy.empty:
        for _, row in energy.iterrows():
            flag_rows.append({
                "location": row.get("location"),
                "date": row.get("date"),
                "flag_type": "energy_demand_impact",
                "value": row.get("energy_demand_impact"),
                "collected_at": collected_at,
            })
    if not floods.empty:
        for _, row in floods.iterrows():
            flag_rows.append({
                "location": row.get("location"),
                "date": pd.Timestamp(row.get("timestamp")).date() if pd.notna(row.get("timestamp")) else None,
                "flag_type": "flood_risk",
                "value": bool(row.get("flood_risk", False)),
                "collected_at": collected_at,
            })
    if not droughts.empty:
        for _, row in droughts.iterrows():
            flag_rows.append({
                "location": row.get("location"),
                "date": pd.Timestamp(row.get("timestamp")).date() if pd.notna(row.get("timestamp")) else None,
                "flag_type": "drought",
                "value": bool(row.get("drought", False)),
                "collected_at": collected_at,
            })
    if not agri.empty:
        for _, row in agri.iterrows():
            flag_rows.append({
                "location": row.get("location"),
                "date": pd.Timestamp(row.get("timestamp")).date() if pd.notna(row.get("timestamp")) else None,
                "flag_type": "agriculture_impact",
                "value": row.get("agriculture_impact"),
                "collected_at": collected_at,
            })

    flags_df = pd.DataFrame(flag_rows)
    if not flags_df.empty:
        flags_df["collected_at"] = collected_at
    return weather_df, alerts_df, flags_df


def run_ingestion(lookback_days=7, run_era5=False):
    # Collect a list of dataframes from the various ingestion modules
    dfs = []
    collected_at = datetime.utcnow().isoformat()

    # 1) PMD alerts
    try:
        alerts = pmd_scraper.get_pmd_alerts()
        df_alerts = pmd_scraper.alerts_to_dataframe(alerts)
        df_alerts["collected_at"] = collected_at
        dfs.append(df_alerts)
    except Exception:
        print("PMD ingestion failed:")
        traceback.print_exc()

    # 2) NOAA (alerts + optional historical) - use DEFAULT_STATE
    try:
        raw_alerts = noaa.get_active_alerts(DEFAULT_STATE)
        df_noaa_alerts = noaa.alerts_to_dataframe(raw_alerts)
        df_noaa_alerts["collected_at"] = collected_at
        dfs.append(df_noaa_alerts)
    except Exception:
        print("NOAA ingestion failed:")
        traceback.print_exc()

    # 3) NASA POWER (point-based for curated Pakistan locations)
    try:
        start, end = _last_n_days_dates(lookback_days)
        for loc in PAKISTAN_LOCATIONS:
            raw = nasa_power.get_power_data(lat=loc["lat"], lon=loc["lon"], start=start, end=end)
            df_loc = nasa_power.power_to_dataframe(raw, location=loc["name"])
            df_loc["collected_at"] = collected_at
            dfs.append(df_loc)
    except Exception:
        print("NASA POWER ingestion failed:")
        traceback.print_exc()

    # 4) Copernicus / ECMWF ERA5 (optional - heavy). Only run if explicitly enabled.
    if run_era5:
        try:
            # default: a single recent month (last full month) to limit size
            today = datetime.utcnow().date()
            month = f"{today.year:04d}{today.month:02d}"
            # use a small test area by default to avoid huge requests; user can
            # override by calling copernicus_ecmwf.fetch_era5 manually.
            nc_path = copernicus_ecmwf.fetch_era5(year=str(today.year), month=f"{today.month:02d}", area=copernicus_ecmwf.TEST_AREA)
            df_era5 = copernicus_ecmwf.era5_to_dataframe(nc_path)
            if not df_era5.empty:
                df_era5["collected_at"] = collected_at
                dfs.append(df_era5)
        except Exception:
            print("Copernicus/ERA5 ingestion failed:")
            traceback.print_exc()

    # concat everything we got
    if not dfs:
        print("No ingestion outputs produced — nothing to do")
        return

    raw = pd.concat(dfs, ignore_index=True, sort=False)
    print(f"Ingestion produced {len(raw)} rows across {raw.source.nunique() if 'source' in raw.columns else 'N/A'} sources")

    # Cleaning
    try:
        cleaned = clean_df(raw)
    except Exception:
        print("Cleaning stage failed:")
        traceback.print_exc()
        cleaned = raw

    # Normalization: normalize per-source where useful
    normalized_frames = []
    if "source" in cleaned.columns:
        for src, grp in cleaned.groupby("source"):
            try:
                nf = normalize_df(grp, source=src)
                normalized_frames.append(nf)
            except Exception:
                print(f"Normalization failed for source {src}:")
                traceback.print_exc()
    else:
        try:
            normalized_frames.append(normalize_df(cleaned, source="UNKNOWN"))
        except Exception:
            print("Normalization failed for combined dataframe:")
            traceback.print_exc()

    normalized = pd.concat(normalized_frames, ignore_index=True, sort=False) if normalized_frames else pd.DataFrame()
    if not normalized.empty:
        normalized["collected_at"] = collected_at
    print(f"Normalized -> {len(normalized)} rows")

    # Feature extraction
    try:
        # ensure timestamp is datetime
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True, errors="coerce")
        heatwaves = flag_heatwave(normalized)
        floods = flag_flood_risk(normalized)
        droughts = flag_drought(normalized)

        agri = agriculture_impact_score(droughts)
        energy = energy_demand_impact_score(heatwaves)

    except Exception:
        print("Feature extraction failed:")
        traceback.print_exc()
        heatwaves = floods = droughts = agri = energy = pd.DataFrame()

    # Storage
    try:
        if not normalized.empty:
            write_parquet(normalized, path=PARQUET_PATH)
            # also write to sqlite for easy querying if configured
            try:
                write_sqlite(normalized, db_path=SQLITE_PATH)
            except Exception:
                print("SQLite write failed (optional):")
                traceback.print_exc()

            weather_df, alerts_df, flags_df = _build_excel_frames(
                normalized=normalized,
                heatwaves=heatwaves,
                floods=floods,
                droughts=droughts,
                agri=agri,
                energy=energy,
                collected_at=collected_at,
            )
            write_excel(weather_df, alerts_df, flags_df, path=EXCEL_PATH)
    except Exception:
        print("Storage stage failed:")
        traceback.print_exc()

    # Output feature artifacts as parquet as well
    try:
        out_dir = Path(PARQUET_PATH).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        heatwaves.to_parquet(out_dir / "features_heatwaves.parquet", index=False)
        floods.to_parquet(out_dir / "features_floods.parquet", index=False)
        droughts.to_parquet(out_dir / "features_droughts.parquet", index=False)
        agri.to_parquet(out_dir / "features_agriculture.parquet", index=False)
        energy.to_parquet(out_dir / "features_energy.parquet", index=False)
        print("Feature artifacts written to storage/output/")
    except Exception:
        print("Writing feature artifacts failed:")
        traceback.print_exc()

    print("Pipeline run complete")


def main_loop(lookback_days=7, run_era5=False):
    # single immediate run
    run_ingestion(lookback_days=lookback_days, run_era5=run_era5)


def start_daemon(lookback_days=7, run_era5=False, hour=6, minute=0):
    sched = BackgroundScheduler()
    # schedule daily at hour:minute UTC (user can set local time via env)
    trigger = CronTrigger(hour=hour, minute=minute)

    def job():
        print(f"Scheduled job running at {datetime.utcnow().isoformat()}")
        run_ingestion(lookback_days=lookback_days, run_era5=run_era5)

    sched.add_job(job, trigger=trigger, id="daily_ingest")
    sched.start()
    print(f"Scheduler started — daily job at {hour:02d}:{minute:02d} UTC")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down scheduler...")
        sched.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate and run weather-pipeline end-to-end")
    parser.add_argument("--once", action="store_true", help="Run once immediately and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as a background process and schedule daily jobs")
    parser.add_argument("--lookback-days", type=int, default=int(os.getenv("LOOKBACK_DAYS", "7")), help="Days of historical data to fetch")
    parser.add_argument("--run-era5", action="store_true", default=(os.getenv("RUN_ERA5", "false").lower() == "true"), help="Enable heavy ERA5 fetch (opt-in)")
    parser.add_argument("--hour", type=int, default=int(os.getenv("SCHEDULE_HOUR", "6")), help="Hour of day (UTC) to run scheduled job")
    parser.add_argument("--minute", type=int, default=int(os.getenv("SCHEDULE_MINUTE", "0")), help="Minute of hour to run scheduled job")

    args = parser.parse_args()

    if args.once:
        main_loop(lookback_days=args.lookback_days, run_era5=args.run_era5)
        sys.exit(0)

    if args.daemon:
        start_daemon(lookback_days=args.lookback_days, run_era5=args.run_era5, hour=args.hour, minute=args.minute)
        sys.exit(0)

    # default: run once
    main_loop(lookback_days=args.lookback_days, run_era5=args.run_era5)
