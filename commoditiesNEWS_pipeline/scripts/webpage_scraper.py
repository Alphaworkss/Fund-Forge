import requests
import uuid
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.validator import validate_article
from utils.article import extract_article
from utils.classifier import classify_article
from utils.date_utils import convert_to_utc
from utils.excel import save_to_excel


def run_webpage_scraper(config):

    print(f"Fetching webpage from {config['Source']}")
    MAX_ARTICLES = 10
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        config["Website"],
        headers=headers,
        timeout=20
    )

    if response.status_code != 200:
        print("Failed to open webpage")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    news_list = []
    market = config["Market"]
    if config["Source"] == "IEA":
      links = soup.find_all("article")
    else:
      links = soup.find_all("a", href=True)

    for link in links:

        if config["Source"] == "IEA":

           title = link.get_text(" ", strip=True)

           a = link.find("a", href=True)

           if not a:
             continue

           href = a["href"]

        else:

           title = link.get_text(strip=True)
           href = link["href"]
        if len(title) < 20:
            continue

        # Convert relative URLs to absolute URLs
        href = urljoin(config["Website"], href)

        full_text = extract_article(href)

        if not full_text:
            full_text = title

        classification = classify_article(full_text)
        

        if market == "Agriculture":
         sector = "Agriculture"

        elif market == "Oil & Gas":
         sector = "Energy"

        elif market == "Metals":
         sector = "Metals"

        else:
         sector = ""

        news = {
            "ID": str(uuid.uuid4()),
            "Source": config["Source"],
            "Source Type": "WEB",
            "URL": href,
            "Title": title,
            "Description": "",
            "Full Text": full_text,
            "Published Time (UTC)": "",
            "Ingestion Time (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Country": config["Country"],
            "Region": config["Region"],
            "Language": config["Language"],
            "Asset Class": "Commodity",
            "Market": config["Market"],
            "Sector": sector,
            "Event Type": classification["Event Type"],
            "Importance Score": classification["Importance Score"],
            "Sentiment Score": classification["Sentiment Score"],
            "Confidence Score": classification["Confidence Score"],
            "Keywords": classification["Keywords"],
            "Named Entities": "",
            "Related Assets": classification["Related Assets"],
            "Raw Response": ""
        }

        if validate_article(news):
           news_list.append(news)
        else:
           print(f"Skipped invalid article from {news['Source']}: missing required fields")

        # Limit to the first 10 articles while testing
        if len(news_list) >= MAX_ARTICLES:
            break

    save_to_excel(news_list, "data/commodity_news.xlsx")

    print(f"{config['Source']} -> {len(news_list)} articles processed")