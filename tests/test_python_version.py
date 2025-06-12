from unittest.mock import patch

from monkey_head.core.system_checks import check_python_version


def test_python_313_warning():
    with patch("monkey_head.core.system_checks.sys.version_info", (3, 13, 0)), patch(
        "monkey_head.core.system_checks.logger"
    ) as log:
        check_python_version()
        log.warning.assert_called_once()


def test_python_supported_no_warning():
    with patch("monkey_head.core.system_checks.sys.version_info", (3, 12, 0)), patch(
        "monkey_head.core.system_checks.logger"
    ) as log:
        check_python_version()
        log.warning.assert_not_called()
