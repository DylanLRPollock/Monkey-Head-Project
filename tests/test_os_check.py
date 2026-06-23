# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Os Check module (tests)

from unittest.mock import patch

import pytest

pytest.importorskip("distro")

from huey.os.core.system_checks import check_os_support


def test_windows_warning():
    with (
        patch("platform.system", return_value="Windows"),
        patch("platform.release", return_value="8"),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        check_os_support()
        log.warning.assert_called_once()


def test_linux_supported_no_warning():
    with (
        patch("platform.system", return_value="Linux"),
        patch("distro.id", return_value="debian"),
        patch("distro.codename", return_value="forky"),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        assert check_os_support() is True
        log.warning.assert_not_called()


def test_macos_supported_no_warning():
    with (
        patch("platform.system", return_value="Darwin"),
        patch("platform.mac_ver", return_value=("13.5", ("", "", ""), "")),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        assert check_os_support() is True
        log.warning.assert_not_called()
