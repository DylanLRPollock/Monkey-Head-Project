# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Logging Setup module (tests)

import logging

import pytest

from hueyos.logging_setup import configure_logging


def test_configure_logging_creates_log(tmp_path):
    cfg = tmp_path / "cfg.ini"
    log_file = tmp_path / "app.log"
    cfg.write_text(
        (
            "[logging]\nlog_level = INFO\nlog_file = {}\nlog_max_bytes = 1024\n"
            "log_backup_count = 1\n"
        ).format(log_file)
    )
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    logger = configure_logging(str(cfg))
    logger.info("entry")
    assert log_file.exists()
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert "entry" in log_file.read_text()


class DummyTk:
    def withdraw(self):
        pass

    def destroy(self):
        pass


class DummyTkModule:
    def __init__(self):
        self.created = False

    def Tk(self):
        self.created = True
        return DummyTk()


def test_critical_error_triggers_gui(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.ini"
    log_file = tmp_path / "app.log"
    cfg.write_text(
        (
            "[logging]\nlog_level = INFO\nlog_file = {}\nlog_max_bytes = 1024\n"
            "log_backup_count = 1\n"
        ).format(log_file)
    )
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    dummy_tk = DummyTkModule()
    monkeypatch.setattr("hueyos.logging_setup.tk", dummy_tk)
    calls = []
    monkeypatch.setattr(
        "hueyos.logging_setup.messagebox.showerror",
        lambda title, message: calls.append((title, message)),
    )

    logger = configure_logging(str(cfg))
    logger.critical("boom")
    assert dummy_tk.created
    assert calls and "boom" in calls[0][1]


def test_env_var_overrides_path(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.ini"
    log_file = tmp_path / "app.log"
    cfg.write_text(
        (
            "[logging]\nlog_level = INFO\nlog_file = {}\nlog_max_bytes = 1024\n"
            "log_backup_count = 1\n"
        ).format(log_file)
    )
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    monkeypatch.setenv("MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.setenv("MONKEY_HEAD_CONFIG", str(cfg))
    logger = configure_logging()
    logger.info("check")
    assert log_file.exists()


def test_default_config_uses_memory(monkeypatch, tmp_path):
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    monkeypatch.setenv("MEMORY_PATH", str(tmp_path / "memory"))
    monkeypatch.delenv("MONKEY_HEAD_CONFIG", raising=False)
    logger = configure_logging()
    logger.info("hello")
    log_file = tmp_path / "memory" / "LOGS" / "hueyos.log"
    assert log_file.exists()


def test_missing_config_raises(tmp_path):
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    missing = tmp_path / "missing.ini"
    with pytest.raises(FileNotFoundError):
        configure_logging(str(missing))
