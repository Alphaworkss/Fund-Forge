import requests
import trafilatura
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def extract_article(url):
    """
    Downloads an article and extracts the main text.

    Returns:
        full_text (str)
    """

    for attempt in range(3):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            if response.status_code != 200:
                print(f"HTTP {response.status_code}: {url}")
                return ""

            downloaded = trafilatura.extract(response.text)

            if downloaded:
                return downloaded.strip()

            return ""

        except Exception as e:

            print(f"Warning: Could not download {url}")

            time.sleep(2)

    return ""