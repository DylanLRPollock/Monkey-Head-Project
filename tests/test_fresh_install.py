# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Fresh Install module (tests)

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

FRESH_INSTALL_MODULE = (
    Path(__file__).resolve().parents[1] / "src" / "huey" / "memory" / "PY" / "fresh_install.py"
)

if not FRESH_INSTALL_MODULE.exists():
    pytest.skip("fresh_install module not available in this repository layout", allow_module_level=True)

spec = importlib.util.spec_from_file_location("fresh_install", FRESH_INSTALL_MODULE)
fresh_install = importlib.util.module_from_spec(spec)
assert spec and spec.loader
MODULE_DIR = str(FRESH_INSTALL_MODULE.parent)
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)
spec.loader.exec_module(fresh_install)


def test_fresh_install_local_success():
    with (
        patch("uninstaller.run_uninstaller", return_value=0) as uninst,
        patch("installer.run_installer", return_value=0) as inst,
    ):
        rc = fresh_install.run_fresh_install("local")
        assert rc == 0
        uninst.assert_called_once()
        inst.assert_called_once()


def test_fresh_install_uninstall_fail():
    with patch("uninstaller.run_uninstaller", return_value=5):
        assert fresh_install.run_fresh_install("local") == 5


def test_fresh_install_github_calls_repair():
    with patch("repair.run_repair", return_value=0) as rep:
        rc = fresh_install.run_fresh_install("github", "repo-url")
        assert rc == 0
        rep.assert_called_once_with("repo-url")
