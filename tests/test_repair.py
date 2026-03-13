# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Repair module (tests)

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPAIR_MODULE = (
    Path(__file__).resolve().parents[1] / "src" / "huey" / "memory" / "PY" / "repair.py"
)

if not REPAIR_MODULE.exists():
    pytest.skip("repair module not available in this repository layout", allow_module_level=True)

spec = importlib.util.spec_from_file_location("repair", REPAIR_MODULE)
repair = importlib.util.module_from_spec(spec)
assert spec and spec.loader
MODULE_DIR = str(REPAIR_MODULE.parent)
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)
spec.loader.exec_module(repair)


class DummyCompleted:
    def __init__(self, returncode=0, stderr=b"", stdout=b""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


def test_run_repair_success(tmp_path):
    with (
        patch("uninstaller.run_uninstaller", return_value=0) as uninst,
        patch("subprocess.run") as run_mock,
        patch("tempfile.TemporaryDirectory") as tmpdir,
    ):
        tmpdir.return_value.__enter__.return_value = str(tmp_path)
        run_mock.side_effect = [DummyCompleted(), DummyCompleted()]
        rc = repair.run_repair("repo-url")
        assert rc == 0
        uninst.assert_called_once()
        run_mock.assert_any_call(
            ["git", "clone", "repo-url", str(tmp_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        run_mock.assert_any_call(
            [sys.executable, str(tmp_path / "scripts" / "installers" / "installer.py")],
            cwd=str(tmp_path),
        )


def test_run_repair_uninstall_failure():
    with patch("uninstaller.run_uninstaller", return_value=5):
        assert repair.run_repair("repo-url") == 5
