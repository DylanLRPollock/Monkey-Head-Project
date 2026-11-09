"""Safe tests for container and Kubernetes command orchestration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from huey.services import container_management as containers


@pytest.mark.parametrize(
    "invoke",
    [
        lambda: containers.build_docker_image(),
        lambda: containers.manage_containers(),
        lambda: containers.stop_containers(),
        lambda: containers.cleanup_images(),
        lambda: containers.manage_volumes(),
        lambda: containers.manage_networks(),
        lambda: containers.deploy_kubernetes(),
        lambda: containers.cleanup_kubernetes(),
        lambda: containers.scale_deployment("web", 2),
    ],
)
def test_denied_container_actions_never_run_commands(monkeypatch, invoke):
    authorize = Mock(return_value=False)
    run = Mock(side_effect=AssertionError("denied operation ran a command"))
    monkeypatch.setattr(containers, "authorize_privileged_operation", authorize)
    monkeypatch.setattr(containers, "_run_command", run)

    invoke()

    authorize.assert_called_once()
    run.assert_not_called()


def test_command_runner_skips_missing_executable(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(containers.shutil, "which", lambda _name: None)
    run = Mock(side_effect=AssertionError("missing executable was launched"))
    monkeypatch.setattr(containers.subprocess, "run", run)

    result = containers._run_command(["kubectl", "get", "pods"], "list pods", tmp_path)

    assert isinstance(result, subprocess.CompletedProcess)
    assert result.returncode == 0
    assert result.stdout == b""
    assert "executable is not available" in caplog.text
    run.assert_not_called()


@pytest.mark.parametrize("returncode", [0, 2])
def test_command_runner_uses_argv_and_logs_result(
    monkeypatch, tmp_path, caplog, returncode
):
    monkeypatch.setattr(containers.shutil, "which", lambda name: f"/bin/{name}")
    result = subprocess.CompletedProcess(
        ["docker", "ps"], returncode, b"container output", b""
    )
    run = Mock(return_value=result)
    monkeypatch.setattr(containers.subprocess, "run", run)

    actual = containers._run_command(["docker", "ps"], "list containers", tmp_path)

    assert actual is result
    run.assert_called_once_with(
        ["docker", "ps"],
        cwd=str(tmp_path),
        check=False,
        capture_output=True,
        shell=False,
        timeout=600,
    )
    if returncode:
        assert "failed with exit code 2" in caplog.text


def test_build_docker_image_validates_tag_before_command(monkeypatch):
    authorize = Mock(return_value=True)
    run = Mock()
    monkeypatch.setattr(containers, "authorize_privileged_operation", authorize)
    monkeypatch.setattr(containers, "_run_command", run)

    with pytest.raises(ValueError, match="Invalid Docker image tag"):
        containers.build_docker_image("bad tag", confirmed=True, actor_role="operator")
    run.assert_not_called()

    containers.build_docker_image(
        "huey/test:latest", confirmed=True, actor_role="operator"
    )
    run.assert_called_once_with(
        ["docker", "build", "-t", "huey/test:latest", "."], "Building Docker image"
    )


def test_container_and_kubernetes_commands_use_validated_paths(monkeypatch, tmp_path):
    manifest = tmp_path / "deploy.yaml"
    manifest.write_text("apiVersion: v1\n", encoding="utf-8")
    monkeypatch.setenv("MONKEY_HEAD_WORKDIR", str(tmp_path))
    monkeypatch.setattr(
        containers, "authorize_privileged_operation", lambda *a, **k: True
    )
    calls = []
    monkeypatch.setattr(
        containers, "_run_command", lambda command, description, cwd=None: calls.append(
            (command, description, cwd)
        )
    )

    containers.manage_containers(confirmed=True, actor_role="operator")
    containers.stop_containers(confirmed=True, actor_role="admin")
    containers.cleanup_images(confirmed=True, actor_role="admin")
    containers.manage_volumes(actor_role="reader")
    containers.manage_networks(actor_role="reader")
    containers.deploy_kubernetes(manifest, confirmed=True, actor_role="operator")
    containers.cleanup_kubernetes(manifest, confirmed=True, actor_role="admin")
    containers.scale_deployment(
        "web-api", 3, confirmed=True, actor_role="operator"
    )

    assert [call[0] for call in calls] == [
        ["docker-compose", "up", "-d"],
        ["docker", "ps"],
        ["docker-compose", "down"],
        ["docker", "image", "prune", "-f"],
        ["docker", "volume", "ls"],
        ["docker", "network", "ls"],
        ["kubectl", "apply", "-f", str(manifest)],
        ["kubectl", "get", "pods"],
        ["kubectl", "delete", "-f", str(manifest)],
        ["kubectl", "scale", "deployment", "web-api", "--replicas=3"],
    ]
    assert calls[0][2] == tmp_path
    assert calls[1][2] == tmp_path


@pytest.mark.parametrize(
    ("name", "replicas"),
    [("../web", 1), ("Web", 1), ("web", -1)],
)
def test_scale_deployment_rejects_invalid_values(monkeypatch, name, replicas):
    monkeypatch.setattr(
        containers, "authorize_privileged_operation", lambda *a, **k: True
    )
    run = Mock()
    monkeypatch.setattr(containers, "_run_command", run)

    with pytest.raises(ValueError, match="Invalid Kubernetes"):
        containers.scale_deployment(
            name, replicas, confirmed=True, actor_role="operator"
        )
    run.assert_not_called()


def test_manifest_validation_rejects_missing_outside_and_symlinked_paths(
    monkeypatch, tmp_path
):
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("MONKEY_HEAD_WORKDIR", str(root))

    with pytest.raises(ValueError, match="regular file inside"):
        containers._validate_manifest_path(root / "missing.yaml")

    outside = tmp_path / "outside.yaml"
    outside.write_text("apiVersion: v1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="regular file inside"):
        containers._validate_manifest_path(outside)

    target = root / "target.yaml"
    target.write_text("apiVersion: v1\n", encoding="utf-8")
    link = root / "linked.yaml"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink support unavailable: {exc}")
    with pytest.raises(ValueError, match="regular file inside"):
        containers._validate_manifest_path(link)


def test_read_only_management_and_log_helpers(monkeypatch):
    calls = []
    monkeypatch.setattr(
        containers,
        "_run_command",
        lambda command, description, cwd=None: (
            calls.append((command, description, cwd))
            or SimpleNamespace(stdout=b"captured output")
        ),
    )

    containers.kubernetes_management()
    assert containers.list_containers() == "captured output"
    assert containers.get_container_logs("huey") == "captured output"
    assert containers.get_pod_logs("api-0") == "captured output"

    assert [call[0] for call in calls] == [
        ["kubectl", "get", "nodes"],
        ["kubectl", "get", "services"],
        ["docker", "ps"],
        ["docker", "logs", "huey"],
        ["kubectl", "logs", "api-0"],
    ]
