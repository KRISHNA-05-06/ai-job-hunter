"""
Shared date parsing utilities for all scrapers.
Converts relative text ("2 days ago") or ISO strings to a standard datetime string.
"""
from datetime import datetime, timedelta


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def relative_to_iso(text: str) -> str:
    """
    Convert relative date text to ISO datetime string.
    Handles: 'just posted', 'today', '2 hours ago', '1 day ago',
             '3 days ago', '1 week ago', 'posted 30+ days ago'
    """
    if not text:
        return now_iso()

    text = text.lower().strip()
    now  = datetime.now()

    if any(w in text for w in ["just", "today", "now", "active", "new"]):
        return now_iso()
    elif "hour" in text:
        try:
            n = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(hours=n)).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            return now_iso()
    elif "day" in text:
        try:
            n = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(days=n)).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            return (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    elif "week" in text:
        try:
            n = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(weeks=n)).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            return (now - timedelta(weeks=1)).strftime("%Y-%m-%dT%H:%M:%S")
    elif "month" in text:
        try:
            n = int(''.join(filter(str.isdigit, text)) or 1)
            return (now - timedelta(days=n * 30)).strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            return (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
    else:
        return now_iso()


def scrape_time_text(text: str) -> str:
    """Auto-detect whether text is relative ('2 days ago') or already ISO, and return ISO."""
    if not text:
        return now_iso()
    # Already an ISO datetime
    if "T" in text or (len(text) == 10 and text[4] == "-"):
        return text
    return relative_to_iso(text)
