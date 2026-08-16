"""
daily_updater.py

Downloads ONLY the latest NAV of every fund.
"""

from datetime import datetime, timedelta
import pandas as pd

from scraper import MufapScraper
from parser import parse_nav_table

CSV_FILE = "data/MUFAP_Historical_NAV.csv"


class DailyNAVUpdater(MufapScraper):

    def __init__(self):

        super().__init__()

        self.amcs_processed = 0
        self.funds_processed = 0
        self.new_records = 0
        self.already_updated = 0
        self.failed_funds = 0

    # -------------------------------------------------------
    # Update One Fund
    # -------------------------------------------------------

    def update_fund(self, amc, fund):

        print()
        print("-" * 60)
        print(fund["name"])
        print("-" * 60)

        self.select_fund(fund)

        # ------------------------------------
        # Last 7 Days
        # ------------------------------------

        today = datetime.today()

        from_date = (
            today - timedelta(days=7)
        ).strftime("%d-%m-%Y")

        to_date = today.strftime("%d-%m-%Y")

        self.page.fill("#_fromdate", "")
        self.page.fill("#_fromdate", from_date)

        self.page.fill("#_Todate", "")
        self.page.fill("#_Todate", to_date)

        self.page.wait_for_timeout(1000)

        self.click_search()

        self.wait_for_table()

        html = self.get_table_html()

        df = parse_nav_table(
            html,
            amc["name"]
        )

        if df.empty:

            print("No NAV Found.")

            return

        # ------------------------------------
        # Keep Latest NAV Only
        # ------------------------------------

        df = df.tail(1).copy()

        df.insert(
            1,
            "FundID",
            fund["id"]
        )

        df.insert(
            3,
            "FundType",
            fund["fund_type"]
        )

        df.insert(
            4,
            "CategoryID",
            fund["category"]
        )

        # ------------------------------------
        # Read Existing CSV
        # ------------------------------------

        try:

            existing = pd.read_csv(
                CSV_FILE,
                low_memory=False
            )

        except FileNotFoundError:

            existing = pd.DataFrame()

        # ------------------------------------
        # Duplicate Check
        # ------------------------------------

        if not existing.empty:

            existing["Validity_Date"] = pd.to_datetime(
                existing["Validity_Date"],
                errors="coerce"
            )

            df["Validity_Date"] = pd.to_datetime(
                df["Validity_Date"],
                errors="coerce"
            )

            duplicate = (

                (existing["AMC"] == df.iloc[0]["AMC"])

                &

                (existing["Fund"] == df.iloc[0]["Fund"])

                &

                (
                    existing["Validity_Date"]
                    ==
                    df.iloc[0]["Validity_Date"]
                )

            )

            if duplicate.any():

                self.already_updated += 1

                print("Already Updated.")

                return

        # ------------------------------------
        # Save New Row
        # ------------------------------------

        df.to_csv(

            CSV_FILE,

            mode="a",

            index=False,

            header=not existing.shape[0],

            encoding="utf-8-sig"

        )

        self.new_records += len(df)

        print("Today's NAV Saved.")

    # -------------------------------------------------------
    # Run Updater
    # -------------------------------------------------------

    def run(self):

        self.start_browser()

        try:

            self.open_nav_page()

            amcs = self.get_amcs()

            for amc in amcs:

                self.amcs_processed += 1

                print()
                print("=" * 70)
                print(amc["name"])
                print("=" * 70)

                self.select_amc(amc)

                funds = self.get_funds()

                for index, fund in enumerate(
                    funds,
                    start=1
                ):

                    self.funds_processed += 1

                    print()
                    print(
                        f"Fund {index} / {len(funds)}"
                    )

                    try:

                        self.update_fund(
                            amc,
                            fund
                        )

                    except Exception as e:

                        self.failed_funds += 1

                        print(e)

            # ------------------------------------
            # Summary
            # ------------------------------------

            print()
            print("=" * 70)
            print("DAILY UPDATE COMPLETED")
            print("=" * 70)

            print(
                f"AMCs Processed    : {self.amcs_processed}"
            )

            print(
                f"Funds Processed   : {self.funds_processed}"
            )

            print(
                f"New Records Added : {self.new_records}"
            )

            print(
                f"Already Updated   : {self.already_updated}"
            )

            print(
                f"Failed Funds      : {self.failed_funds}"
            )

            print("=" * 70)

        finally:

            self.stop_browser()


if __name__ == "__main__":

    updater = DailyNAVUpdater()

    updater.run()