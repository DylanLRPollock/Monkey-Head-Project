"""Cover legacy install, repair, uninstall, and launcher control flow."""

from __future__ import annotations

import importlib
import runpy
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest


def _legacy_stubs(monkeypatch):
    calls = []
    installer = ModuleType("installer")
    installer.run_installer = lambda **kwargs: calls.append(("install", kwargs)) or 0
    repair = ModuleType("repair")
    repair.REPO_URL = "https://example.invalid/repo.git"
    repair.run_repair = lambda *args, **kwargs: (
        calls.append(("repair", args, kwargs)) or 0
    )
    uninstaller = ModuleType("uninstaller")
    uninstaller.run_uninstaller = lambda **kwargs: (
        calls.append(("uninstall", kwargs)) or 0
    )
    runtime = ModuleType("run")
    runtime.main = lambda: calls.append(("run", list(sys.argv)))
    for module in (installer, repair, uninstaller, runtime):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    return calls, installer, repair, uninstaller, runtime


def _reload(name: str):
    return importlib.reload(importlib.import_module(f"huey.memory.PY.{name}"))


def test_legacy_fresh_install_runs_authorized_paths_and_cli(monkeypatch, capsys):
    calls, installer, _repair, uninstaller, _runtime = _legacy_stubs(monkeypatch)
    module = _reload("fresh_install")
    assert module.parse_args(["--source", "github", "--yes"]).yes is True
    assert (
        module.run_fresh_install("github", "repo", confirmed=True, actor_role="admin")
        == 0
    )
    assert calls[-1] == (
        "repair",
        ("repo",),
        {"confirmed": True, "actor_role": "admin"},
    )

    uninstaller.run_uninstaller = lambda **_kwargs: 7
    assert module.run_fresh_install("local", confirmed=True, actor_role="admin") == 7
    assert "Uninstall failed with code 7" in capsys.readouterr().out

    uninstaller.run_uninstaller = lambda **_kwargs: 0
    installer.run_installer = lambda **_kwargs: 4
    assert module.run_fresh_install("local", confirmed=True, actor_role="admin") == 4

    monkeypatch.setattr(
        module, "authorize_privileged_operation", Mock(side_effect=PermissionError)
    )
    assert module.run_fresh_install("local") == 2


def test_legacy_fresh_install_prompts_and_main_defaults(monkeypatch):
    calls, _installer, _repair, _uninstaller, _runtime = _legacy_stubs(monkeypatch)
    module = _reload("fresh_install")
    monkeypatch.setattr(module.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _prompt: "GitHub")
    assert module.run_fresh_install(confirmed=True, actor_role="admin") == 0
    assert calls[-1][0] == "repair"
    assert module.main(["--source", "local", "--yes"]) == 0


def test_legacy_uninstaller_all_outcomes(monkeypatch, tmp_path, capsys):
    module = _reload("uninstaller")
    monkeypatch.setattr(
        module, "authorize_privileged_operation", lambda *_a, **k: not k.get("dry_run")
    )
    assert module.run_uninstaller(dry_run=True) == 0
    assert "no host changes" in capsys.readouterr().out

    monkeypatch.setattr(
        module,
        "authorize_privileged_operation",
        Mock(side_effect=PermissionError("no approval")),
    )
    assert module.run_uninstaller() == 2

    monkeypatch.setattr(
        module, "authorize_privileged_operation", lambda *_a, **_k: True
    )
    host = SimpleNamespace(system="Plan9")
    monkeypatch.setattr(
        module,
        "resolve_platform_script_paths",
        lambda _root: SimpleNamespace(uninstall=None, host=host),
    )
    assert module.run_uninstaller(confirmed=True) == 1

    outside_root = tmp_path / "project"
    outside_root.mkdir()
    outside_script = tmp_path / "uninstall.sh"
    outside_script.write_text("exit 0\n", encoding="utf-8")
    script = outside_root / "uninstall.sh"
    script.write_text("exit 0\n", encoding="utf-8")
    monkeypatch.setattr(module, "PROJECT_ROOT", outside_root)

    def set_script(path, command=None):
        monkeypatch.setattr(
            module,
            "resolve_platform_script_paths",
            lambda _root: SimpleNamespace(
                uninstall=path,
                host=SimpleNamespace(system="Linux"),
                command_for=lambda _action: command,
            ),
        )

    set_script(outside_root / "missing.sh")
    assert module.run_uninstaller(confirmed=True) == 1
    link = outside_root / "link.sh"
    link.symlink_to(outside_script)
    set_script(link)
    assert module.run_uninstaller(confirmed=True) == 1
    set_script(outside_script)
    assert module.run_uninstaller(confirmed=True) == 2
    set_script(script)
    assert module.run_uninstaller(confirmed=True) == 2
    set_script(script, ["bash", ""])
    assert module.run_uninstaller(confirmed=True) == 2
    set_script(script, ["bash", str(script)])
    monkeypatch.setattr(module.subprocess, "run", Mock(return_value=None))
    assert module.run_uninstaller(confirmed=True) == 0
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=module.subprocess.TimeoutExpired("uninstall", 1200)),
    )
    assert module.run_uninstaller(confirmed=True) == 124
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=module.subprocess.CalledProcessError(9, "uninstall")),
    )
    assert module.run_uninstaller(confirmed=True) == 9
    monkeypatch.setattr(module.subprocess, "run", Mock(side_effect=OSError("missing")))
    assert module.run_uninstaller(confirmed=True) == 1


def test_legacy_repair_authorization_clone_and_installer_results(
    monkeypatch, tmp_path, capsys
):
    _calls, _installer, _repair, uninstaller, _runtime = _legacy_stubs(monkeypatch)
    legacy_dir = Path(__file__).parents[1] / "src" / "huey" / "memory" / "PY"
    monkeypatch.syspath_prepend(str(legacy_dir))
    module = _reload("repair")
    monkeypatch.setattr(
        module,
        "authorize_privileged_operation",
        Mock(side_effect=PermissionError),
    )
    assert module.run_repair(confirmed=True) == 2

    monkeypatch.setattr(
        module, "authorize_privileged_operation", lambda *_a, **_k: None
    )
    uninstaller.run_uninstaller = lambda **_kwargs: 6
    assert module.run_repair(confirmed=True) == 6

    uninstaller.run_uninstaller = lambda **_kwargs: 0
    monkeypatch.setattr(
        module.tempfile, "TemporaryDirectory", lambda: nullcontext(str(tmp_path))
    )
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(return_value=SimpleNamespace(returncode=9, stderr=b"clone error")),
    )
    assert module.run_repair("repo") == 9
    assert "clone error" in capsys.readouterr().err

    installer = tmp_path / "scripts" / "installers" / "installer.py"
    installer.parent.mkdir(parents=True, exist_ok=True)
    installer.write_text("pass\n", encoding="utf-8")
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(
            side_effect=[
                SimpleNamespace(returncode=0, stderr=b""),
                SimpleNamespace(returncode=7),
            ]
        ),
    )
    assert module.run_repair("repo") == 7
    assert "Installer failed with code 7" in capsys.readouterr().out

    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(
            side_effect=[
                SimpleNamespace(returncode=0, stderr=b""),
                SimpleNamespace(returncode=0),
            ]
        ),
    )
    assert module.run_repair("repo") == 0

    installer.unlink()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(return_value=SimpleNamespace(returncode=0, stderr=b"")),
    )
    assert module.run_repair("repo") == 1

    installer.symlink_to(tmp_path / "outside.py")
    assert module.run_repair("repo") == 1

    privileged = importlib.import_module("huey.os.core.privileged_operations")
    monkeypatch.setattr(
        privileged,
        "authorize_privileged_operation",
        Mock(side_effect=PermissionError),
    )
    repair_path = legacy_dir / "repair.py"
    monkeypatch.setattr(sys, "argv", [str(repair_path)])
    with pytest.raises(SystemExit) as unconfirmed:
        runpy.run_path(str(repair_path), run_name="__main__")
    assert unconfirmed.value.code == 2
    monkeypatch.setattr(sys, "argv", [str(repair_path), "--yes"])
    with pytest.raises(SystemExit) as confirmed:
        runpy.run_path(str(repair_path), run_name="__main__")
    assert confirmed.value.code == 2


def test_legacy_launcher_dispatch_after_coverage_start(monkeypatch):
    calls, installer, repair, uninstaller, runtime = _legacy_stubs(monkeypatch)
    legacy_dir = Path(__file__).parents[1] / "src" / "huey" / "memory" / "PY"
    monkeypatch.syspath_prepend(str(legacy_dir))
    module = _reload("launcher")
    monkeypatch.setattr(module, "system_check", lambda: calls.append(("check", {})))

    module.main(["run", "--cli"])
    assert calls[-1][0] == "run"
    with pytest.raises(SystemExit) as install:
        module.main(["install", "--yes", "--dry-run"])
    assert install.value.code == 0
    with pytest.raises(SystemExit):
        module.main(["uninstall"])
    with pytest.raises(SystemExit):
        module.main(["fresh-install", "--source", "github", "--yes"])
    module.main(["system-check"])
    assert calls[-1][0] == "check"
    assert (
        installer.run_installer
        and repair.run_repair
        and uninstaller.run_uninstaller
        and runtime.main
    )
