# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Error Handler module (tests)

import importlib.util
import logging
import sys
import types
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "huey" / "memory" / "PY"
spec = importlib.util.spec_from_file_location(
    "hueyos.error_handler",
    PACKAGE_ROOT / "error_handler.py",
    submodule_search_locations=[str(PACKAGE_ROOT)],
)
module = importlib.util.module_from_spec(spec)
sys.modules.setdefault("hueyos", types.ModuleType("hueyos"))
sys.modules["hueyos.error_handler"] = module
spec.loader.exec_module(module)  # type: ignore[union-attr]
ErrorHandler = module.ErrorHandler


def test_handle_exception_logs_and_reraises(tmp_path, caplog):
    log_path = tmp_path / "app.log"
    handler = ErrorHandler(log_file=str(log_path))

    with caplog.at_level(logging.ERROR):
        handler.handle_exception(ValueError("boom"))
    assert "Exception occurred: boom" in caplog.text
    assert log_path.exists()

    with pytest.raises(ValueError):
        handler.handle_exception(ValueError("again"), raise_error=True)
