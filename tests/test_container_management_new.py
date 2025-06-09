import subprocess
from unittest.mock import patch

from monkey_head.services.container_management import (
    scale_deployment,
    get_pod_logs,
    cleanup_kubernetes,
    build_docker_image,
    stop_containers,
    cleanup_images,
    manage_networks,
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


def test_build_docker_image():
    with patch("subprocess.run", return_value=DummyCompleted()):
        build_docker_image()


def test_stop_containers():
    with patch("subprocess.run", return_value=DummyCompleted()):
        with patch("os.chdir"):
            stop_containers()


def test_cleanup_images():
    with patch("subprocess.run", return_value=DummyCompleted()):
        cleanup_images()


def test_manage_networks():
    with patch("subprocess.run", return_value=DummyCompleted()):
        manage_networks()
