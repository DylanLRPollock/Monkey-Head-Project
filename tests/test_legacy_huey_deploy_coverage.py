"""Exercise the dependency-free Docker/Kubernetes deployment helper."""

from __future__ import annotations

import argparse
import subprocess

import pytest

from huey.memory.PY import Huey


def test_check_error_and_required_tool_validation(monkeypatch, caplog):
    Huey.check_error(subprocess.CompletedProcess([], 0), "deployment")
    with pytest.raises(RuntimeError, match="deployment failed with error code 3"):
        Huey.check_error(subprocess.CompletedProcess([], 3), "deployment")
    assert "Error: deployment failed with error code 3." in caplog.text

    available = {"docker"}
    monkeypatch.setattr(
        Huey.shutil, "which", lambda tool: tool if tool in available else None
    )
    Huey.require_tools(["docker"])
    with pytest.raises(EnvironmentError, match="docker-compose, kubectl"):
        Huey.require_tools(["docker-compose", "kubectl"])


def test_prepare_environment_creates_directory(tmp_path):
    workdir = tmp_path / "Huey"
    Huey.prepare_environment(str(workdir))
    assert workdir.is_dir()


@pytest.mark.parametrize("returncode", [0, 4])
def test_build_image_checks_docker_result(monkeypatch, returncode):
    calls = []
    monkeypatch.setattr(
        Huey.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs))
        or subprocess.CompletedProcess(command, returncode),
    )

    if returncode:
        with pytest.raises(RuntimeError, match="Build Huey Docker Image failed"):
            Huey.build_image("custom:tag", "context-dir")
    else:
        Huey.build_image("custom:tag", "context-dir")

    assert calls[0][0] == ["docker", "build", "-t", "custom:tag", "context-dir"]
    assert calls[0][1]["stdout"] == subprocess.PIPE
    assert calls[0][1]["stderr"] == subprocess.PIPE


@pytest.mark.parametrize("failure_at", [None, 0, 1])
def test_deploy_huey_runs_compose_and_kubectl_with_failures(
    tmp_path, monkeypatch, failure_at
):
    workdir = tmp_path / "work"
    workdir.mkdir()
    monkeypatch.chdir(tmp_path)
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        code = 2 if len(calls) - 1 == failure_at else 0
        return subprocess.CompletedProcess(command, code)

    monkeypatch.setattr(Huey.subprocess, "run", run)
    if failure_at == 0:
        with pytest.raises(RuntimeError, match="Huey Deployment failed"):
            Huey.deploy_huey(str(workdir), "compose.yml", "cluster.yml")
        assert len(calls) == 1
    elif failure_at == 1:
        with pytest.raises(RuntimeError, match="Kubernetes Deployment failed"):
            Huey.deploy_huey(str(workdir), "compose.yml", "cluster.yml")
        assert len(calls) == 2
    else:
        Huey.deploy_huey(str(workdir), "compose.yml", "cluster.yml")
        assert len(calls) == 2

    assert calls[0][0] == ["docker-compose", "-f", "compose.yml", "up", "-d"]
    assert calls[0][1]["stdout"] == subprocess.PIPE
    if failure_at != 0:
        assert calls[1][0] == ["kubectl", "apply", "-f", "cluster.yml"]
        assert calls[1][1]["stderr"] == subprocess.PIPE


def test_parse_args_accepts_deployment_overrides(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "Huey.py",
            "--tag",
            "huey:test",
            "--context",
            "image-src",
            "--compose-file",
            "compose.test.yml",
            "--k8s-file",
            "huey.test.yaml",
            "--workdir",
            "/tmp/huey",
            "--build-only",
        ],
    )
    args = Huey.parse_args()
    assert args == argparse.Namespace(
        tag="huey:test",
        context="image-src",
        compose_file="compose.test.yml",
        k8s_file="huey.test.yaml",
        workdir="/tmp/huey",
        build_only=True,
        deploy_only=False,
    )


@pytest.mark.parametrize(
    ("build_only", "deploy_only", "expected"),
    [
        (False, False, ["build", "deploy"]),
        (True, False, ["build"]),
        (False, True, ["deploy"]),
        (True, True, []),
    ],
)
def test_main_selects_build_and_deploy_steps(
    monkeypatch, build_only, deploy_only, expected
):
    calls = []
    monkeypatch.setattr(
        Huey,
        "parse_args",
        lambda: argparse.Namespace(
            tag="tag",
            context="context",
            compose_file="compose.yml",
            k8s_file="huey.yml",
            workdir="/tmp/work",
            build_only=build_only,
            deploy_only=deploy_only,
        ),
    )
    monkeypatch.setattr(Huey, "require_tools", lambda tools: calls.append("tools"))
    monkeypatch.setattr(
        Huey, "prepare_environment", lambda path: calls.append("prepare")
    )
    monkeypatch.setattr(Huey, "build_image", lambda *_args: calls.append("build"))
    monkeypatch.setattr(Huey, "deploy_huey", lambda *_args: calls.append("deploy"))

    Huey.main()

    assert calls == ["tools", "prepare", *expected]
