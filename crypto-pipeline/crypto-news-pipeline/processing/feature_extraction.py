"""
Feature extraction: affected coins, event category, VADER sentiment,
and rule-based importance score. Fills the four feature fields on each
normalized record.
"""

import logging
import re
import sys
from pathlib import Path

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    COIN_KEYWORDS,
    DEFAULT_CATEGORY,
    EVENT_CATEGORY_KEYWORDS,
    IMPORTANCE_BASE,
    IMPORTANCE_HIGH_BONUS,
    IMPORTANCE_HIGH_CATEGORIES,
    IMPORTANCE_MEDIUM_BONUS,
    IMPORTANCE_MEDIUM_CATEGORIES,
    IMPORTANCE_OFFICIAL_BONUS,
    IMPORTANCE_SENTIMENT_BONUS,
    IMPORTANCE_SENTIMENT_THRESHOLD,
)

logger = logging.getLogger(__name__)

_analyzer = SentimentIntensityAnalyzer()

# Precompile word-boundary patterns for coin names and tickers.
_COIN_PATTERNS: list[tuple[str, re.Pattern]] = []
for _name, _ticker in COIN_KEYWORDS.items():
    _COIN_PATTERNS.append(
        (_ticker, re.compile(rf"\b{re.escape(_name)}\b", re.IGNORECASE))
    )
    _COIN_PATTERNS.append(
        (_ticker, re.compile(rf"\b{re.escape(_ticker)}\b"))  # tickers: case-sensitive
    )


def detect_affected_coins(text: str) -> str:
    """
    Match coin names (case-insensitive) and tickers (exact case) against the
    text. Returns a comma-separated, de-duplicated ticker string, e.g.
    "BTC,ETH". Preserves first-mention order.
    """
    if not text:
        return ""
    found: list[str] = []
    for ticker, pattern in _COIN_PATTERNS:
        if ticker not in found and pattern.search(text):
            found.append(ticker)
    return ",".join(found)


def classify_event_category(text: str) -> str:
    """
    Keyword-rule classification. Categories are evaluated in the order
    defined in config.EVENT_CATEGORY_KEYWORDS; first match wins.
    """
    if not text:
        return DEFAULT_CATEGORY
    lowered = text.lower()
    for category, keywords in EVENT_CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword.lower() in lowered:
                return category
    return DEFAULT_CATEGORY


def score_sentiment(text: str) -> float:
    """VADER compound sentiment score in [-1.0, 1.0]."""
    if not text:
        return 0.0
    return float(_analyzer.polarity_scores(text)["compound"])


def compute_importance(event_category: str, source_type: str, sentiment_score: float) -> float:
    """
    Rule-based importance score:
      - Base 0.3
      - +0.3 for high-impact categories (hack/exploit/outage/regulatory)
      - +0.2 for medium-impact categories (listing/delisting/ETF/fork)
      - +0.1 if the source is an official exchange announcement
      - +0.1 if |sentiment| > 0.5
      - Clamped to [0.0, 1.0]
    """
    score = IMPORTANCE_BASE
    if event_category in IMPORTANCE_HIGH_CATEGORIES:
        score += IMPORTANCE_HIGH_BONUS
    elif event_category in IMPORTANCE_MEDIUM_CATEGORIES:
        score += IMPORTANCE_MEDIUM_BONUS
    if source_type == "exchange_announcement":
        score += IMPORTANCE_OFFICIAL_BONUS
    if abs(sentiment_score) > IMPORTANCE_SENTIMENT_THRESHOLD:
        score += IMPORTANCE_SENTIMENT_BONUS
    return round(max(0.0, min(1.0, score)), 4)


def extract_features(record: dict) -> dict:
    """Fill the four feature fields on one normalized record (in place copy)."""
    text = f"{record['title']} {record['content']}".strip()

    enriched = dict(record)
    enriched["affected_coins"] = detect_affected_coins(text)
    enriched["event_category"] = classify_event_category(text)
    enriched["sentiment_score"] = score_sentiment(text)
    enriched["importance_score"] = compute_importance(
        enriched["event_category"],
        enriched["source_type"],
        enriched["sentiment_score"],
    )
    return enriched


def extract_features_batch(records: list[dict]) -> list[dict]:
    """Extract features for a batch. A single bad record is logged and skipped."""
    enriched: list[dict] = []
    for record in records:
        try:
            enriched.append(extract_features(record))
        except Exception as exc:
            logger.error(
                "Feature extraction failed for %s: %s",
                record.get("url", "<no url>"), exc,
            )
    logger.info("Feature extraction: %d in, %d out", len(records), len(enriched))
    return enriched
