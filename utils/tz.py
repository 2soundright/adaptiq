"""
utils/tz.py
-----------
Timezone utilities. All app timestamps use GMT+5.
"""

from datetime import datetime, timedelta, timezone

GMT5 = timezone(timedelta(hours=5))


def now_gmt5() -> datetime:
    """Return current datetime in GMT+5."""
    return datetime.now(GMT5)


def now_gmt5_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Return current GMT+5 datetime as a formatted string."""
    return now_gmt5().strftime(fmt)


def utc_str_to_gmt5(utc_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Convert a UTC datetime string (from SQLite CURRENT_TIMESTAMP)
    to a GMT+5 formatted string.
    """
    try:
        dt_utc = datetime.strptime(utc_str, fmt).replace(tzinfo=timezone.utc)
        dt_gmt5 = dt_utc.astimezone(GMT5)
        return dt_gmt5.strftime(fmt)
    except Exception:
        return utc_str


def since_gmt5(days: int = 0, hours: int = 0) -> str:
    """
    Return a datetime string (UTC-equivalent for SQLite comparison)
    representing N days/hours ago from now in GMT+5.
    SQLite stores UTC, so we subtract the offset to keep comparisons correct.
    """
    ref = datetime.now(timezone.utc) - timedelta(days=days, hours=hours)
    return ref.strftime("%Y-%m-%d %H:%M:%S")
