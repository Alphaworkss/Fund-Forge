from pathlib import Path
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


OPEC_URL = "https://www.opec.org/press-releases-2023.html"

chrome_options = Options()

# Browser background mein chalega.
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = None

try:
    print("Opening OPEC website...")

    driver = webdriver.Chrome(
        options=chrome_options
    )

    driver.get(OPEC_URL)

    sleep(5)

    print("Page title:", driver.title)
    print("Current URL:", driver.current_url)
    print("Page length:", len(driver.page_source))

    Path("data/raw/opec").mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(
        "data/raw/opec/opec_test_2023.html"
    ).write_text(
        driver.page_source,
        encoding="utf-8",
    )

    print("OPEC page saved successfully.")

finally:
    if driver is not None:
        driver.quit()