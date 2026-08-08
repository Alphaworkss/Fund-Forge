"""
Feature extraction: turn cleaned, normalized time series into event-level
features the prediction engine wants: heatwave, flood risk, drought,
agriculture impact, energy demand impact. Starts rule-based; swap in ML later.
"""
import pandas as pd
from config.settings import (
    HEATWAVE_THRESHOLD_C, HEATWAVE_CONSECUTIVE_DAYS,
    FLOOD_RAINFALL_MM_24H, DROUGHT_LOW_RAINFALL_MM_30D,
)


def flag_heatwave(df: pd.DataFrame, threshold_c=HEATWAVE_THRESHOLD_C,
                   consecutive_days=HEATWAVE_CONSECUTIVE_DAYS) -> pd.DataFrame:
    temp = df[df.metric_type == "temperature_c"]
    daily_max = temp.groupby([temp.timestamp.dt.date, "location"]).value.max().reset_index()
    daily_max = daily_max.rename(columns={"timestamp": "date"})
    daily_max["is_hot"] = daily_max["value"] >= threshold_c

    # streak = consecutive hot days per location
    daily_max["streak"] = (
        daily_max.groupby("location")["is_hot"]
        .apply(lambda s: s.groupby((~s).cumsum()).cumsum())
        .reset_index(drop=True)
    )
    daily_max["heatwave"] = daily_max["streak"] >= consecutive_days
    return daily_max


def flag_flood_risk(df: pd.DataFrame, rainfall_mm_24h=FLOOD_RAINFALL_MM_24H) -> pd.DataFrame:
    rain = df[df.metric_type == "rainfall_mm"].sort_values("timestamp").set_index("timestamp")
    rolling = rain.groupby("location")["value"].rolling("24h").sum().reset_index()
    rolling["flood_risk"] = rolling["value"] >= rainfall_mm_24h
    return rolling


def flag_drought(df: pd.DataFrame, low_rainfall_mm_30d=DROUGHT_LOW_RAINFALL_MM_30D) -> pd.DataFrame:
    rain = df[df.metric_type == "rainfall_mm"].sort_values("timestamp").set_index("timestamp")
    rolling = rain.groupby("location")["value"].rolling("30D").sum().reset_index()
    rolling["drought"] = rolling["value"] <= low_rainfall_mm_30d
    return rolling


def agriculture_impact_score(drought_df: pd.DataFrame) -> pd.DataFrame:
    """Simple derived score: drought flag -> high impact, else low. Refine later."""
    out = drought_df.copy()
    out["agriculture_impact"] = out["drought"].map({True: "high", False: "low"})
    return out


def energy_demand_impact_score(heatwave_df: pd.DataFrame) -> pd.DataFrame:
    """Simple derived score: heatwave flag -> likely demand spike. Refine later."""
    out = heatwave_df.copy()
    out["energy_demand_impact"] = out["heatwave"].map({True: "spike_likely", False: "normal"})
    return out
