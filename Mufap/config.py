"""
Configuration for FundForge Historical NAV Scraper
"""

from datetime import datetime

# ======================================================
# MUFAP URLs
# ======================================================

BASE_URL = "https://www.mufap.com.pk"

HISTORICAL_NAV_URL = (
    "https://www.mufap.com.pk/Industry/IndustryStatDaily"
)

GET_AMC_URL = (
    "https://www.mufap.com.pk/AMC/GetAMCList"
)

GET_FUNDS_URL = (
    "https://www.mufap.com.pk/AMC/GetFundNameByAMC"
)

# ======================================================
# Date Range
# ======================================================

START_DATE = "2016-08-01"

END_DATE = datetime.today().strftime("%Y-%m-%d")

# ======================================================
# Target AMCs
# ======================================================

TARGET_AMCS = [

    "ABL Asset Management Company Limited",

    "Al Habib Asset Management Limited",

    "Al Meezan Investment Management Limited",

    "Alfalah Asset Management Limited",

    "EFU Life Insurance Limited",

    "Faysal Asset Management Limited",

    "HBL Asset Management Limited",

    "UBL Fund Managers Limited"

]

# ======================================================
# Output
# ======================================================

CSV_FILE = "data/mufap_historical_nav.csv"

# ======================================================
# Retry Settings
# ======================================================

MAX_RETRIES = 3

REQUEST_TIMEOUT = 60

SLEEP_TIME = 1

# ======================================================
# Logging
# ======================================================

LOG_FILE = "logs/scraper.log"