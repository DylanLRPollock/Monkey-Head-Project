"""Installer authorization must precede path access and host changes."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from huey.memory.PY import installer


def test_installer_denial_and_dry_run_do_not_select_or_touch_host(monkeypatch):
    select = Mock(side_effect=AssertionError("unexpected prompt or filesystem write"))
    run = Mock(side_effect=AssertionError("unexpected subprocess"))
    monkeypatch.setattr(installer, "select_hardware", select)
    monkeypatch.setattr(installer.subprocess, "run", run)

    assert installer.run_installer() == 2
    assert installer.run_installer(dry_run=True) == 0

    select.assert_not_called()
    run.assert_not_called()


def test_confirmed_installer_uses_project_script_with_timeout(monkeypatch, tmp_path):
    script = tmp_path / "install.sh"
    script.write_text("exit 0\n", encoding="utf-8")
    paths = SimpleNamespace(
        install=script,
        host=SimpleNamespace(system="Linux"),
        command_for=lambda action: ["bash", str(script)] if action == "install" else [],
    )
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(installer, "resolve_platform_script_paths", lambda _root: paths)
    monkeypatch.setattr(installer, "ensure_admin_privileges", Mock())
    monkeypatch.setattr(installer, "update_submodules", Mock())
    monkeypatch.setattr(installer, "display_license", Mock())
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(installer.subprocess, "run", run)

    result = installer.run_installer(confirmed=True, actor_role="operator")

    assert result == 0
    args, kwargs = run.call_args
    assert args[0] == ["bash", str(script)]
    assert kwargs["check"] is True
    assert kwargs["shell"] is False
    assert kwargs["timeout"] == 1200
    assert kwargs["cwd"] == tmp_path
    assert kwargs["env"]["MHP_HARDWARE"] == "general"
    assert kwargs["env"]["MHP_SOFTWARE"] == "auto"
