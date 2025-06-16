import logging
import logging.handlers
import os
from configparser import ConfigParser

try:  # pragma: no cover - optional GUI dependency
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None


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


def configure_logging(config_path=None):
    """Configure root logger using settings from CONFIG.txt."""
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "CONFIG.txt")

    parser = ConfigParser()
    if os.path.exists(config_path):
        parser.read(config_path)
        log_level = parser.get("logging", "log_level", fallback="INFO").upper()
        log_file = parser.get(
            "logging",
            "log_file",
            fallback="memory/LOGS/monkey_head.log",
        )
        max_bytes = parser.get("logging", "log_max_bytes", fallback="10485760")
        backup_count = parser.get("logging", "log_backup_count", fallback="5")
        max_bytes = int(str(max_bytes).split("#")[0].strip())
        backup_count = int(str(backup_count).split("#")[0].strip())
    else:
        log_level = "INFO"
        log_file = "memory/LOGS/monkey_head.log"
        max_bytes = 10_485_760
        backup_count = 5

    logger = logging.getLogger()
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):  # pragma: no cover - fs access
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            log_file = os.path.basename(log_file)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
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
