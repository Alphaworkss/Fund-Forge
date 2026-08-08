from utils.sentiment import calculate_sentiment
from utils.importance import calculate_importance
import pandas as pd

# Load rules once
rules = pd.read_excel("config/event_keywords.xlsx")


def classify_article(text):

    if not text:
        return {
            "Event Type": "",
            "Keywords": "",
            "Related Assets": "",
            "Importance Score": 0,
            "Sentiment Score": 0,
            "Confidence Score": 0.0
        }

    text = text.lower()

    event_types = set()
    assets = set()
    matched_keywords = set()

    for _, row in rules.iterrows():

        keyword = str(row["Keyword"]).lower()

        if keyword in text:

            matched_keywords.add(keyword)

            if pd.notna(row["Event Type"]) and str(row["Event Type"]).strip():
                event_types.add(row["Event Type"])

            if pd.notna(row["Asset"]) and str(row["Asset"]).strip():
                assets.add(row["Asset"])

    importance = calculate_importance(text)
    sentiment_score, confidence_score = calculate_sentiment(text)

    return {
        "Event Type": ", ".join(sorted(event_types)),
        "Keywords": ", ".join(sorted(matched_keywords)),
        "Related Assets": ", ".join(sorted(assets)),
        "Importance Score": importance,
        "Sentiment Score": sentiment_score,
        "Confidence Score": confidence_score
    }