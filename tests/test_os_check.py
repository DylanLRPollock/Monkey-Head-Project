from unittest.mock import patch

from monkey_head.core.system_checks import check_os_support


def test_windows_warning():
    with patch('platform.system', return_value='Windows'), \
         patch('platform.release', return_value='8'), \
         patch('monkey_head.core.system_checks.logger') as log:
        check_os_support()
        log.warning.assert_called_once()


def test_linux_supported_no_warning():
    with patch('platform.system', return_value='Linux'), \
         patch('distro.id', return_value='debian'), \
         patch('distro.codename', return_value='trixie'), \
         patch('monkey_head.core.system_checks.logger') as log:
        check_os_support()
        log.warning.assert_not_called()


def test_macos_old_warning():
    with patch('platform.system', return_value='Darwin'), \
         patch('platform.mac_ver', return_value=('12.5', ('', '', ''), '')), \
         patch('monkey_head.core.system_checks.logger') as log:
        check_os_support()
        log.warning.assert_called_once()
