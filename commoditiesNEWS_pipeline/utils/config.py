import pandas as pd


def load_sources():
    """
    Loads all enabled news sources from the configuration file.
    """

    df = pd.read_excel("config/news_sources.xlsx")

    df = df[df["Enabled"] == True]

    return df.to_dict(orient="records")