
def validate_article(news):
    """
    Validates a news article before saving.

    Returns:
        True  -> Article is valid
        False -> Article is invalid
    """

    # Required fields
    required_fields = [
        "Source",
        "URL",
        "Title",
        "Market",
        "Sector"
    ]

    for field in required_fields:
        value = news.get(field)

        if value is None:
            return False

        if isinstance(value, str) and value.strip() == "":
            return False

    # Ensure scores are valid
    importance = news.get("Importance Score", 0)

    if not (0 <= importance <= 10):
        news["Importance Score"] = 0

    sentiment = news.get("Sentiment Score", 0)

    if sentiment < -1 or sentiment > 1:
        news["Sentiment Score"] = 0

    confidence = news.get("Confidence Score", 0)

    if confidence < 0 or confidence > 1:
        news["Confidence Score"] = 0

    return True