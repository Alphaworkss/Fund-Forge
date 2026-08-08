# Unified Weather Record Schema

Every row written to storage, regardless of source, has these columns:

| Field | Type | Notes |
|---|---|---|
| `source` | string | One of `NOAA`, `NASA_POWER`, `ECMWF_ERA5`, `PMD` |
| `location` | string | Convention TBD — currently free-text (station id, city name, region). Decide once whether to key by lat/lon or place name and update all `ingestion/*.py` files to match. |
| `timestamp` | datetime (UTC) | Always converted to UTC in the cleaning stage |
| `metric_type` | string | `temperature_c`, `rainfall_mm`, or `alert` |
| `value` | float or string | Numeric for `temperature_c`/`rainfall_mm`; free text for `alert` (e.g. "Flood Warning") |
| `unit` | string or null | `C`, `mm`, or null for alerts |

## Valid ranges (enforced in `cleaning/clean.py`)
- `temperature_c`: -90 to 60
- `rainfall_mm`: 0 to 1000

## Derived features (from `features/extract_features.py`)
- `heatwave`: bool, daily max temp >= 40C for 3+ consecutive days
- `flood_risk`: bool, rolling 24h rainfall >= 100mm
- `drought`: bool, rolling 30-day rainfall <= 15mm
- `agriculture_impact`: "high"/"low", derived from `drought`
- `energy_demand_impact`: "spike_likely"/"normal", derived from `heatwave`

Update this file whenever a field, threshold, or convention changes — this
is the single source of truth the prediction-engine team will read.
