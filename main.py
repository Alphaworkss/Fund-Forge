from scraper import MufapScraper
from parser import (
    parse_performance,
    parse_nav,
    parse_aum
)

from excel_handler import save_dataframe

from config import (
    PERFORMANCE_URL,
    NAV_URL,
    AUM_URL
)


def main():

    print("=" * 60)
    print("              FUND FORGE SCRAPER")
    print("=" * 60)

    scraper = MufapScraper()

    scraper.start_browser()

    try:

        # ==========================================
        # PERFORMANCE SUMMARY
        # ==========================================

        print("\nScraping Performance Summary...")

        html = scraper.get_page_html(PERFORMANCE_URL)

        if html:

            df = parse_performance(html)

            save_dataframe(
                df,
                "Performance Summary"
            )

        else:

            print("Failed to scrape Performance Summary")

        # ==========================================
        # DAILY NAV
        # ==========================================

        print("\nScraping Daily NAV...")

        html = scraper.get_page_html(NAV_URL)

        if html:

            df = parse_nav(html)

            save_dataframe(
                df,
                "Daily NAV"
            )

        else:

            print("Failed to scrape Daily NAV")

        # ==========================================
        # AUM
        # ==========================================

        print("\nScraping Assets Under Management...")

        html = scraper.get_page_html(AUM_URL)

        if html:

            df = parse_aum(html)

            save_dataframe(
                df,
                "Assets Under Management"
            )

        else:

            print("Failed to scrape AUM")

    except Exception as e:

        print("ERROR:", e)

    finally:

        scraper.stop_browser()

        print("\nScraping Completed Successfully")


if __name__ == "__main__":

    main()