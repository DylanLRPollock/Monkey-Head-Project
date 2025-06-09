import logging
import logging.handlers
import os
from configparser import ConfigParser


def configure_logging(config_path=None):
    """Configure root logger using settings from CONFIG.txt."""
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "CONFIG.txt")

    parser = ConfigParser()
    if os.path.exists(config_path):
        parser.read(config_path)
        log_level = parser.get("logging", "log_level", fallback="INFO").upper()
        log_file = parser.get("logging", "log_file", fallback="monkey_head.log")
        max_bytes = parser.get("logging", "log_max_bytes", fallback="10485760")
        backup_count = parser.get(
            "logging", "log_backup_count", fallback="5"
        )
        max_bytes = int(str(max_bytes).split("#")[0].strip())
        backup_count = int(str(backup_count).split("#")[0].strip())
    else:
        log_level = "INFO"
        log_file = "monkey_head.log"
        max_bytes = 10_485_760
        backup_count = 5

    logger = logging.getLogger()
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
