"""
scraper.py

FundForge
Historical NAV Scraper
"""

import time
from datetime import datetime

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from parser import parse_nav_table
from csv_handler import save_dataframe
from logger import logger


class MufapScraper:

    def __init__(self):

        self.playwright = None
        self.browser = None
        self.page = None

        self.selected_amcs = [

            "ABL Asset Management Company Limited",

            "AL Habib Asset Management Limited",

            "Al Meezan Investment Management Limited",

            "Alfalah Asset Management Limited",

            "EFU Life Assurance Limited",

            "Faysal Asset Management Limited",

            "HBL Asset Management Limited",

            "UBL Fund Managers Limited"

        ]

    # -------------------------------------------------------
    # Browser
    # -------------------------------------------------------

    def start_browser(self):

        print("=" * 60)
        print("STEP 1 : Starting Playwright")
        print("=" * 60)

        self.playwright = sync_playwright().start()

        print("✓ Playwright Started")

        print("\nSTEP 2 : Connecting to Chrome")

        self.browser = self.playwright.chromium.connect_over_cdp(
            "http://127.0.0.1:9222"
        )

        print("✓ Browser Connected")

        print("\nSTEP 3 : Getting Contexts")

        print(self.browser.contexts)

        context = self.browser.contexts[0]

        print("✓ Context Found")

        print("\nSTEP 4 : Creating Page")

        self.page = context.new_page()

        print("✓ Page Created")

        self.page.set_default_timeout(120000)

        print("\n✓ Connected Successfully")

    def stop_browser(self):

        if self.page:
            self.page.close()

        if self.playwright:
            self.playwright.stop()

        print("Browser Closed")

    # -------------------------------------------------------
    # Open NAV Page
    # -------------------------------------------------------

    def open_nav_page(self):

        print("\nOpening NAV Page...")

        self.page.goto(

            "https://www.mufap.com.pk/Industry/IndustryStatDaily?tab=3",

            wait_until="domcontentloaded"

        )

        self.page.wait_for_timeout(5000)

        print("NAV Page Loaded")

    # -------------------------------------------------------
    # Get Selected AMCs
    # -------------------------------------------------------

    def get_amcs(self):

        soup = BeautifulSoup(

            self.page.content(),

            "html.parser"

        )

        dropdown = soup.find(

            "select",

            id="_amcDesc"

        )

        amcs = []

        for option in dropdown.find_all("option"):

            value = option.get("value", "").strip()

            name = option.text.strip()

            if value == "":
                continue

            if name not in self.selected_amcs:
                continue

            amcs.append({

                "id": value,

                "name": name

            })

        print()

        print("=" * 60)
        print("Selected AMCs")
        print("=" * 60)

        for amc in amcs:
            print(amc["name"])

        print()

        return amcs

    # -------------------------------------------------------
    # Select AMC
    # -------------------------------------------------------

    def select_amc(self, amc):

        print()

        print("=" * 60)
        print("AMC")
        print(amc["name"])
        print("=" * 60)

        self.page.select_option(

            "#_amcDesc",

            value=amc["id"]

        )

        self.page.wait_for_timeout(3000)

    # -------------------------------------------------------
    # Read Funds
    # -------------------------------------------------------

    def get_funds(self):

        soup = BeautifulSoup(

            self.page.content(),

            "html.parser"

        )

        dropdown = soup.find(

            "select",

            id="_fundDesc"

        )

        funds = []

        for option in dropdown.find_all("option"):

            value = option.get("value", "").strip()

            if value == "":
                continue

            funds.append({

                "id": value,

                "name": option.text.strip(),

                "fund_type": option.get(

                    "data-fundtype",

                    ""

                ),

                "category": option.get(

                    "data-fundcat",

                    ""

                )

            })

        print()

        print("Funds Found :", len(funds))

        return funds

    # -------------------------------------------------------
    # Select Fund
    # -------------------------------------------------------

    def select_fund(self, fund):

        print()

        print("----------------------------------------")
        print(fund["name"])
        print("----------------------------------------")

        self.page.select_option(

            "#_fundDesc",

            value=fund["id"]

        )

        self.page.wait_for_timeout(2000)


    # -------------------------------------------------------
    # Set Date Range
    # -------------------------------------------------------

    def set_date_range(self):

        print("Setting Date Range...")

        self.page.fill("#_fromdate", "")

        self.page.fill("#_fromdate", "06-08-2016")

        self.page.fill("#_Todate", "")

        today = datetime.today().strftime("%d-%m-%Y")

        self.page.fill("#_Todate", today)

        self.page.wait_for_timeout(1000)

        print(f"From : 06-08-2016")

        print(f"To   : {today}")

    # -------------------------------------------------------
    # Click Search
    # -------------------------------------------------------

    def click_search(self):

        print("Searching...")

        self.page.click("#btnSearch")

        try:

            self.page.wait_for_load_state(

                "networkidle",

                timeout=120000

            )

        except:

            pass

        self.page.wait_for_timeout(5000)

    # -------------------------------------------------------
    # Wait Until Table Loads
    # -------------------------------------------------------

    def wait_for_table(self):

        print("Waiting for historical data...")

        self.page.wait_for_selector(

            "#table_id tbody tr",

            timeout=120000

        )

        self.page.wait_for_timeout(2000)

    # -------------------------------------------------------
    # Extract Table HTML
    # -------------------------------------------------------

    def get_table_html(self):

        table = self.page.locator(

            "#table_id"

        )

        return table.evaluate(

            "element => element.outerHTML"

        )

    # -------------------------------------------------------
    # Scrape Current Fund
    # -------------------------------------------------------

    def scrape_current_fund(

        self,

        amc,

        fund

    ):

        try:

            self.select_fund(

                fund

            )

            self.set_date_range()

            self.click_search()

            self.wait_for_table()

            html = self.get_table_html()

            df = parse_nav_table(
                html,
                amc["name"]
            )

            if df.empty:

                print("No historical data found.")

                return

            # --------------------------------------------
            # Add Metadata
            # --------------------------------------------

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

            save_dataframe(

                df

            )

            print()

            print("Rows Saved :", len(df))

            print()

        except Exception as e:

            print()

            print("ERROR")

            print(fund["name"])

            print(e)

            print()

            logger.error(

                str(e)

            )

    # -------------------------------------------------------
    # Scrape Every Fund of Current AMC
    # -------------------------------------------------------

    def scrape_amc(

        self,

        amc

    ):

        self.select_amc(

            amc

        )

        funds = self.get_funds()

        total = len(

            funds

        )

        for index, fund in enumerate(

            funds,

            start=1

        ):

            print()

            print("=" * 60)

            print(

                f"Fund {index} of {total}"

            )

            print(

                fund["name"]

            )

            print("=" * 60)

            self.scrape_current_fund(

                amc,

                fund

            )

            self.page.wait_for_timeout(

                1000

            )

    # -------------------------------------------------------
    # Run Complete Scraper
    # -------------------------------------------------------

    def run(self):

        try:

            self.start_browser()

            self.open_nav_page()

            amcs = self.get_amcs()

            print()
            print("=" * 70)
            print(f"TOTAL SELECTED AMCs : {len(amcs)}")
            print("=" * 70)

            for index, amc in enumerate(amcs, start=1):

                print()
                print("#" * 70)
                print(f"AMC {index} OF {len(amcs)}")
                print(amc["name"])
                print("#" * 70)

                try:

                    self.scrape_amc(amc)

                except Exception as e:

                    print()
                    print("FAILED AMC")
                    print(amc["name"])
                    print(e)
                    print()

                    logger.error(
                        f"AMC ERROR : {amc['name']} : {e}"
                    )

                    continue

            print()
            print("=" * 70)
            print("SCRAPING COMPLETED")
            print("=" * 70)

        except Exception as e:

            print()
            print("FATAL ERROR")
            print(e)

            logger.error(str(e))

        finally:

            self.stop_browser() 