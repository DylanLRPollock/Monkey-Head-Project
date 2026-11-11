"""The unified installer must gate before resolving paths or spawning."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

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


def test_unified_installer_rejects_unknown_target_and_missing_scripts(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(unified_installer, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(unified_installer, "detect_target", lambda: "unknown")
    monkeypatch.setattr(unified_installer, "_normalize_target", lambda _target: "unknown")
    assert unified_installer.main(["--yes"]) == 1
    assert "Unsupported OS" in capsys.readouterr().err

    monkeypatch.setattr(unified_installer, "detect_target", lambda: "linux")
    monkeypatch.setattr(unified_installer, "_normalize_target", lambda _target: "linux")
    monkeypatch.setattr(unified_installer, "select_script", lambda _target: tmp_path / "missing.sh")
    assert unified_installer.main(["--yes"]) == 1
    assert "Installer script not found" in capsys.readouterr().err


def test_unified_installer_rejects_symlink_and_script_outside_project(
    monkeypatch, tmp_path, capsys
):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.sh"
    outside.write_text("exit 0\n", encoding="utf-8")
    link = root / "install.sh"
    link.symlink_to(outside)
    monkeypatch.setattr(unified_installer, "REPO_ROOT", root)
    monkeypatch.setattr(unified_installer, "select_script", lambda _target: link)
    assert unified_installer.main(["--yes", "--target", "linux"]) == 1
    assert "Installer script not found" in capsys.readouterr().err

    monkeypatch.setattr(unified_installer, "select_script", lambda _target: outside)
    assert unified_installer.main(["--yes", "--target", "linux"]) == 2
    assert "inside the project directory" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (pytest.param("timeout", 124, id="timeout")),
        (pytest.param("failure", 23, id="installer-error")),
    ],
)
def test_unified_installer_reports_subprocess_failures(
    monkeypatch, tmp_path, capsys, error, expected
):
    script = tmp_path / "install.sh"
    script.write_text("exit 0\n", encoding="utf-8")
    monkeypatch.setattr(unified_installer, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(unified_installer, "select_script", lambda _target: script)
    monkeypatch.setattr(unified_installer, "build_command", lambda _target, args: ["installer", *args])
    failure = (
        unified_installer.subprocess.TimeoutExpired("installer", 1200)
        if error == "timeout"
        else unified_installer.subprocess.CalledProcessError(23, "installer")
    )
    monkeypatch.setattr(unified_installer.subprocess, "run", Mock(side_effect=failure))
    assert unified_installer.main(["--yes", "--target", "linux", "--", "--quiet"]) == expected
    if error == "timeout":
        assert "Installer timed out" in capsys.readouterr().err
