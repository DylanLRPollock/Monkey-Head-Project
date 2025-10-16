# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Logger module (huey/memory/PY)

"""Centralized logging utilities for Monkey Head."""

import logging
from ..logging_setup import configure_logging


def get_logger(name: str | None = None, level: str | None = None) -> logging.Logger:
    """Return a logger configured via project settings.

    Parameters
    ----------
    name:
        The logger name. Defaults to the root logger when ``None``.
    level:
        Optional logging level name (e.g. ``"DEBUG"``). When provided the
        returned logger's level will be updated accordingly.
    """

    logger = logging.getLogger(name)
    if not logger.handlers:
        configure_logging()
    if level is not None:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
