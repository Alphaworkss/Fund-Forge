import os
import time
import requests

from cookie_manager import get_cookies
from logger import logger
from config import MAX_RETRIES


# Create debug folder
os.makedirs("debug", exist_ok=True)


class Downloader:

    def __init__(self):

        self.session = requests.Session()

        # Load Chrome cookies
        cookies = get_cookies()

        if cookies:
            self.session.cookies = cookies

        # Browser-like headers
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        })

    def download(self, url):

        retries = 0

        while retries < MAX_RETRIES:

            try:

                print("\n======================================")
                print("Downloading")
                print(url)
                print("======================================")

                response = self.session.get(
                    url,
                    timeout=60
                )

                response.raise_for_status()

                html = response.text

                print("Status Code:", response.status_code)
                print("HTML Length:", len(html))

                # Save HTML for debugging
                filename = (
                    url.split("/")[-1]
                    .replace("?", "_")
                    .replace("&", "_")
                    .replace("=", "_")
                )

                filepath = os.path.join(
                    "debug",
                    f"{filename}.html"
                )

                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(html)

                print(f"Saved HTML -> {filepath}")

                logger.info(f"Downloaded {url}")

                return html

            except Exception as e:

                retries += 1

                logger.error(str(e))

                print(f"Retry {retries}/{MAX_RETRIES}")

                time.sleep(5)

        print("Download failed.")

        return None
