import logging
import sys

from app.utils.config import get_settings


def _build_logger(name: str = "tender_agent") -> logging.Logger:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)

    log = logging.getLogger(name)
    log.setLevel(level)
    if not log.handlers:
        log.addHandler(handler)
    log.propagate = False
    return log


logger = _build_logger()
