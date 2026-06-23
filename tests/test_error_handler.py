# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Error Handler module (tests)

import logging

import pytest

from huey.os.error_handler import ErrorHandler


def test_handle_exception_logs_and_reraises(tmp_path, caplog):
    log_path = tmp_path / "app.log"
    handler = ErrorHandler(log_file=str(log_path))

    with caplog.at_level(logging.ERROR):
        handler.handle_exception(ValueError("boom"))
    assert "Exception occurred: boom" in caplog.text
    assert log_path.exists()

    with pytest.raises(ValueError):
        handler.handle_exception(ValueError("again"), raise_error=True)
