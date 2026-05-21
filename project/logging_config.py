import logging
import sys
from logging import Logger


def get_logger(name: str = "sentinelai") -> Logger:
    """Return a configured logger for the application.

    Uses a simple, structured formatter and logs to stdout. Call this from modules.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    fmt = (
        "%(asctime)s | %(levelname)-7s | %(name)s | %(module)s:%(lineno)d | %(message)s"
    )
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


__all__ = ["get_logger"]
