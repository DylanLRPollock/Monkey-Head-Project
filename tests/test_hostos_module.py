from unittest.mock import patch

from docker.HostOS.HostOS import (
    enable_services,
    check_virtualization,
    configure_firewall,
)


class DummyCompleted:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.stdout = b""
        self.stderr = b""


def test_enable_services():
    with patch("subprocess.run", return_value=DummyCompleted()):
        enable_services()


def test_check_virtualization():
    with patch("subprocess.check_output", return_value=b"vmx"):
        check_virtualization()


def test_configure_firewall():
    with patch("subprocess.run", return_value=DummyCompleted()):
        configure_firewall(1234)
