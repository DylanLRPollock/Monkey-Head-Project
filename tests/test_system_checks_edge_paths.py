"""Cover system-check policy edges without relying on the host machine."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from huey.os import system_checks
from huey.os.core.platform_support import HostPlatform


def _host(
    family,
    system,
    *,
    release="",
    version="",
    is_linux=False,
    is_windows=False,
    is_macos=False,
):
    return HostPlatform(
        family=family,
        system=system,
        release=release,
        version=version,
        machine="test",
        sys_platform=family,
        display_name=system,
        is_windows=is_windows,
        is_macos=is_macos,
        is_linux=is_linux,
        is_unknown=family == "unknown",
        is_wsl=False,
        distribution_id="",
        distribution_codename="",
        distribution_like=(),
    )


def test_admin_and_command_errors_raise_only_when_needed(monkeypatch):
    monkeypatch.setattr(system_checks, "require_admin_privileges", lambda: None)
    system_checks.ensure_admin()
    monkeypatch.setattr(
        system_checks,
        "require_admin_privileges",
        lambda: (_ for _ in ()).throw(PermissionError("not root")),
    )
    with pytest.raises(PermissionError, match="not root"):
        system_checks.ensure_admin()

    system_checks.check_error(SimpleNamespace(returncode=0), "ok")
    system_checks.check_error(object(), "missing returncode")
    with pytest.raises(RuntimeError, match="deploy failed with error code 7"):
        system_checks.check_error(SimpleNamespace(returncode=7), "deploy")


def test_os_support_handles_unknown_os_and_platform_version_fallbacks(monkeypatch):
    assert not system_checks.check_os_support(_host("unknown", ""))
    assert system_checks.check_os_support(
        _host("windows", "Windows", version="Windows 11", is_windows=True)
    )
    assert not system_checks.check_os_support(
        _host("windows", "Windows", release="preview", is_windows=True)
    )

    monkeypatch.setattr(system_checks.platform, "mac_ver", lambda: ("", (), ""))
    assert not system_checks.check_os_support(
        _host("macos", "macOS", version="11.7", is_macos=True)
    )
    assert system_checks.check_os_support(
        _host("macos", "macOS", release="14.1", is_macos=True)
    )


@pytest.mark.parametrize(
    ("release", "valid", "role"),
    [
        ("unknown", False, ""),
        ("6.18.2-generic", False, ""),
        ("6.18.2-hueyos-", False, ""),
        ("6.18.2-hueyos-bad$role", False, "bad$role"),
    ],
)
def test_kernel_policy_rejects_missing_or_invalid_roles(
    monkeypatch, release, valid, role
):
    monkeypatch.setattr(system_checks.platform, "release", lambda: release)
    result = system_checks.check_kernel_policy()
    assert result["role_valid"] is valid
    assert result["detected_role"] == role
    assert result["errors"]


def test_windows_tool_fallback_checks_alternative_executables(monkeypatch):
    host = _host("windows", "Windows", is_windows=True)
    checked = []

    def which(command):
        checked.append(command)
        return "/usr/bin/py" if command == "py" else None

    monkeypatch.setattr(system_checks.shutil, "which", which)
    result = system_checks._check_required_tools(host=host)

    assert result == {"git": False, "python": True, "powershell": False}
    assert checked == ["git", "python", "py", "pwsh", "powershell"]


def test_linux_tool_checks_include_role_requirements_and_warn(monkeypatch, caplog):
    host = _host("linux", "Linux", is_linux=True)
    checked = []

    def which(command):
        checked.append(command)
        return "/usr/bin/" + command if command == "git" else None

    monkeypatch.setattr(system_checks.shutil, "which", which)
    result = system_checks._check_required_tools("pulse", host)

    assert result["git"] is True
    assert result["ethtool"] is False
    assert "ethtool" in checked
    assert "Required executable 'ethtool' not found" in caplog.text


def test_system_check_builds_platform_policy_for_non_linux_host(monkeypatch):
    host = _host("windows", "Windows 11", version="11", is_windows=True)
    monkeypatch.setattr(system_checks, "detect_host_platform", lambda: host)
    monkeypatch.setattr(system_checks, "check_os_support", lambda _host: True)
    monkeypatch.setattr(system_checks, "check_python_version", lambda: True)
    monkeypatch.setattr(
        system_checks,
        "_check_required_tools",
        lambda role, host: {"git": True, "python": False},
    )

    result = system_checks.system_check()

    assert result["os_supported"] is True
    assert result["kernel_supported"] is True
    assert result["kernel_policy"]["platform_specific"] is True
    assert result["kernel_policy"]["runtime_allowed"] is True
    assert result["tools_available"] is False
    assert result["python_available"] is False
