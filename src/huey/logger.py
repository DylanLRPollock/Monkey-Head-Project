"""Logging helpers for the new HueyOS scaffold."""

from __future__ import annotations

import logging

from .settings import RuntimeSettings

_CONFIGURED = False


def configure_logging(
    settings: RuntimeSettings | None = None, *, level: str | None = None
) -> logging.Logger:
    """Configure process-wide logging in an idempotent way."""

    global _CONFIGURED

    settings = settings or RuntimeSettings.from_env()
    resolved_level = (level or settings.log_level).upper()
    numeric_level = getattr(logging, resolved_level, logging.INFO)
    if not _CONFIGURED:
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
        _CONFIGURED = True
    else:
        logging.getLogger().setLevel(numeric_level)
    return logging.getLogger("huey")


def get_logger(name: str, settings: RuntimeSettings | None = None) -> logging.Logger:
    configure_logging(settings=settings)
    return logging.getLogger(name)


__all__ = ["configure_logging", "get_logger"]
