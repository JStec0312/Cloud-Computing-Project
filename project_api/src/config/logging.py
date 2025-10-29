import logging
import sys
from enum import StrEnum

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s %(levelname)s [%(name)s] %(pathname)s:%(lineno)d - %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

class LogLevel(StrEnum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

_LEVEL_MAP = {
    LogLevel.CRITICAL: logging.CRITICAL,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.INFO: logging.INFO,
    LogLevel.DEBUG: logging.DEBUG,
}

def configure_logging(level: str | LogLevel = LogLevel.ERROR, *, debug_paths: bool = False) -> None:
    """
    Konfiguruje root logger raz (idempotentnie). Użyj na starcie aplikacji.
    """
    if isinstance(level, str):
        level = level.upper()
        try:
            level = LogLevel[level] if level in LogLevel.__members__ else LogLevel(level)
        except Exception:
            level = LogLevel.ERROR

    if logging.getLogger().handlers:
        logging.getLogger().setLevel(_LEVEL_MAP[level])
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(
        LOG_FORMAT_DEBUG if level == LogLevel.DEBUG and debug_paths else LOG_FORMAT,
        datefmt=DATEFMT
    ))

    root = logging.getLogger()
    root.setLevel(_LEVEL_MAP[level])
    root.addHandler(handler)

    # Przycisz hałaśliwe loggery (dostosuj wg potrzeb)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
