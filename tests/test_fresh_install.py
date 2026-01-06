# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Fresh Install module (tests)

from unittest.mock import patch

from scripts.installers import fresh_install


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
