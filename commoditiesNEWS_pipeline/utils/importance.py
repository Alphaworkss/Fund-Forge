import pandas as pd

# Load the importance rules once
rules = pd.read_excel("config/importance_rules.xlsx")


def calculate_importance(text):
    """
    Calculate the importance score based on keyword matches.
    Returns the highest matching score.
    """

    if not text:
        return 0

    text = text.lower()

    highest_score = 0

    for _, row in rules.iterrows():

        keyword = str(row["Keyword"]).lower()

        if keyword in text:

            score = int(row["Score"])

            if score > highest_score:
                highest_score = score

    return highest_score