# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Container Management New module (tests)

from unittest.mock import patch

import pytest

pytest.importorskip("requests")

from hueyos.services.container_management import (
    build_docker_image,
    cleanup_images,
    cleanup_kubernetes,
    get_container_logs,
    get_pod_logs,
    list_containers,
    manage_networks,
    scale_deployment,
    stop_containers,
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
            cleanup_kubernetes("k8s/deployment.yaml")


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


def test_list_containers():
    with patch("subprocess.run", return_value=DummyCompleted(stdout=b"list")):
        output = list_containers()
        assert output == "list"


def test_get_container_logs():
    with patch("subprocess.run", return_value=DummyCompleted(stdout=b"logs")):
        logs = get_container_logs("monkey-head")
        assert logs == "logs"
