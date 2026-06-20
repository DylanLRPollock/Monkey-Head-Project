"""Logging helpers for the Monkey Head compatibility layer."""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional GUI dependency
    import tkinter as tk
    from tkinter import messagebox
except ImportError:  # pragma: no cover - can't import GUI libs
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]

from huey.os.config_manager import ConfigManager

__all__ = ["CriticalErrorHandler", "configure_logging"]

from huey.utils.paths import get_logs_dir, get_memory_path

logger = logging.getLogger(__name__)


class CriticalErrorHandler(logging.Handler):
    """Display a GUI dialog for critical log records."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - GUI
        if messagebox is None or tk is None:
            return
        if record.levelno >= logging.CRITICAL:
            root = None
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Critical Error", self.format(record))
            except (RuntimeError, AttributeError, TypeError) as e:
                logger.error(f"Failed to show error dialog: {e}")
            finally:
                if root is not None:
                    try:
                        root.destroy()
                    except (RuntimeError, AttributeError, TypeError) as e:
                        logger.debug(f"Error destroying root window: {e}")


def _resolve_log_path(log_file: str) -> Path:
    raw_path = Path(str(log_file).strip())
    if raw_path.is_absolute():
        return raw_path

    parts = raw_path.parts
    if parts and parts[0] == "memory":
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / raw_path).resolve()

    base_memory = get_memory_path(create=True)
    return (base_memory / raw_path).resolve()


def _parse_int(value: object, default: int) -> int:
    try:
        text = str(value).split("#")[0].strip()
        return int(text)
    except (TypeError, ValueError):
        return default


def _load_logging_settings(config_path: Optional[str]) -> dict[str, object]:
    defaults = {
        "log_level": "INFO",
        "log_file": "LOGS/huey.os.log",
        "log_max_bytes": 10_485_760,
        "log_backup_count": 5,
    }
    resolved_path = config_path or os.environ.get("MONKEY_HEAD_CONFIG")
    manager = ConfigManager(resolved_path)
    cfg_path = manager.path

    if resolved_path:
        if not cfg_path.exists():
            raise FileNotFoundError(f"Logging configuration file not found: {cfg_path}")
        return manager.get_section("logging", defaults)

    if not cfg_path.exists():
        return defaults

    return manager.get_section(
        "logging",
        defaults,
    )


def configure_logging(config_path: Optional[str] = None) -> logging.Logger:
    """Configure the root logger using settings from the configuration file."""

    logging_cfg = _load_logging_settings(config_path)
    default_logs_dir = get_logs_dir()

    log_level = str(logging_cfg.get("log_level", "INFO")).upper()
    log_file_value = logging_cfg.get("log_file", "LOGS/huey.os.log")
    max_bytes = _parse_int(logging_cfg.get("log_max_bytes", 10_485_760), 10_485_760)
    backup_count = _parse_int(logging_cfg.get("log_backup_count", 5), 5)

    logger_obj = logging.getLogger()
    if logger_obj.handlers:
        return logger_obj

    logger_obj.setLevel(getattr(logging, log_level, logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = _resolve_log_path(str(log_file_value))
    log_dir = log_path.parent
    if log_dir and not log_dir.exists():  # pragma: no cover - fs access
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to create log directory: {e}")
            log_path = Path(log_path.name)
    elif log_dir and log_dir == default_logs_dir.resolve():
        try:
            default_logs_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to create default logs directory: {e}")

    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    gui_handler = CriticalErrorHandler()
    gui_handler.setLevel(logging.CRITICAL)
    gui_handler.setFormatter(formatter)

    logger_obj.addHandler(file_handler)
    logger_obj.addHandler(stream_handler)
    logger_obj.addHandler(gui_handler)
    return logger_obj
