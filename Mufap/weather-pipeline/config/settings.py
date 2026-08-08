"""
Central place for constants, thresholds, and endpoints.
Everything here should be safe to commit — actual secrets live in .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root into os.environ

# --- Secrets / IDs pulled from environment ---
NOAA_USER_AGENT = os.getenv("NOAA_USER_AGENT", "weather-pipeline (set_your_email@example.com)")
NOAA_CDO_TOKEN = os.getenv("NOAA_CDO_TOKEN", "")

# --- Default location (used when a caller doesn't specify one) ---
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "33.6844"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "73.0479"))
DEFAULT_STATE = os.getenv("DEFAULT_STATE", "PA")  # NOAA state/zone code for alerts

# --- Feature-extraction thresholds (rule-based, tune later) ---
HEATWAVE_THRESHOLD_C = 40
HEATWAVE_CONSECUTIVE_DAYS = 3
FLOOD_RAINFALL_MM_24H = 100
DROUGHT_LOW_RAINFALL_MM_30D = 15  # total rainfall over 30 days below this = drought flag

# --- Valid ranges used by the cleaning stage ---
VALID_RANGES = {
    "temperature_c": (-90, 60),
    "rainfall_mm": (0, 1000),
}

# --- Storage ---
PARQUET_PATH = "storage/output/weather_records.parquet"
SQLITE_PATH = "sqlite:///storage/output/weather.db"
EXCEL_PATH = "storage/output/weather_data.xlsx"

# --- Curated locations: Pakistan's major agriculture/commodity-relevant
PAKISTAN_LOCATIONS = [
    {"name": "Lahore",      "lat": 31.5204, "lon": 74.3587},  # Punjab - wheat/rice belt
    {"name": "Faisalabad",  "lat": 31.4180, "lon": 73.0790},  # Punjab - cotton/wheat
    {"name": "Multan",      "lat": 30.1575, "lon": 71.5249},  # Punjab - cotton/mango
    {"name": "Bahawalpur",  "lat": 29.3956, "lon": 71.6722},  # Punjab - cotton
    {"name": "Hyderabad",   "lat": 25.3960, "lon": 68.3578},  # Sindh - rice/sugarcane
    {"name": "Sukkur",      "lat": 27.7052, "lon": 68.8574},  # Sindh - rice/wheat
    {"name": "Larkana",     "lat": 27.5590, "lon": 68.2123},  # Sindh - wheat
    {"name": "Peshawar",    "lat": 34.0151, "lon": 71.5249},  # KPK
    {"name": "Quetta",      "lat": 30.1798, "lon": 66.9750},  # Balochistan - fruit
    {"name": "Islamabad",   "lat": 33.6844, "lon": 73.0479},  # baseline/capital
]
