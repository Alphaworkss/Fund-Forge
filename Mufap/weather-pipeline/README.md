# Weather Data Pipeline — Finalized

Collects Pakistan agriculture-region weather + live PMD flood/drought
alerts, and writes one Excel file you can open directly.

## What it collects (and why only this)

| Source | What | Why |
|---|---|---|
| NASA POWER | Daily temperature + rainfall for 10 curated Pakistani agriculture regions (Lahore, Faisalabad, Multan, Bahawalpur, Hyderabad, Sukkur, Larkana, Peshawar, Quetta, Islamabad) | These are the crop/commodity belts that actually matter for the fund advisor's climate-risk signal |
| PMD | Live flood/rain/drought advisory feed | Real-time shock/event risk |

**Not included by default:** NOAA (US-only, irrelevant here) and full
country-grid ERA5 (produces far more rows than useful in Excel). Both
remain available in `ingestion/` if you need them later — see
`docs/sources/`.

## Output

Running the pipeline produces **one file**: `storage/output/weather_data.xlsx`,
with three sheets:

1. **Weather Data** — `source, location, timestamp, metric_type, value, unit, collected_at`
2. **PMD Alerts** — `title, published, description, collected_at`
3. **Climate Risk Flags** — `location, date, flag_type, value, collected_at`
   (`flag_type` is one of `heatwave`, `flood_risk`, `drought`, `agriculture_impact`)

Every row has `collected_at` — the exact timestamp this script ran, so you
always know how fresh the data is.

## Setup (one time)

```bash
cd weather-pipeline
python -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install --default-timeout=120 -r requirements.txt
cp .env.example .env              # then open .env and set NOAA_USER_AGENT to a real email
```

## Run it manually

```bash
python main.py
```

Takes about a minute (10 locations x 1 API call each, plus the alerts
feed). You'll see progress printed per location. When it finishes:

```bash
python -c "import pandas as pd; print(pd.read_excel('storage/output/weather_data.xlsx', sheet_name=None).keys())"
```

Then just open `storage/output/weather_data.xlsx` in Excel to see it.

## Automate it (no Task Scheduler required)

A cross-platform automation script is included: `automate.py`.

Run once immediately:

```bash
python automate.py --once
```

Run as a long-lived daemon that schedules a daily job (default 06:00 UTC):

```bash
python automate.py --daemon --hour 6 --minute 0
```

Configuration (via `.env` or environment variables):

- `RUN_ERA5=true`  # (optional) enable the heavy Copernicus ERA5 fetch (opt-in)
- `LOOKBACK_DAYS=7` # how many days of recent history to fetch
- `SCHEDULE_HOUR=6` # hour (0-23 UTC) for the daily job
- `SCHEDULE_MINUTE=0` # minute for the daily job

Notes:
- The daemon must stay running (or be managed by a process manager such as systemd, NSSM, or any service runner) for scheduled jobs to execute.
- `automate.py` will run ingestion -> cleaning -> normalization -> feature extraction -> storage and write results to `storage/output/`.

## Run tests (checks the logic, not live data)

```bash
python -m pytest tests/ -v
```

## Project layout

```
weather-pipeline/
├── config/settings.py          # PAKISTAN_LOCATIONS, thresholds, env loading
├── ingestion/
│   ├── nasa_power.py           # point + regional NASA POWER (point mode used by default)
│   ├── pmd_scraper.py          # PMD live CAP alerts feed
│   ├── copernicus_ecmwf.py     # optional: full-grid ERA5 (not in default run)
│   └── noaa.py                 # optional: US-only, not in default run
├── cleaning/clean.py           # dedupe, range checks, UTC timestamps
├── normalization/normalize.py  # unify units + schema across sources
├── features/extract_features.py# heatwave/flood/drought/agriculture_impact
├── storage/
│   ├── excel_writer.py         # writes the final .xlsx (default output)
│   └── writer.py                # optional: parquet/sqlite for larger volumes
├── scheduler/run_daily.py      # APScheduler daily job (or use Task Scheduler/cron)
├── tests/                      # one file per stage + one integration test
├── docs/SCHEMA.md              # schema reference
├── docs/sources/*.md           # per-source notes
└── main.py                     # THE finalized script - run this
```
