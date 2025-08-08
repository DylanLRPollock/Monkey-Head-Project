# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
"""Lightweight error handling helpers used across the project."""

from __future__ import annotations

import logging
from typing import Optional

from .logging_setup import configure_logging


class ErrorHandler:
    """Wrapper around the standard :mod:`logging` utilities.

    The handler ensures that logging is configured exactly once and optionally
    stores messages in a dedicated log file.  It exposes convenience methods
    for logging messages and exceptions while keeping the public API minimal.
    """

    def __init__(self, log_file: Optional[str] = "memory/LOGS/app.log") -> None:
        """Initialise the handler and attach a file logger if requested."""

        logger = configure_logging()
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(file_handler)

    def log_error(self, error_message: str) -> None:
        """Log ``error_message`` at ``ERROR`` level."""

        logging.error(error_message)

    def log_info(self, info_message: str) -> None:
        """Log ``info_message`` at ``INFO`` level."""

        logging.info(info_message)

    def handle_exception(self, exception: Exception, *, raise_error: bool = False) -> None:
        """Log ``exception`` with traceback and optionally re-raise it.

        Parameters
        ----------
        exception:
            The exception instance to handle.
        raise_error:
            When ``True`` the exception is re-raised after being logged.
        """

        logging.exception("Exception occurred: %s", exception)
        if raise_error:
            raise exception
