"""Mocked coverage for installation management entry points."""

from __future__ import annotations

import importlib
import subprocess
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

_script_dir = Path(__file__).resolve().parents[1] / "src/huey/memory/PY"
sys.path.insert(0, str(_script_dir))
uninstaller = importlib.import_module("uninstaller")
repair = importlib.import_module("repair")
fresh_install = importlib.import_module("fresh_install")
_previous_run = sys.modules.get("run")
_run_stub = types.ModuleType("run")
_run_stub.main = lambda: None
sys.modules["run"] = _run_stub
try:
    launcher = importlib.import_module("launcher")
finally:
    if _previous_run is None:
        sys.modules.pop("run", None)
    else:
        sys.modules["run"] = _previous_run


def _paths(script, command=None, system="Linux"):
    return SimpleNamespace(
        uninstall=script,
        host=SimpleNamespace(system=system),
        command_for=lambda _name: command if command is not None else [str(script)],
    )


def _authorize(monkeypatch, outcome=True):
    monkeypatch.setattr(
        uninstaller,
        "authorize_privileged_operation",
        lambda *args, **kwargs: outcome,
    )


def test_uninstaller_authorization_and_platform_branches(monkeypatch, capsys):
    _authorize(monkeypatch, False)
    assert uninstaller.run_uninstaller() == 0
    assert "dry-run" in capsys.readouterr().out
    monkeypatch.setattr(
        uninstaller,
        "authorize_privileged_operation",
        lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )
    assert uninstaller.run_uninstaller() == 2
    assert "denied" in capsys.readouterr().out
    _authorize(monkeypatch, True)
    monkeypatch.setattr(
        uninstaller,
        "resolve_platform_script_paths",
        lambda _root: _paths(None, system="UnknownOS"),
    )
    assert uninstaller.run_uninstaller(confirmed=True) == 1
    assert "Unsupported operating system" in capsys.readouterr().out


@pytest.mark.parametrize(
    "failure,expected",
    [
        (subprocess.TimeoutExpired("uninstall", 1200), 124),
        (subprocess.CalledProcessError(6, "uninstall"), 6),
        (OSError("missing executable"), 1),
    ],
)
def test_uninstaller_subprocess_failures(
    monkeypatch, tmp_path, capsys, failure, expected
):
    script = tmp_path / "uninstall.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(uninstaller, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        uninstaller, "resolve_platform_script_paths", lambda _root: _paths(script)
    )
    _authorize(monkeypatch, True)
    monkeypatch.setattr(
        uninstaller.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(failure),
    )
    assert uninstaller.run_uninstaller(confirmed=True) == expected
    assert capsys.readouterr().out


def test_uninstaller_rejects_invalid_command_and_escape(monkeypatch, tmp_path):
    script = tmp_path / "uninstall.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(uninstaller, "PROJECT_ROOT", root)
    _authorize(monkeypatch, True)
    monkeypatch.setattr(
        uninstaller,
        "resolve_platform_script_paths",
        lambda _root: _paths(script, command=[]),
    )
    assert uninstaller.run_uninstaller(confirmed=True) == 2
    monkeypatch.setattr(
        uninstaller, "resolve_platform_script_paths", lambda _root: _paths(script)
    )
    assert uninstaller.run_uninstaller(confirmed=True) == 2
    link = root / "link.sh"
    link.symlink_to(script)
    monkeypatch.setattr(
        uninstaller, "resolve_platform_script_paths", lambda _root: _paths(link)
    )
    assert uninstaller.run_uninstaller(confirmed=True) == 1


def test_fresh_install_authorization_routes_and_uninstall_failure(monkeypatch, capsys):
    monkeypatch.setattr(
        fresh_install,
        "authorize_privileged_operation",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError()),
    )
    assert fresh_install.run_fresh_install(confirmed=True) == 2
    monkeypatch.setattr(
        fresh_install, "authorize_privileged_operation", lambda *a, **k: None
    )
    seen = []
    monkeypatch.setattr(
        fresh_install.repair, "run_repair", lambda *a, **k: seen.append((a, k)) or 9
    )
    assert (
        fresh_install.run_fresh_install(
            "github", "https://example.test/repo", confirmed=True
        )
        == 9
    )
    assert seen[0][0][0] == "https://example.test/repo"
    monkeypatch.setattr(fresh_install.uninstaller, "run_uninstaller", lambda **k: 5)
    assert fresh_install.run_fresh_install("local", confirmed=True) == 5
    assert "Uninstall failed" in capsys.readouterr().out
    assert fresh_install.parse_args(["--source", "github", "--yes"]).yes


def test_fresh_install_local_success_and_source_prompt(monkeypatch):
    monkeypatch.setattr(
        fresh_install, "authorize_privileged_operation", lambda *a, **k: None
    )
    monkeypatch.setattr(fresh_install.uninstaller, "run_uninstaller", lambda **k: 0)
    monkeypatch.setattr(fresh_install.installer, "run_installer", lambda **k: 3)
    assert fresh_install.run_fresh_install("local", confirmed=True) == 3
    monkeypatch.setattr(fresh_install.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "github")
    monkeypatch.setattr(fresh_install.repair, "run_repair", lambda *a, **k: 4)
    assert fresh_install.run_fresh_install(confirmed=True) == 4


def test_repair_permission_and_uninstall_short_circuit(monkeypatch, capsys):
    monkeypatch.setattr(
        repair,
        "authorize_privileged_operation",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError()),
    )
    assert repair.run_repair() == 2
    monkeypatch.setattr(repair, "authorize_privileged_operation", lambda *a, **k: None)
    monkeypatch.setattr(repair.uninstaller, "run_uninstaller", lambda **k: 7)
    assert repair.run_repair(confirmed=True) == 7
    assert "Uninstall failed" in capsys.readouterr().out


def test_repair_handles_clone_failure_and_missing_installer(
    monkeypatch, capsys, tmp_path
):
    monkeypatch.setattr(repair, "authorize_privileged_operation", lambda *a, **k: None)
    monkeypatch.setattr(repair.uninstaller, "run_uninstaller", lambda **k: 0)
    monkeypatch.setattr(
        repair.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=8, stderr=b"clone failed"),
    )
    assert repair.run_repair(confirmed=True) == 8
    assert "clone failed" in capsys.readouterr().err
    monkeypatch.setattr(
        repair.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stderr=b""),
    )
    monkeypatch.setattr(
        repair.tempfile,
        "TemporaryDirectory",
        lambda: _TemporaryDir(tmp_path),
    )
    assert repair.run_repair(confirmed=True) == 1
    assert "regular file" in capsys.readouterr().out


class _TemporaryDir:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        return self.path

    def __exit__(self, *_exc):
        return False


def test_launcher_dispatches_subcommands(monkeypatch):
    calls = []
    monkeypatch.setattr(
        launcher.installer, "run_installer", lambda **k: calls.append("install") or 0
    )
    monkeypatch.setattr(
        launcher.uninstaller,
        "run_uninstaller",
        lambda **k: calls.append("uninstall") or 0,
    )
    monkeypatch.setattr(
        launcher.fresh_install,
        "run_fresh_install",
        lambda *a, **k: calls.append("fresh") or 0,
    )
    monkeypatch.setattr(launcher, "system_check", lambda: calls.append("check"))
    monkeypatch.setattr(launcher.run, "main", lambda: calls.append("run"))
    for command in (
        ["install", "--yes"],
        ["uninstall", "--yes"],
        ["fresh-install", "--yes"],
    ):
        with pytest.raises(SystemExit):
            launcher.main(command)
    launcher.main(["system-check"])
    launcher.main(["run"])
    assert calls == ["install", "uninstall", "fresh", "check", "run"]
