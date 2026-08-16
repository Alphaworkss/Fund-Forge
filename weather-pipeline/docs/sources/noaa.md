# NOAA (NOT used in the default pipeline for this project)

- NWS Alerts API (api.weather.gov) only covers the United States - it will
  never return anything meaningful for Pakistan. Kept in ingestion/noaa.py
  for reference only, in case a future version of this project needs
  US-market weather context (e.g. for commodities traded on US exchanges).
- NCEI CDO (historical data) does technically include some Pakistani
  GHCND stations, but coverage is sparse compared to ERA5's full grid -
  not worth pursuing unless a specific gap in ERA5 shows up.
