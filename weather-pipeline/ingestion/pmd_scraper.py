import feedparser
import pandas as pd

PMD_CAP_FEED_URL = "https://cap-sources.s3.amazonaws.com/pk-pmd-en/rss.xml"


def get_pmd_alerts(feed_url: str = PMD_CAP_FEED_URL) -> list[dict]:
    """Fetch and parse the live PMD CAP alert feed."""
    import calendar

    feed = feedparser.parse(feed_url)
    print(f"    PMD feed returned {len(feed.entries)} entries")

    alerts = []
    for entry in feed.entries:
        # feedparser gives a pre-parsed struct_time in published_parsed which
        # is far more reliable than the raw 'published' string (different
        # CAP feeds use different date formats that pandas can't always
        # guess correctly, which was silently dropping every PMD row).
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed:
            published_iso = pd.Timestamp(
                calendar.timegm(parsed), unit="s", tz="UTC"
            ).isoformat()
        else:
            # No usable date on the entry at all - fall back to "now" rather
            # than silently losing the alert.
            published_iso = pd.Timestamp.now(tz="UTC").isoformat()

        alerts.append({
            "title": entry.get("title", "").strip() or "(no title)",
            "description": entry.get("description", "").strip(),
            "published": published_iso,
            "author": entry.get("author", ""),
            "category": entry.get("category", ""),
            "link": entry.get("link", ""),
        })
    return alerts


def alerts_to_dataframe(alerts: list[dict]) -> pd.DataFrame:
    """
    Shape PMD alerts into our unified schema. These are free-text regional
    advisories (e.g. "Urban flooding is likely in Sindh"), not per-location
    numeric readings, so 'location' holds the region/province mentioned in
    the title and 'value' holds the alert text.
    """
    rows = []
    for a in alerts:
        rows.append({
            "source": "PMD",
            "location": a["title"],          # e.g. "Widespread rain in SE Sindh"
            "timestamp": a["published"],
            "metric_type": "alert",
            "value": a["description"],       # full advisory text, e.g. districts affected
            "unit": None,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    alerts = get_pmd_alerts()
    print(f"Fetched {len(alerts)} PMD alerts")
    df = alerts_to_dataframe(alerts)
    print(df[["location", "timestamp"]].head(10))
