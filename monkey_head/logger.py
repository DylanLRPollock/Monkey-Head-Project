import logging
import os


def get_logger(name: str = __name__, log_file: str = "logs/app.log", level=logging.INFO) -> logging.Logger:
    """Return a configured logger that writes to ``log_file``.

    If the logger already has handlers configured, they will be reused.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
