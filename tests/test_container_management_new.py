# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Container Management New module (tests)

from unittest.mock import patch

import pytest

pytest.importorskip("requests")

from huey.os.services.container_management import (
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
        scale_deployment("monkey-head", 2, confirmed=True, actor_role="operator")


def test_get_pod_logs():
    with patch("subprocess.run", return_value=DummyCompleted(stdout=b"log")):
        logs = get_pod_logs("monkey-head-0")
        assert logs == "log"


def test_cleanup_kubernetes():
    with patch("subprocess.run", return_value=DummyCompleted()), patch("os.chdir"):
        cleanup_kubernetes(
            "src/huey/memory/YAML/deployment.yaml",
            confirmed=True,
            actor_role="admin",
        )


def test_build_docker_image():
    with patch("subprocess.run", return_value=DummyCompleted()):
        build_docker_image(confirmed=True, actor_role="operator")


def test_stop_containers():
    with patch("subprocess.run", return_value=DummyCompleted()), patch("os.chdir"):
        stop_containers(confirmed=True, actor_role="admin")


def test_cleanup_images():
    with patch("subprocess.run", return_value=DummyCompleted()):
        cleanup_images(confirmed=True, actor_role="admin")


def test_manage_networks():
    with patch("subprocess.run", return_value=DummyCompleted()):
        manage_networks(confirmed=True, actor_role="operator")


def test_mutating_container_commands_default_to_deny_without_spawning():
    with patch("subprocess.run", side_effect=AssertionError("spawned")) as run:
        with pytest.raises(PermissionError):
            build_docker_image()
        with pytest.raises(PermissionError):
            stop_containers()
    run.assert_not_called()


def test_container_dry_run_skips_path_and_subprocess_access(monkeypatch):
    from huey.os.services import container_management

    root = patch.object(
        container_management, "_project_root", side_effect=AssertionError("touched")
    )
    with root, patch("subprocess.run", side_effect=AssertionError("spawned")) as run:
        build_docker_image(dry_run=True)
        cleanup_kubernetes(dry_run=True)
    run.assert_not_called()


def test_kubernetes_manifest_and_resource_arguments_are_validated(tmp_path):
    with patch("subprocess.run", side_effect=AssertionError("spawned")) as run:
        with pytest.raises(ValueError, match="manifest must be"):
            cleanup_kubernetes(
                tmp_path / "outside.yaml", confirmed=True, actor_role="admin"
            )
        with pytest.raises(ValueError, match="deployment name or replica count"):
            scale_deployment(
                "../deployment", 1, confirmed=True, actor_role="operator"
            )
        with pytest.raises(ValueError, match="deployment name or replica count"):
            scale_deployment(
                "valid-name", -1, confirmed=True, actor_role="operator"
            )
    run.assert_not_called()


def test_list_containers():
    with patch("subprocess.run", return_value=DummyCompleted(stdout=b"list")):
        output = list_containers()
        assert output == "list"


def test_get_container_logs():
    with patch("subprocess.run", return_value=DummyCompleted(stdout=b"logs")):
        logs = get_container_logs("monkey-head")
        assert logs == "logs"
