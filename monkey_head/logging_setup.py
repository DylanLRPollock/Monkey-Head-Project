"""Logging helpers for the Monkey Head compatibility layer."""

from __future__ import annotations

import logging
import logging.handlers
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional GUI dependency
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]

__all__ = ["CriticalErrorHandler", "configure_logging"]


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


def _resolve_config_path(config_path: Optional[str]) -> Path:
    if config_path is not None:
        return Path(config_path)

    env_path = os.environ.get("MONKEY_HEAD_CONFIG")
    if env_path:
        return Path(env_path)

    base_dir = Path(__file__).resolve().parents[1]
    return base_dir / "config" / "CONFIG.txt"


def configure_logging(config_path: Optional[str] = None) -> logging.Logger:
    """Configure the root logger using settings from the configuration file."""

    cfg_path = _resolve_config_path(config_path)
    parser = ConfigParser()
    if cfg_path.exists():
        parser.read(cfg_path)
        log_level = parser.get("logging", "log_level", fallback="INFO").upper()
        log_file = parser.get(
            "logging",
            "log_file",
            fallback="memory/LOGS/monkey_head.log",
        )
        max_bytes_raw = parser.get("logging", "log_max_bytes", fallback="10485760")
        backup_count_raw = parser.get("logging", "log_backup_count", fallback="5")
        try:
            max_bytes = int(str(max_bytes_raw).split("#")[0].strip())
        except (TypeError, ValueError):
            max_bytes = 10_485_760
        try:
            backup_count = int(str(backup_count_raw).split("#")[0].strip())
        except (TypeError, ValueError):
            backup_count = 5
    else:
        log_level = "INFO"
        log_file = "memory/LOGS/monkey_head.log"
        max_bytes = 10_485_760
        backup_count = 5

    logger = logging.getLogger()
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level, logging.INFO))
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    log_path = Path(log_file)
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
