import requests
import pandas as pd

# [west, south, east, north] - NASA POWER's regional endpoint uses this order
PAKISTAN_BOUNDS = {"west": 60.5, "south": 23.5, "east": 77.5, "north": 37.5}


def get_power_data(lat: float, lon: float, start: str, end: str) -> dict:
    """Single point. start/end format: 'YYYYMMDD'."""
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": lon, "latitude": lat,
        "start": start, "end": end,
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["properties"]["parameter"]


def power_to_dataframe(raw: dict, location: str) -> pd.DataFrame:
    """Reshape single-point {"T2M": {date: val}, ...} dict into long-format rows."""
    rows = []
    for date_str, temp_c in raw.get("T2M", {}).items():
        rows.append({
            "source": "NASA_POWER", "location": location, "timestamp": date_str,
            "metric_type": "temperature_c", "value": temp_c, "unit": "C",
        })
    for date_str, rain_mm in raw.get("PRECTOTCORR", {}).items():
        rows.append({
            "source": "NASA_POWER", "location": location, "timestamp": date_str,
            "metric_type": "rainfall_mm", "value": rain_mm, "unit": "mm",
        })
    return pd.DataFrame(rows)


def _fetch_regional_single_param(bounds: dict, parameter: str, start: str, end: str) -> dict:
    """
    NASA POWER's regional endpoint only allows ONE parameter per request
    (unlike the point endpoint, which allows several) - so temperature and
    rainfall must be fetched as two separate calls.
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/regional"
    params = {
        "parameters": parameter,
        "community": "AG",
        "latitude-min": bounds["south"], "latitude-max": bounds["north"],
        "longitude-min": bounds["west"], "longitude-max": bounds["east"],
        "start": start, "end": end,
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def _chunk_bounds(bounds: dict, max_size: float = 4.0) -> list[dict]:
    """
    NASA POWER's regional endpoint caps requests at 4.5 x 4.5 degrees
    (~100 grid points) - a request bigger than that returns a 422 error.
    Split a larger bounding box into a grid of sub-boxes under that limit
    (4.0 used instead of 4.5 to leave a safety margin).
    """
    import math
    lat_span = bounds["north"] - bounds["south"]
    lon_span = bounds["east"] - bounds["west"]
    n_lat = max(1, math.ceil(lat_span / max_size))
    n_lon = max(1, math.ceil(lon_span / max_size))

    chunks = []
    lat_step = lat_span / n_lat
    lon_step = lon_span / n_lon
    for i in range(n_lat):
        for j in range(n_lon):
            chunks.append({
                "south": bounds["south"] + i * lat_step,
                "north": bounds["south"] + (i + 1) * lat_step,
                "west": bounds["west"] + j * lon_step,
                "east": bounds["west"] + (j + 1) * lon_step,
            })
    return chunks


def get_power_regional_data(bounds: dict, start: str, end: str) -> dict:
    """
    Grid/regional data over a bounding box, e.g. PAKISTAN_BOUNDS.
    start/end format: 'YYYYMMDD'. Returns {"T2M": <merged json>, "PRECTOTCORR": <merged json>}.

    Automatically splits bounds larger than 4.5x4.5 degrees into multiple
    requests and merges the results, since NASA POWER rejects oversized
    regional requests with a 422 error. For the full Pakistan bounding box
    this means ~20 sub-requests per parameter (~40 total) - expect this to
    take a few minutes, and don't run it on every pipeline execution; cache
    the result or run it on a slower schedule than the point-based sources.
    """
    chunks = _chunk_bounds(bounds)
    print(f"Splitting region into {len(chunks)} sub-requests to stay under NASA POWER's 4.5x4.5 degree limit...")

    t2m_features, precip_features = [], []
    for idx, chunk in enumerate(chunks, 1):
        print(f"  chunk {idx}/{len(chunks)}: {chunk}")
        t2m_resp = _fetch_regional_single_param(chunk, "T2M", start, end)
        precip_resp = _fetch_regional_single_param(chunk, "PRECTOTCORR", start, end)
        t2m_features.extend(t2m_resp.get("features", []))
        precip_features.extend(precip_resp.get("features", []))

    return {
        "T2M": {"features": t2m_features},
        "PRECTOTCORR": {"features": precip_features},
    }


def _extract_regional_rows(raw_response: dict, param_key: str, metric_type: str, unit: str,
                            value_transform=lambda v: v) -> list[dict]:
    features = raw_response.get("features", [])
    rows = []
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        location = f"{round(lat, 2)},{round(lon, 2)}"
        series = feature.get("properties", {}).get("parameter", {}).get(param_key, {})
        for date_str, value in series.items():
            rows.append({
                "source": "NASA_POWER", "location": location, "timestamp": date_str,
                "metric_type": metric_type, "value": value_transform(value), "unit": unit,
            })
    return rows


def regional_power_to_dataframe(raw: dict) -> pd.DataFrame:
    """Reshape the two regional responses into our unified schema."""
    rows = _extract_regional_rows(raw["T2M"], "T2M", "temperature_c", "C")
    rows += _extract_regional_rows(raw["PRECTOTCORR"], "PRECTOTCORR", "rainfall_mm", "mm")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Point test (Islamabad):")
    raw = get_power_data(lat=33.6844, lon=73.0479, start="20260101", end="20260107")
    print(power_to_dataframe(raw, location="Islamabad").head())

    print("\nRegional test (small Pakistan sub-box, 3 days):")
    # NOTE: regional requests are heavier than point requests. Start with a
    # small box and short date range - the full PAKISTAN_BOUNDS over a long
    # date range can be slow or hit size limits; chunk by month if needed.
    small_box = {"west": 72.5, "south": 33.0, "east": 73.5, "north": 34.0}
    raw_regional = get_power_regional_data(small_box, start="20260101", end="20260103")
    df = regional_power_to_dataframe(raw_regional)
    print(f"Got {len(df)} rows covering {df['location'].nunique()} grid cells")
    print(df.head(10))
