import pandas as pd

rules = pd.read_excel("config/sentiment_keywords.xlsx")


def calculate_sentiment(text):
    """
    Returns:
        sentiment_score (int)
        confidence_score (float)
    """

    if not text:
        return 0, 0.0

    text = text.lower()

    score = 0
    matches = 0

    for _, row in rules.iterrows():

        keyword = str(row["Keyword"]).lower()

        if keyword in text:
            score += int(row["Score"])
            matches += 1

    confidence = min(matches / 10, 1.0)

    return score, round(confidence, 2)