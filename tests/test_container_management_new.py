import subprocess
from unittest.mock import patch

from monkey_head.services.container_management import (
    scale_deployment,
    get_pod_logs,
    cleanup_kubernetes,
)


class DummyCompleted:
    def __init__(self, stdout=b"", returncode=0):
        self.stdout = stdout
        self.stderr = b""
        self.returncode = returncode


def test_scale_deployment():
    with patch("subprocess.run", return_value=DummyCompleted()):
        scale_deployment("monkey-head", 2)


def test_get_pod_logs():
    with patch("subprocess.run", return_value=DummyCompleted(stdout=b"log")):
        logs = get_pod_logs("monkey-head-0")
        assert logs == "log"


def test_cleanup_kubernetes():
    with patch("subprocess.run", return_value=DummyCompleted()):
        with patch("os.chdir"):
            cleanup_kubernetes("deployment.yaml")
