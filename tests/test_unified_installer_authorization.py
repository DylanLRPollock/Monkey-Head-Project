"""The unified installer must gate before resolving paths or spawning."""

from __future__ import annotations

from unittest.mock import Mock

from huey.platform.installers.shared.installers import unified_installer


def test_unified_installer_denies_and_dry_run_without_host_access(monkeypatch):
    resolve = Mock(side_effect=AssertionError("path discovery occurred"))
    run = Mock(side_effect=AssertionError("subprocess spawned"))
    monkeypatch.setattr(unified_installer, "detect_target", resolve)
    monkeypatch.setattr(unified_installer.subprocess, "run", run)

    assert unified_installer.main([]) == 2
    assert unified_installer.main(["--dry-run"]) == 0

    resolve.assert_not_called()
    run.assert_not_called()


def test_unified_installer_confirmed_run_is_project_bound_and_timed(
    monkeypatch, tmp_path
):
    script = tmp_path / "install.sh"
    script.write_text("exit 0\n", encoding="utf-8")
    monkeypatch.setattr(unified_installer, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(unified_installer, "detect_target", lambda: "debian")
    monkeypatch.setattr(unified_installer, "select_script", lambda _target: script)
    monkeypatch.setattr(
        unified_installer, "build_command", lambda _target, _args: ["bash", str(script)]
    )
    run = Mock()
    monkeypatch.setattr(unified_installer.subprocess, "run", run)

    assert unified_installer.main(["--yes", "--target", "debian"]) == 0

    run.assert_called_once_with(
        ["bash", str(script)], check=True, shell=False, timeout=1200, cwd=tmp_path
    )
