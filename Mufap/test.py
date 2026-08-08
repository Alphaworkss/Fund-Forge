from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    print("Playwright Started")

    browser = p.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )

    print("CONNECTED!")

    print(browser.contexts)