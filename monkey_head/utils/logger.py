"""Centralized logging utilities for Monkey Head."""

import logging
from ..logging_setup import configure_logging


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger with the given name configured via project settings."""
    configure_logging()
    return logging.getLogger(name)
