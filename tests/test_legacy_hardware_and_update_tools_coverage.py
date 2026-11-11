"""Exercise legacy hardware, update, installation, and Huey deployment helpers."""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest


def _reload(name: str):
    return importlib.reload(importlib.import_module(f"huey.memory.PY.{name}"))


def test_hardware_interface_routes_commands_to_configured_paths(monkeypatch):
    module = _reload("hardware_interface")
    calls = []
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)) or "result",
    )
    monkeypatch.setenv("HOSTOS_PATH", "/host")
    monkeypatch.setenv("SUBOS_PATH", "/sub")
    monkeypatch.setenv("NANOOS_PATH", "/nano")

    assert module.send_hostos(["echo", "host"]) == "result"
    assert module.send_subos(["echo", "sub"]) == "result"
    assert module.send_nanoos(["echo", "nano"]) == "result"
    assert [call[0][0][0] for call in calls] == ["echo", "echo", "echo"]
    assert [call[1]["cwd"] for call in calls] == [
        Path("/host"),
        Path("/sub"),
        Path("/nano"),
    ]


def test_installation_steps_run_and_report_failures(monkeypatch):
    module = _reload("installations")
    errors = []
    monkeypatch.setattr(module, "check_error", lambda result, name: errors.append(name))
    calls = []
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: (
            calls.append((args, kwargs)) or SimpleNamespace(returncode=0)
        ),
    )

    module.install_common_tools()
    module.install_additional_tools()
    module.install_optional_tools()
    assert len(calls) == 3
    assert errors == [
        "Common Tools Installation",
        "Additional Tools Installation",
        "Optional Tools Installation",
    ]

    def fail(result, name):
        raise RuntimeError(name)

    monkeypatch.setattr(module, "check_error", fail)
    with pytest.raises(RuntimeError, match="Common Tools Installation"):
        module.install_common_tools()


def test_update_commands_authorization_and_failures(monkeypatch):
    core = ModuleType("huey.memory.core")
    core.__path__ = []
    checks = ModuleType("huey.memory.core.system_checks")
    checks.check_error = lambda *_args: None
    monkeypatch.setitem(sys.modules, "huey.memory.core", core)
    monkeypatch.setitem(sys.modules, "huey.memory.core.system_checks", checks)
    module = _reload("updates")
    authorization = Mock()
    checked = []
    monkeypatch.setattr(module, "authorize_privileged_operation", authorization)
    monkeypatch.setattr(
        module, "check_error", lambda result, label: checked.append(label)
    )
    commands = []
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: (
            commands.append(args[0]) or SimpleNamespace(returncode=0)
        ),
    )

    assert module.update_system(confirmed=True, actor_role="admin") is True
    assert module.update_python_packages(confirmed=True, actor_role="admin") is True
    assert len(commands) == 4
    assert checked == [
        "System Update",
        "System Upgrade",
        "Pip Upgrade",
        "Update Python Packages",
    ]
    assert authorization.call_count == 2

    monkeypatch.setattr(
        module, "check_error", Mock(side_effect=RuntimeError("update failed"))
    )
    with pytest.raises(RuntimeError, match="update failed"):
        module.update_system(confirmed=True, actor_role="admin")


def test_huey_environment_helpers_and_deployment_paths(monkeypatch, tmp_path):
    module = _reload("Huey")
    monkeypatch.setattr(module.shutil, "which", lambda _tool: "/bin/tool")
    module.require_tools(["python"])
    monkeypatch.setattr(
        module.shutil, "which", lambda tool: None if tool == "missing" else "/bin/tool"
    )
    with pytest.raises(EnvironmentError, match="missing"):
        module.require_tools(["python", "missing"])

    workdir = tmp_path / "huey"
    module.prepare_environment(str(workdir))
    assert workdir.is_dir()
    monkeypatch.setattr(module.os, "chdir", lambda path: None)
    monkeypatch.setattr(
        module.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=0))
    )
    module.build_image("tag", "context")
    module.deploy_huey(str(workdir), "compose.yml", "cluster.yml")
    assert module.subprocess.run.call_count == 3

    monkeypatch.setattr(
        module.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=4))
    )
    with pytest.raises(RuntimeError, match="Build Huey Docker Image"):
        module.build_image()
    with pytest.raises(RuntimeError, match="Huey Deployment"):
        module.deploy_huey(str(workdir))


def test_huey_main_flags_and_script_entrypoint(monkeypatch, tmp_path):
    module = _reload("Huey")
    monkeypatch.setattr(sys, "argv", ["Huey.py", "--tag", "test", "--build-only"])
    assert module.parse_args().tag == "test"

    calls = []
    monkeypatch.setattr(
        module, "require_tools", lambda tools: calls.append(("tools", tools))
    )
    monkeypatch.setattr(
        module, "prepare_environment", lambda path: calls.append(("prepare", path))
    )
    monkeypatch.setattr(
        module, "build_image", lambda *args: calls.append(("build", args))
    )
    monkeypatch.setattr(
        module, "deploy_huey", lambda *args: calls.append(("deploy", args))
    )
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: SimpleNamespace(
            workdir="/tmp/huey",
            deploy_only=False,
            build_only=True,
            tag="custom",
            context="ctx",
            compose_file="compose.yml",
            k8s_file="cluster.yml",
        ),
    )
    module.main()
    assert [entry[0] for entry in calls] == ["tools", "prepare", "build"]

    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: SimpleNamespace(
            workdir="/tmp/huey",
            deploy_only=True,
            build_only=False,
            tag="custom",
            context="ctx",
            compose_file="compose.yml",
            k8s_file="cluster.yml",
        ),
    )
    module.main()
    assert calls[-1][0] == "deploy"

    legacy_dir = Path(__file__).parents[1] / "src" / "huey" / "memory" / "PY"
    script = legacy_dir / "Huey.py"
    monkeypatch.setattr(module.shutil, "which", lambda _tool: "/bin/tool")
    monkeypatch.setattr(
        module.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=0))
    )
    monkeypatch.setattr(module.os, "chdir", lambda _path: None)
    monkeypatch.setattr(
        sys, "argv", [str(script), "--workdir", str(tmp_path), "--build-only"]
    )
    runpy.run_path(str(script), run_name="__main__")
