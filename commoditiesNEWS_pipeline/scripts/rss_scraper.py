from utils.classifier import classify_article
import feedparser
import uuid
from datetime import datetime, timezone
from utils.validator import validate_article
from utils.article import extract_article
from utils.date_utils import convert_to_utc
from utils.excel import save_to_excel


def run_rss_scraper(config):
    print(f"Fetching RSS from {config['Source']}")

    rss_url = config["RSS URL"]
    feed = feedparser.parse(rss_url)

    news_list = []

    for article in feed.entries:

        try:
            summary = article.get("summary", "")

            # USDA uses RSS summary because article links are unreliable
            if config["Source"] == "USDA":
                full_text = summary if summary else article.title
            else:
                full_text = extract_article(article.link)

                if not full_text:
                    full_text = summary

                if not full_text:
                    full_text = article.title

            classification = classify_article(full_text)

            news = {
                "ID": str(uuid.uuid4()),
                "Source": config["Source"],
                "Source Type": config["Source Type"],
                "URL": article.link,
                "Title": article.title,
                "Description": summary,
                "Full Text": full_text,
                "Published Time (UTC)": convert_to_utc(article.published),
                "Ingestion Time (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Country": config["Country"],
                "Region": config["Region"],
                "Language": config["Language"],
                "Asset Class": "Commodity",
                "Market": config["Market"],
                "Sector": "Energy",
                "Event Type": classification["Event Type"],
                "Importance Score": classification["Importance Score"],
                "Sentiment Score": classification["Sentiment Score"],
                "Confidence Score": classification["Confidence Score"],
                "Keywords": classification["Keywords"],
                "Named Entities": "",
                "Related Assets": classification["Related Assets"],
                "Raw Response": str(article)
            }

            
            if validate_article(news):
                news_list.append(news)
            else:
                print(f"Skipped invalid article from {news['Source']}: missing required fields")
            

        except Exception as e:
            print(f"Skipping article: {e}")



    save_to_excel(news_list, "data/commodity_news.xlsx")

    print(f"{config['Source']} -> {len(news_list)} articles processed")