from email.utils import parsedate_to_datetime
from datetime import timezone


def convert_to_utc(date_string):
    """
    Converts RSS date string to UTC ISO 8601 format.

    Example:
    Tue, 7 Jul 2026 12:00:00 EST
        ↓
    2026-07-07T17:00:00Z
    """

    try:
        dt = parsedate_to_datetime(date_string)

        dt = dt.astimezone(timezone.utc)

        return dt.strftime("%Y-%m-%d T %H:%M:%SZ")

    except Exception:
        return date_string