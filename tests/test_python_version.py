# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Python Version module (tests)

from unittest.mock import patch

from hueyos.core.system_checks import check_python_version


def test_python_313_warning():
    with (
        patch("hueyos.core.system_checks.sys.version_info", (3, 13, 0)),
        patch("hueyos.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_called_once()


def test_python_314_supported_no_warning():
    with (
        patch("hueyos.core.system_checks.sys.version_info", (3, 14, 1)),
        patch("hueyos.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_not_called()


def test_python_315_warning():
    with (
        patch("hueyos.core.system_checks.sys.version_info", (3, 15, 0)),
        patch("hueyos.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_called_once()
