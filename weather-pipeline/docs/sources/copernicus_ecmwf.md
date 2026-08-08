# Copernicus CDS / ECMWF ERA5

- Requires account registration + accepting the dataset license (done manually
  in the browser on the dataset page, not via code) before first use.
- As of 2026, auth uses a single Personal Access Token from
  https://cds.climate.copernicus.eu/profile, saved to .cdsapirc:
    url: https://cds.climate.copernicus.eu/api
    key: <token>
  (Windows path: C:\Users\<you>\.cdsapirc — older UID:KEY format is deprecated.)
- Data returned as NetCDF — read with xarray (netCDF4 engine; cfgrib not
  needed since we're not requesting GRIB format).
- Requests are QUEUED server-side, not instant — larger areas/date ranges can
  take significantly longer. Always test with a small area first
  (see TEST_AREA in ingestion/copernicus_ecmwf.py) before requesting the
  full Pakistan bounding box.
- Data is grid-based: each (lat, lon) cell becomes its own 'location' value,
  formatted as "lat,lon".
- Quirks: none else discovered yet — update this file as you find them.
