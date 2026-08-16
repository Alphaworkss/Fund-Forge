"""
api.py

Handles all communication with the MUFAP website.
"""

import time
import requests

from logger import logger
from config import (
    GET_AMC_URL,
    GET_FUNDS_URL,
    HISTORICAL_NAV_URL,
    MAX_RETRIES,
    REQUEST_TIMEOUT
)


class MufapAPI:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({

            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36",

            "Accept":
                "application/json, text/javascript, */*; q=0.01",

            "Referer":
                "https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=3",

            "X-Requested-With":
                "XMLHttpRequest"
        })

        # Initialize ASP.NET session
        self.initialize_session()

    # ====================================================
    # Initialize Session
    # ====================================================

    def initialize_session(self):

        print("\nInitializing MUFAP session...")

        try:

            response = self.session.get(

                HISTORICAL_NAV_URL + "?tab=3",

                timeout=REQUEST_TIMEOUT

            )

            print("Session Initialized")
            print("Status:", response.status_code)

            print("\nCookies:")

            for cookie in self.session.cookies:

                print(cookie.name, "=", cookie.value)

        except Exception as e:

            print("Session Initialization Failed")

            print(e)

    # ====================================================
    # Internal GET Request
    # ====================================================

    def _get(self, url, params=None):

        retries = 0

        while retries < MAX_RETRIES:

            try:

                print("\n===================================")
                print("GET:", url)

                if params:
                    print("Parameters:")
                    print(params)

                response = self.session.get(

                    url,

                    params=params,

                    timeout=REQUEST_TIMEOUT

                )

                print("Status Code:", response.status_code)

                print("Final URL:", response.url)

                print(
                    "Content-Type:",
                    response.headers.get("Content-Type")
                )

                print("\nFirst 500 Characters:\n")

                print(response.text[:500])

                response.raise_for_status()

                return response

            except Exception as e:

                retries += 1

                print("\nERROR")

                print(e)

                logger.error(str(e))

                print(f"\nRetry {retries}/{MAX_RETRIES}")

                time.sleep(2)

        return None

    # ====================================================
    # Get AMC List
    # ====================================================

    def get_amc_list(self):

        print("\nDownloading AMC List...")

        response = self._get(GET_AMC_URL)

        if response is None:

            return None

        try:

            return response.json()

        except Exception as e:

            print("\nJSON ERROR")

            print(e)

            return None

    # ====================================================
    # Get Funds of One AMC
    # ====================================================

    def get_funds(self, amc_id):

        print("\nDownloading Fund List...")

        params = {

            "AMCId": amc_id

        }

        response = self._get(

            GET_FUNDS_URL,

            params=params

        )

        if response is None:

            return None

        try:

            return response.json()

        except Exception as e:

            print("\nJSON ERROR")

            print(e)

            return None

    # ====================================================
    # Historical NAV
    # ====================================================

    def get_historical_nav(

        self,

        amc_id,

        fund_id,

        start_date,

        end_date

    ):

        print("\nDownloading Historical NAV...")

        params = {

            "tab": 3,

            "AMCId": amc_id,

            "fundId": fund_id,

            "datefrom": start_date,

            "datetill": end_date

        }

        response = self._get(

            HISTORICAL_NAV_URL,

            params=params

        )

        if response is None:

            return None

        return response.text