# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test System Checks Module module (tests)

"""Unit tests for :mod:`huey.os.system_checks`."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from huey.os.core.platform_support import HostPlatform
from huey.os import system_checks


def _host(
    *,
    family: str,
    system: str,
    release: str = "",
    version: str = "",
    distribution_id: str = "",
    distribution_codename: str = "",
    distribution_like: tuple[str, ...] = (),
    is_wsl: bool = False,
) -> HostPlatform:
    display_name = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}.get(
        family, system
    )
    return HostPlatform(
        family=family,  # type: ignore[arg-type]
        system=system,
        release=release,
        version=version,
        machine="x86_64",
        sys_platform=family,
        display_name=display_name,
        is_windows=family == "windows",
        is_macos=family == "macos",
        is_linux=family == "linux",
        is_unknown=family == "unknown",
        is_wsl=is_wsl,
        distribution_id=distribution_id,
        distribution_codename=distribution_codename,
        distribution_like=distribution_like,
    )


def test_check_os_support_accepts_supported_windows_release(monkeypatch, caplog):
    monkeypatch.setattr(
        system_checks,
        "detect_host_platform",
        lambda: _host(family="windows", system="Windows", release="10"),
    )

    with caplog.at_level(logging.WARNING):
        supported = system_checks.check_os_support()

    assert supported is True
    assert "Unsupported Windows version" not in caplog.text


def test_check_os_support_warns_for_legacy_windows(monkeypatch, caplog):
    monkeypatch.setattr(
        system_checks,
        "detect_host_platform",
        lambda: _host(family="windows", system="Windows", release="6.1"),
    )

    with caplog.at_level(logging.WARNING):
        supported = system_checks.check_os_support()

    assert supported is False
    assert "Unsupported Windows version" in caplog.text


def test_check_os_support_accepts_supported_macos_version(monkeypatch, caplog):
    monkeypatch.setattr(
        system_checks,
        "detect_host_platform",
        lambda: _host(family="macos", system="Darwin"),
    )
    monkeypatch.setattr(
        system_checks.platform,
        "mac_ver",
        lambda: ("13.5", ("", "", ""), ""),
    )

    with caplog.at_level(logging.WARNING):
        supported = system_checks.check_os_support()

    assert supported is True
    assert "Unsupported macOS version" not in caplog.text

def test_check_os_support_warns_for_non_debian_linux(monkeypatch, caplog):
    monkeypatch.setattr(
        system_checks,
        "detect_host_platform",
        lambda: _host(
            family="linux",
            system="Linux",
            distribution_id="ubuntu",
            distribution_codename="noble",
        ),
    )

    with caplog.at_level(logging.WARNING):
        system_checks.check_os_support()

    assert "Unsupported Linux distribution" in caplog.text


def test_check_python_version_warns_on_testing_lane(monkeypatch, caplog):
    class FakeInfo:
        major = 3
        minor = 14

    monkeypatch.setattr(system_checks.sys, "version_info", FakeInfo())

    with caplog.at_level(logging.WARNING):
        system_checks.check_python_version()

    assert "testing-only compatibility lane" in caplog.text


def test_check_python_version_accepts_primary_target(monkeypatch, caplog):
    class FakeInfo:
        major = 3
        minor = 13

    monkeypatch.setattr(system_checks.sys, "version_info", FakeInfo())

    with caplog.at_level(logging.WARNING):
        system_checks.check_python_version()

    assert "Python 3.13" not in caplog.text


def test_check_python_version_rejects_free_threaded_build(monkeypatch, caplog):
    class FakeInfo:
        major = 3
        minor = 13

    monkeypatch.setattr(system_checks.sys, "version_info", FakeInfo())
    monkeypatch.setattr(system_checks, "_is_free_threaded_build", lambda: True)
    monkeypatch.setattr(system_checks, "_python_gil_enabled", lambda: False)

    with caplog.at_level(logging.WARNING):
        supported = system_checks.check_python_version()

    assert supported is False
    assert "free-threaded Python 3.13 build" in caplog.text


def test_check_kernel_naming_accepts_hueyos_family_role(monkeypatch, caplog):
    monkeypatch.setattr(system_checks.platform, "release", lambda: "6.18.2-hueyos-core")

    with caplog.at_level(logging.WARNING):
        supported = system_checks._check_kernel_naming()

    assert supported is True
    assert "Kernel release" not in caplog.text


def test_check_kernel_naming_rejects_non_hueyos_suffix(monkeypatch, caplog):
    monkeypatch.setattr(system_checks.platform, "release", lambda: "6.18.2-generic")

    with caplog.at_level(logging.WARNING):
        supported = system_checks._check_kernel_naming()

    assert supported is False
    assert "family/role suffix" in caplog.text


def test_check_kernel_naming_accepts_lab_rc_kernel(monkeypatch, caplog):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "7.0.0-rc7-hueyos-lab",
    )

    with caplog.at_level(logging.INFO):
        supported = system_checks._check_kernel_naming()

    assert supported is True
    assert "Detected explicit HueyOS hueyos kernel role 'lab'" in caplog.text


def test_check_kernel_naming_rejects_rc_kernel_for_non_lab_roles(monkeypatch, caplog):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "7.0.0-rc7-hueyos-core",
    )

    with caplog.at_level(logging.WARNING):
        supported = system_checks._check_kernel_naming()

    assert supported is False


def test_check_kernel_policy_supports_rc_in_lab_mode(monkeypatch):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "7.0.0-rc7-hueyos-core",
    )

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is False
    assert result["lab_supported"] is True
    assert result["is_release_candidate"] is True
    assert result["detected_family"] == system_checks.SUPPORTED_KERNEL_FAMILY
    assert result["detected_role"] == "core"
    assert result["version_prefix"] == (7, 0, 0)
    assert result["is_lab_kernel"] is False
    assert result["runtime_policy"] == system_checks.DEFAULT_RUNTIME_POLICY
    assert result["runtime_allowed"] is False


def test_check_kernel_policy_accepts_pulse_in_both_modes(monkeypatch):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "6.18.2-hueyos-pulse",
    )

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is True
    assert result["lab_supported"] is True
    assert result["runtime_allowed"] is True


def test_check_kernel_policy_accepts_lab_role_for_lab_mode(monkeypatch):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "6.18.2-hueyos-lab",
    )

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is False
    assert result["lab_supported"] is True
    assert result["is_lab_kernel"] is True


@pytest.mark.parametrize(
    ("release", "expected_role"),
    [
        ("7.0.0-hueyos-core", "core"),
        ("7.0.0-hueyos-pulse", "pulse"),
    ],
)
def test_check_kernel_policy_accepts_stable_production_kernel_roles(
    monkeypatch, release, expected_role
):
    monkeypatch.setattr(system_checks.platform, "release", lambda: release)

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is True
    assert result["lab_supported"] is True
    assert result["runtime_allowed"] is True
    assert result["detected_role"] == expected_role
    assert result["errors"] == []


def test_check_kernel_policy_accepts_rc_lab_kernel(monkeypatch):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "7.0.0-rc7-hueyos-lab",
    )

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is False
    assert result["lab_supported"] is True
    assert result["is_release_candidate"] is True
    assert result["runtime_allowed"] is False
    assert result["detected_role"] == "lab"
    assert result["errors"] == []


def test_check_kernel_policy_rejects_missing_family_suffix(monkeypatch):
    monkeypatch.setattr(system_checks.platform, "release", lambda: "7.0.0")

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is False
    assert result["lab_supported"] is False
    assert result["family_role_present"] is False
    assert "missing the 'hueyos-<role>' family/role suffix" in result["errors"][0]


@pytest.mark.parametrize(
    "release",
    [
        "7.0.0-hueyos--core",
        "7.0.0-hueyos-core$",
    ],
)
def test_check_kernel_policy_rejects_malformed_role_segment(monkeypatch, release):
    monkeypatch.setattr(system_checks.platform, "release", lambda: release)

    result = system_checks.check_kernel_policy()

    assert result["production_supported"] is False
    assert result["lab_supported"] is False
    assert result["role_valid"] is False
    assert "invalid HueyOS role segment" in result["errors"][0]


def test_check_kernel_policy_disallows_rc_build_for_production_mode(monkeypatch):
    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "7.0.0-rc7-hueyos-core",
    )

    result = system_checks.check_kernel_policy()

    assert result["is_release_candidate"] is True
    assert result["production_supported"] is False
    assert result["runtime_policy"] == "production"
    assert result["runtime_allowed"] is False
    assert result["lab_supported"] is True


def test_system_check_collects_expected_results(monkeypatch):
    def fake_os_check(_host=None):
        return True

    monkeypatch.setattr(
        system_checks,
        "detect_host_platform",
        lambda: _host(family="linux", system="Linux"),
    )
    monkeypatch.setattr(system_checks, "check_os_support", fake_os_check)
    monkeypatch.setattr(system_checks, "check_python_version", lambda: True)
    monkeypatch.setattr(
        system_checks,
        "check_kernel_policy",
        lambda: {
            "production_supported": True,
            "lab_supported": True,
            "errors": [],
        },
    )
    monkeypatch.setattr(
        system_checks.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(free=5 * 1024**3),
    )
    monkeypatch.setattr(system_checks.shutil, "which", lambda tool: f"/usr/bin/{tool}")

    results = system_checks.system_check()

    assert results["os_supported"] is True
    assert results["python_supported"] is True
    assert results["kernel_supported"] is True
    assert results["kernel_policy"]["lab_supported"] is True
    assert results["git_available"] is True
    assert results["python3_available"] is True


def test_system_check_uses_windows_tool_requirements(monkeypatch):
    monkeypatch.setattr(
        system_checks,
        "detect_host_platform",
        lambda: _host(family="windows", system="Windows"),
    )
    monkeypatch.setattr(system_checks, "check_os_support", lambda _host=None: True)
    monkeypatch.setattr(system_checks, "check_python_version", lambda: True)
    monkeypatch.setattr(
        system_checks,
        "check_kernel_policy",
        lambda: pytest.fail("Windows system checks should not use Linux kernel policy"),
    )
    monkeypatch.setattr(
        system_checks.shutil,
        "which",
        lambda tool: f"C:/Tools/{tool}.exe"
        if tool in {"git", "python", "pwsh"}
        else None,
    )

    results = system_checks.system_check()

    assert results["os_supported"] is True
    assert results["kernel_supported"] is True
    assert results["git_available"] is True
    assert results["python_available"] is True
    assert results["powershell_available"] is True


def test_required_tools_for_pulse_role_includes_pavucontrol() -> None:
    tools = system_checks._required_tools_for_role("pulse")

    assert "pavucontrol" in tools
