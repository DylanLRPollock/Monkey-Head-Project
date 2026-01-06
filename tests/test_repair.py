# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Repair module (tests)

import subprocess
import sys
from unittest.mock import patch

from scripts.installers import repair


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
            ["git", "clone", "--depth", "1", "repo-url", str(tmp_path)],
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        run_mock.assert_any_call(
            [sys.executable, str(tmp_path / "scripts" / "installers" / "installer.py")],
            cwd=str(tmp_path),
            stdout=None,
            stderr=None,
            text=True,
            check=False,
        )


def test_run_repair_uninstall_failure():
    with patch("uninstaller.run_uninstaller", return_value=5):
        assert repair.run_repair("repo-url") == 5
