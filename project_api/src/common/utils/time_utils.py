from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

def utcnow() -> datetime:
    """Get the current UTC time with timezone info."""
    return datetime.now(tz=timezone.utc)

def timedelta_minutes(minutes: int) -> datetime:
    """Get a datetime object representing the current UTC time plus a given number of minutes."""
    return utcnow() + timedelta(minutes=minutes) 

def timedelta_days(days: int) -> datetime:
    """Get a datetime object representing the current UTC time plus a given number of days."""
    return utcnow() + timedelta(days=days)