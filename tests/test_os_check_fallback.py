# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Os Check Fallback module (tests)

from unittest.mock import patch

from huey.os.core.system_checks import check_os_support


def test_linux_fallback_no_warning():
    with (
        patch("platform.system", return_value="Linux"),
        patch("huey.os.core.system_checks.distro", None),
        patch(
            "platform.freedesktop_os_release",
            return_value={"ID": "debian", "VERSION_CODENAME": "forky"},
        ),
        patch("huey.os.core.system_checks.logger") as log,
    ):
        check_os_support()
        log.warning.assert_not_called()
