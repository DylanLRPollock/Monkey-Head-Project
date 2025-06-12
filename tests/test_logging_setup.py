import logging
from pathlib import Path

from monkey_head.logging_setup import configure_logging


def test_configure_logging_creates_log(tmp_path):
    cfg = tmp_path / "cfg.ini"
    log_file = tmp_path / "app.log"
    cfg.write_text(
        "[logging]\nlog_level = INFO\nlog_file = {}\nlog_max_bytes = 1024\nlog_backup_count = 1\n".format(
            log_file
        )
    )
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    logger = configure_logging(str(cfg))
    logger.info("entry")
    assert log_file.exists()
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert "entry" in log_file.read_text()
