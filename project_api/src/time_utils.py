from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def utcnow() -> datetime:
    """Get the current UTC time with timezone info."""
    return datetime.now(tz=timezone.utc)

