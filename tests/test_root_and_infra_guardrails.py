"""Regression tests for root entrypoint diagnostics and host preflight checks."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import run as root_run
from infra.docker.docker import orchestrator_utils


def test_root_run_error_keeps_readable_diagnostic_and_pickle_args():
    error = root_run.RunError("runtime failed", "check the installation")

    assert str(error) == ("error: runtime failed\nhint:  check the installation")
    assert error.args == ("runtime failed", "check the installation")


def test_setup_error_keeps_readable_diagnostic_and_pickle_args():
    setup_path = Path(__file__).parents[1] / "setup.py"
    spec = importlib.util.spec_from_file_location("huey_setup_compat", setup_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    error = module.SetupError("metadata missing", "restore pyproject.toml")

    assert str(error) == "error: metadata missing\nhint:  restore pyproject.toml"
    assert error.args == ("metadata missing", "restore pyproject.toml")


def test_system_preflight_checks_os_disk_connectivity_and_commands(monkeypatch):
    logger = logging.getLogger("orchestrator-test")
    commands = []
    monkeypatch.setattr(
        orchestrator_utils,
        "_read_os_release",
        lambda: {"pretty_name": "Example Linux", "id": "example"},
    )
    monkeypatch.setattr(
        orchestrator_utils.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=10 * 1024**3),
    )
    monkeypatch.setattr(
        orchestrator_utils,
        "run",
        lambda argv, _logger, check=False: (
            commands.append((argv, check)) or SimpleNamespace(returncode=0)
        ),
    )
    monkeypatch.setattr(orchestrator_utils.shutil, "which", lambda _name: "/bin/tool")

    orchestrator_utils.ensure_system_requirements(
        logger=logger,
        allowed_distros=("example",),
        min_free_gib=5,
        ping_hosts=("example.invalid",),
        required_commands=("docker",),
    )

    assert commands == [(["ping", "-c", "1", "-W", "2", "example.invalid"], False)]


def test_system_preflight_rejects_unsupported_os_before_host_checks(monkeypatch):
    logger = logging.getLogger("orchestrator-test")
    monkeypatch.setattr(
        orchestrator_utils,
        "_read_os_release",
        lambda: {"pretty_name": "Unknown OS", "id": "unknown"},
    )
    monkeypatch.setattr(
        orchestrator_utils.shutil,
        "disk_usage",
        lambda _path: (_ for _ in ()).throw(AssertionError("disk check ran")),
    )
    monkeypatch.setattr(
        orchestrator_utils,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("connectivity check ran")
        ),
    )

    with pytest.raises(RuntimeError, match="Unsupported distribution"):
        orchestrator_utils.ensure_system_requirements(
            logger=logger,
            allowed_distros=("debian",),
            ping_hosts=(),
        )
