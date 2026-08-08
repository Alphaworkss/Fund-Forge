import cdsapi
import xarray as xr
import pandas as pd
import zipfile
import glob
import os

# [north, west, south, east] bounding boxes
PAKISTAN_BBOX = [37.5, 60.5, 23.5, 77.5]        # whole country - big, slow request
TEST_AREA = [34.0, 72.8, 33.5, 73.3]            # small box around Islamabad - fast, for testing


def fetch_era5(year: str, month: str, area: list[float], out_path: str = "era5_data.nc") -> str:
    """
    Downloads a NetCDF file covering the given area/month and returns its path.
    NOTE: larger areas and longer date ranges take much longer to process on
    Copernicus's servers (this is a queued request, not instant) — start
    with TEST_AREA and a single month before requesting the full country.
    """
    c = cdsapi.Client()
    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": ["2m_temperature", "total_precipitation"],
            "year": year,
            "month": month,
            "day": [f"{d:02d}" for d in range(1, 29)],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": area,
            "format": "netcdf",
        },
        out_path,
    )
    return out_path


def _load_dataset(path: str) -> xr.Dataset:
    """
    Copernicus's newer backend sometimes returns a zip file full of
    separate .nc files (one per variable) instead of a single NetCDF file,
    even though the filename still ends in .nc. Detect and handle both cases.
    """
    if zipfile.is_zipfile(path):
        extract_dir = path + "_extracted"
        with zipfile.ZipFile(path) as z:
            z.extractall(extract_dir)
        nc_files = sorted(glob.glob(os.path.join(extract_dir, "*.nc")))
        if not nc_files:
            raise RuntimeError(f"Downloaded zip at {path} contained no .nc files")
        datasets = [xr.open_dataset(f) for f in nc_files]
        return xr.merge(datasets, compat="override")
    return xr.open_dataset(path)


def era5_to_dataframe(nc_path: str) -> pd.DataFrame:
    """
    Load the downloaded NetCDF grid (or zip of NetCDFs, see _load_dataset)
    and reshape it into our unified schema. Each grid cell becomes its own
    'location', written as 'lat,lon' so it stays lightweight and
    sortable/filterable later.
    """
    ds = _load_dataset(nc_path)
    df = ds.to_dataframe().reset_index()

    # Copernicus has changed these column names between backend versions
    # (e.g. 'time' -> 'valid_time'), so detect whichever is actually present
    # instead of assuming one fixed name.
    time_col = next((c for c in ("time", "valid_time") if c in df.columns), None)
    lat_col = next((c for c in ("latitude", "lat") if c in df.columns), None)
    lon_col = next((c for c in ("longitude", "lon") if c in df.columns), None)
    if time_col is None or lat_col is None or lon_col is None:
        raise RuntimeError(
            f"Unrecognized column names in ERA5 output: {list(df.columns)} "
            "(expected some form of time/latitude/longitude)"
        )

    df["location"] = df[lat_col].round(2).astype(str) + "," + df[lon_col].round(2).astype(str)

    frames = []
    if "t2m" in df.columns:
        temp = df[["location", time_col, "t2m"]].rename(columns={time_col: "timestamp"})
        temp["value"] = temp.pop("t2m") - 273.15  # Kelvin -> Celsius
        temp["metric_type"] = "temperature_c"
        temp["unit"] = "C"
        frames.append(temp)
    if "tp" in df.columns:
        precip = df[["location", time_col, "tp"]].rename(columns={time_col: "timestamp"})
        precip["value"] = precip.pop("tp") * 1000  # meters -> mm
        precip["metric_type"] = "rainfall_mm"
        precip["unit"] = "mm"
        frames.append(precip)

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        out["source"] = "ECMWF_ERA5"
    return out


if __name__ == "__main__":
    print("Requesting a small test area around Islamabad for one month...")
    path = fetch_era5(year="2026", month="01", area=PAKISTAN_BBOX)
    df = era5_to_dataframe(path)
    print(f"Got {len(df)} rows covering {df['location'].nunique()} grid cells")
    print(df.head(10))
