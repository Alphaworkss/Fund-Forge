from playwright.sync_api import sync_playwright
from logger import logger


class MufapScraper:

    def __init__(self):

        self.playwright = None
        self.browser = None
        self.page = None

    def start_browser(self):

        print("Connecting to existing Chrome...")

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            "http://localhost:9222"
        )

        context = self.browser.contexts[0]

        self.page = context.new_page()

        self.page.set_default_timeout(120000)

        print("Connected Successfully")

    def stop_browser(self):

        if self.page:
            self.page.close()

        if self.playwright:
            self.playwright.stop()

        print("Disconnected")

    def get_page_html(self, url):

        print(f"\nOpening\n{url}")

        self.page.goto(
            url,
            wait_until="domcontentloaded"
        )

        self.page.wait_for_timeout(8000)

        html = self.page.content()

        print("HTML Length:", len(html))

        return html