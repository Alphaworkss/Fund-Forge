import datetime
import xml.etree.ElementTree as ET
import html
import re
import pandas as pd
from textblob import TextBlob
import requests
from database import SessionLocal, init_db, NewsArticle

# ====================================================
# 1. DEFINE SOURCES
# ====================================================
# RSS Feeds of Pakistan's major financial and business portals
NEWS_SOURCES = {
    "Business Recorder": "https://www.brecorder.com/feeds/latest-news/",
    "Dawn Business": "https://www.dawn.com/feeds/business/",
    "Express Tribune Business": "https://tribune.com.pk/feed/business",
    "The News Business": "https://www.thenews.com.pk/rss/1/2",
    "Profit by Pakistan Today": "https://profit.pakistantoday.com.pk/feed/",
    "Mettis Global": "https://mettisglobal.news/feed/"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ====================================================
# 2. DATA CLEANING & NORMALISATION FUNCTIONS
# ====================================================
def clean_text(raw_html):
    """
    Cleans raw HTML tags, unescapes HTML symbols, and strips extra spaces.
    """
    if not raw_html:
        return ""
    # Strip HTML tags
    clean_r = re.compile('<.*?>')
    text = re.sub(clean_r, '', raw_html)
    # Convert HTML entities like &amp; or &quot; back to normal text
    text = html.unescape(text)
    # Remove extra whitespaces
    text = " ".join(text.split())
    return text.strip()

def normalize_date(date_str):
    """
    Standardizes typical RSS dates into a unified Python datetime.
    """
    if not date_str:
        return datetime.datetime.utcnow()
    
    # Try typical RSS date formats
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
        try:
            clean_str = date_str.strip()
            # Handle GMT timezone representation safely
            if clean_str.endswith(" GMT"):
                clean_str = clean_str[:-4] + " +0000"
            return datetime.datetime.strptime(clean_str, fmt)
        except ValueError:
            continue
    return datetime.datetime.utcnow()

# ====================================================
# 3. FEATURE EXTRACTION FUNCTIONS
# ====================================================
def detect_pakistan_entities(text):
    """
    Pakistan Entity Recognition: Identifies key financial/regulatory bodies in Pakistan.
    """
    entities = []
    text_lower = text.lower()
    
    if "state bank" in text_lower or "sbp" in text_lower or "monetary policy" in text_lower:
        entities.append("State Bank of Pakistan (SBP)")
    if "stock exchange" in text_lower or "psx" in text_lower or "kse" in text_lower:
        entities.append("Pakistan Stock Exchange (PSX)")
    if "federal board of revenue" in text_lower or "fbr" in text_lower or "tax dept" in text_lower:
        entities.append("Federal Board of Revenue (FBR)")
    if "secp" in text_lower or "securities and exchange" in text_lower:
        entities.append("SECP (Securities Regulator)")
    if "imf" in text_lower or "monetary fund" in text_lower:
        entities.append("International Monetary Fund (IMF)")
    if "nepra" in text_lower or "power regulatory" in text_lower:
        entities.append("NEPRA (Energy Regulator)")
    if "ogra" in text_lower or "oil and gas regulatory" in text_lower:
        entities.append("OGRA (Gas & Oil Regulator)")
        
    return ", ".join(entities) if entities else "None Detected"

def detect_sectors(text):
    """
    Sector Detection: Identifies the specific business sector discussed in the article.
    """
    sectors = []
    text_lower = text.lower()
    
    if any(k in text_lower for k in ["bank", "banking", "mcb", "hbl", "meezan", "ubl", "kibor"]):
        sectors.append("Banking & Finance")
    if any(k in text_lower for k in ["power", "electricity", "gas", "nepra", "ogra", "petrol", "oil", "fuel", "hubco", "ogdc", "ppl"]):
        sectors.append("Energy & Power")
    if any(k in text_lower for k in ["textile", "cotton", "yarn", "garment", "export"]):
        sectors.append("Textiles")
    if any(k in text_lower for k in ["cement", "lucky", "dg khan", "fauji"]):
        sectors.append("Construction & Cement")
    if any(k in text_lower for k in ["fertilizer", "engro", "ffc"]):
        sectors.append("Agriculture & Fertilizer")
    if any(k in text_lower for k in ["tech", "systems", "trg", "software", "information technology"]):
        sectors.append("Technology")
    if any(k in text_lower for k in ["auto", "honda", "toyota", "suzuki", "car"]):
        sectors.append("Automotive")
        
    return ", ".join(sectors) if sectors else "Macro-economy"

def classify_event(text):
    """
    Event Classification: Maps the news article to specific event topics.
    """
    text_lower = text.lower()
    
    if "budget" in text_lower or "fiscal year" in text_lower:
        return "Budget News"
    if any(k in text_lower for k in ["tax", "gst", "duty", "duties", "fbr", "taxation"]):
        return "Tax Changes"
    if any(k in text_lower for k in ["interest rate", "kibor", "sbp", "monetary policy", "policy rate"]):
        return "SBP Policy News"
    if any(k in text_lower for k in ["psx", "kse", "dividend", "earnings", "listed", "stock"]):
        return "PSX News"
    if any(k in text_lower for k in ["inflation", "cpi", "spi", "prices", "costly"]):
        return "Inflation"
    if any(k in text_lower for k in ["rupee", "pkr", "exchange rate", "dollar", "usd"]):
        return "PKR Exchange News"
    if any(k in text_lower for k in ["import", "export", "trade", "tariff"]):
        return "Import/Export News"
    if any(k in text_lower for k in ["power tariff", "electricity price", "petrol price", "gas price", "lng"]):
        return "Energy News"
    if any(k in text_lower for k in ["political", "election", "government", "minister", "parliament"]):
        return "Political News"
        
    return "General Economic News"

# ====================================================
# 4. MAIN PIPELINE EXECUTION
# ====================================================
def run_pipeline():
    print("Initializing News Pipeline Database...")
    init_db()
    db = SessionLocal()
    
    all_processed_articles = []
    articles_added = 0
    
    print("\n--- Phase 1: Data Collection & Cleaning ---")
    for source_name, feed_url in NEWS_SOURCES.items():
        try:
            print(f"Connecting to {source_name} RSS feed...")
            response = requests.get(feed_url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {source_name}. Status: {response.status_code}")
                continue
                
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                continue
                
            items = channel.findall("item")
            print(f"Scraped {len(items)} raw articles from {source_name}.")
            
            for item in items:
                raw_title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                raw_description = item.find("description").text if item.find("description") is not None else ""
                pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
                
                if not raw_title or not link:
                    continue
                    
                # ----------------- CLEANING & NORMALISATION -----------------
                title = clean_text(raw_title)
                content = clean_text(raw_description)
                published_at = normalize_date(pub_date_str)
                
                # ----------------- FEATURE EXTRACTION -----------------
                # 1. Sentiment Score (-1.0 to +1.0)
                full_text = f"{title}. {content}"
                blob = TextBlob(full_text)
                sentiment_score = round(blob.sentiment.polarity, 2)
                
                # 2. Pakistan Entity Recognition
                entities = detect_pakistan_entities(full_text)
                
                # 3. Sector Detection
                sectors = detect_sectors(full_text)
                
                # 4. Event Classification
                event_class = classify_event(full_text)
                
                # Add to excel list
                all_processed_articles.append({
                    "Title": title,
                    "Content/Description": content,
                    "URL": link,
                    "Source": source_name,
                    "Published At": published_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "Sentiment Score": sentiment_score,
                    "Pakistan Entities": entities,
                    "Sector": sectors,
                    "Event Class": event_class
                })
                
                # ----------------- DATA STORAGE (SQLite) -----------------
                # Check if article link already exists to avoid duplicates
                existing = db.query(NewsArticle).filter(NewsArticle.url == link).first()
                if not existing:
                    new_article = NewsArticle(
                        title=title,
                        content=content,
                        url=link,
                        source=source_name,
                        published_at=published_at,
                        sentiment_score=sentiment_score
                    )
                    db.add(new_article)
                    articles_added += 1
                    
            db.commit()
            
        except Exception as e:
            print(f"Error processing {source_name} feed: {e}")
            continue
            
    # ----------------- DATA STORAGE (Excel) -----------------
    if all_processed_articles:
        df_excel = pd.DataFrame(all_processed_articles)
        excel_filename = "financial_news_dataset.xlsx"
        df_excel.to_excel(excel_filename, index=False, sheet_name="Pakistan Financial News")
        print(f"\nSuccess! News pipeline dataset saved to Excel: {excel_filename}")
        print(f"Total processed articles: {len(df_excel)}")
    else:
        print("No articles collected.")
        
    print(f"Database update complete: Added {articles_added} new articles to SQLite.")
    db.close()

if __name__ == "__main__":
    run_pipeline()