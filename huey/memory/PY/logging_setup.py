"""Logging helpers for the legacy Huey memory package."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional GUI dependency
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None

from monkey_head.config_manager import ConfigManager


class CriticalErrorHandler(logging.Handler):
    """Display a GUI dialog for critical log records."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - GUI
        if messagebox is None or tk is None:
            return
        if record.levelno >= logging.CRITICAL:
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Critical Error", self.format(record))
            except Exception:
                pass
            finally:
                try:
                    root.destroy()
                except Exception:
                    pass


def _resolve_log_path(log_file: str) -> Path:
    raw_path = Path(str(log_file).strip())
    if raw_path.is_absolute():
        return raw_path
    return Path.cwd() / raw_path


def _parse_int(value: object, default: int) -> int:
    try:
        text = str(value).split("#")[0].strip()
        return int(text)
    except (TypeError, ValueError):
        return default


def _load_logging_settings(config_path: Optional[str]) -> dict[str, object]:
    manager = ConfigManager(config_path)
    cfg_path = manager.path
    if not cfg_path.exists():
        raise FileNotFoundError(f"Logging configuration file not found: {cfg_path}")

    return manager.get_section(
        "logging",
        {
            "log_level": "INFO",
            "log_file": "memory/LOGS/monkey_head.log",
            "log_max_bytes": 10_485_760,
            "log_backup_count": 5,
        },
    )


def configure_logging(config_path: Optional[str] = None) -> logging.Logger:
    """Configure root logger using settings from main.config."""

    logging_cfg = _load_logging_settings(config_path)

    log_level = str(logging_cfg.get("log_level", "INFO")).upper()
    log_file_value = logging_cfg.get("log_file", "memory/LOGS/monkey_head.log")
    max_bytes = _parse_int(logging_cfg.get("log_max_bytes", 10_485_760), 10_485_760)
    backup_count = _parse_int(logging_cfg.get("log_backup_count", 5), 5)

    logger = logging.getLogger()
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = _resolve_log_path(str(log_file_value))
    log_dir = log_path.parent
    if log_dir and not log_dir.exists():  # pragma: no cover - fs access
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            log_path = Path(log_path.name)

    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    gui_handler = CriticalErrorHandler()
    gui_handler.setLevel(logging.CRITICAL)
    gui_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(gui_handler)
    return logger


__all__ = ["CriticalErrorHandler", "configure_logging"]
