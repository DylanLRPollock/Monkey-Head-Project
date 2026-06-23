# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Python Version module (tests)

from unittest.mock import patch

from huey.os.core.system_checks import check_python_version


def test_python_312_warning():
    with (
        patch("huey.os.core.system_checks.sys.version_info", (3, 12, 0)),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_called_once()


def test_python_313_supported_no_warning():
    with (
        patch("huey.os.core.system_checks.sys.version_info", (3, 13, 1)),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_not_called()


def test_python_314_testing_lane_warning():
    with (
        patch("huey.os.core.system_checks.sys.version_info", (3, 14, 0)),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_called_once()


def test_python_313t_warning():
    with (
        patch("huey.os.core.system_checks.sys.version_info", (3, 13, 1)),
        patch("huey.os.core.system_checks._is_free_threaded_build", return_value=True),
        patch("huey.os.core.system_checks._python_gil_enabled", return_value=False),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        check_python_version()
        log.warning.assert_called_once()
