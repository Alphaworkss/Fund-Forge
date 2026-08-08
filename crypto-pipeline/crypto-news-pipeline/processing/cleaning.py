"""
Cleaning: strip HTML, remove boilerplate, normalize whitespace and
timestamps, drop invalid records, and de-duplicate (exact URL match plus
fuzzy title-similarity across sources).
"""

import logging
import re
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BOILERPLATE_PHRASES, TITLE_SIMILARITY_THRESHOLD  # noqa: E402

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove all HTML tags/entities, returning plain text."""
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ")


def remove_boilerplate(text: str) -> str:
    """Remove known boilerplate/ad phrases (case-insensitive)."""
    if not text:
        return ""
    for phrase in BOILERPLATE_PHRASES:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse all runs of whitespace into single spaces and trim."""
    if not text:
        return ""
    return _WHITESPACE_RE.sub(" ", text).strip()


def clean_text(text: str) -> str:
    """Full text-cleaning pass: HTML -> boilerplate -> whitespace."""
    return normalize_whitespace(remove_boilerplate(strip_html(text)))


def to_utc_iso(timestamp: str) -> Optional[str]:
    """
    Convert a timestamp string (RFC 2822 from RSS, ISO 8601, or a few
    common date formats) to UTC ISO 8601. Returns None if unparseable.
    """
    if not timestamp:
        return None
    timestamp = timestamp.strip()

    dt: Optional[datetime] = None

    # RFC 2822 (typical RSS): "Mon, 06 Jan 2025 14:30:00 GMT"
    try:
        dt = parsedate_to_datetime(timestamp)
    except (TypeError, ValueError):
        dt = None

    # ISO 8601 (handle trailing Z)
    if dt is None:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            dt = None

    # Common bare date formats
    if dt is None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%b %d, %Y", "%d %b %Y", "%B %d, %Y"):
            try:
                dt = datetime.strptime(timestamp, fmt)
                break
            except ValueError:
                continue

    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def titles_similar(a: str, b: str, threshold: float = TITLE_SIMILARITY_THRESHOLD) -> bool:
    """Fuzzy title comparison for near-duplicate detection."""
    if not a or not b:
        return False
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio() >= threshold


def deduplicate(records: list[dict]) -> list[dict]:
    """
    Remove duplicates:
      1. Exact URL match.
      2. Fuzzy title similarity across sources (keeps the first occurrence).
    """
    result: list[dict] = []
    seen_urls: set[str] = set()
    kept_titles: list[str] = []

    for record in records:
        url = record.get("url", "")
        title = record.get("title", "")

        if url in seen_urls:
            continue

        if any(titles_similar(title, kept) for kept in kept_titles):
            continue

        seen_urls.add(url)
        kept_titles.append(title)
        result.append(record)

    return result


def clean_record(record: dict) -> Optional[dict]:
    """
    Clean a single raw record. Returns the cleaned record, or None if the
    record is invalid (missing title or unparseable timestamp).
    """
    title = clean_text(record.get("title", ""))
    if not title:
        return None

    published_at = to_utc_iso(record.get("published_at", ""))
    if published_at is None:
        return None

    cleaned = dict(record)
    cleaned["title"] = title
    cleaned["published_at"] = published_at
    cleaned["raw_content"] = clean_text(record.get("raw_content", ""))
    return cleaned


def clean_records(records: list[dict]) -> list[dict]:
    """Clean a batch: per-record cleaning + validation, then de-duplication."""
    cleaned: list[dict] = []
    dropped = 0
    for record in records:
        result = clean_record(record)
        if result is None:
            dropped += 1
            continue
        cleaned.append(result)

    deduped = deduplicate(cleaned)
    logger.info(
        "Cleaning: %d in, %d dropped (invalid), %d removed (duplicates), %d out",
        len(records), dropped, len(cleaned) - len(deduped), len(deduped),
    )
    return deduped
