"""
NOAA has two useful endpoints for this project:

1. NWS Alerts API (api.weather.gov) - no key needed, gives live alerts
   (storms, heatwaves, flood warnings) for a US state/zone.
2. NCEI Climate Data Online (CDO) - needs a free token, gives historical
   temperature/rainfall records.

Run this file directly to sanity-check both calls:  python -m ingestion.noaa
"""
import requests
import pandas as pd
from config.settings import NOAA_USER_AGENT, NOAA_CDO_TOKEN


def get_active_alerts(state: str = "PA") -> list[dict]:
    """Fetch currently active NWS alerts for a US state/zone code."""
    url = f"https://api.weather.gov/alerts/active?area={state}"
    headers = {"User-Agent": NOAA_USER_AGENT}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()["features"]  # list of alert dicts


def alerts_to_dataframe(alerts: list[dict]) -> pd.DataFrame:
    """Turn raw alert JSON into rows matching our unified schema shape."""
    rows = []
    for a in alerts:
        props = a.get("properties", {})
        rows.append({
            "source": "NOAA",
            "location": props.get("areaDesc", "unknown"),
            "timestamp": props.get("sent"),
            "metric_type": "alert",
            "value": props.get("event"),   # e.g. "Flood Warning"
            "unit": None,
        })
    return pd.DataFrame(rows)


def get_historical_daily(station_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Historical daily temperature/precipitation from NCEI CDO.
    station_id example: 'GHCND:USW00094728' (find via NCEI station search).
    Dates as 'YYYY-MM-DD'. Requires NOAA_CDO_TOKEN in .env.
    """
    if not NOAA_CDO_TOKEN:
        raise RuntimeError("NOAA_CDO_TOKEN is not set in .env — request one at ncdc.noaa.gov/cdo-web/token")

    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
    headers = {"token": NOAA_CDO_TOKEN}
    params = {
        "datasetid": "GHCND",
        "stationid": station_id,
        "startdate": start_date,
        "enddate": end_date,
        "units": "metric",
        "limit": 1000,
    }
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])

    rows = []
    for item in results:
        # datatype 'TMAX'/'TMIN' = temperature (tenths of C from GHCND, already
        # metric-converted here since we asked for units=metric); 'PRCP' = rainfall mm
        if item["datatype"] in ("TMAX", "TMIN"):
            metric_type, unit = "temperature_c", "C"
        elif item["datatype"] == "PRCP":
            metric_type, unit = "rainfall_mm", "mm"
        else:
            continue
        rows.append({
            "source": "NOAA",
            "location": station_id,
            "timestamp": item["date"],
            "metric_type": metric_type,
            "value": item["value"],
            "unit": unit,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    alerts = get_active_alerts("PA")
    print(f"Fetched {len(alerts)} active alerts for PA")
    print(alerts_to_dataframe(alerts).head())
