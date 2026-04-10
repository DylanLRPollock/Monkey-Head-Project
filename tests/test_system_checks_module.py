# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test System Checks Module module (tests)

"""Unit tests for :mod:`hueyos.system_checks`."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from hueyos import system_checks


def test_check_os_support_warns_for_legacy_windows(monkeypatch, caplog):
    monkeypatch.setattr(system_checks.platform, "system", lambda: "Windows")
    monkeypatch.setattr(system_checks.platform, "release", lambda: "6.1")

    with caplog.at_level(logging.WARNING):
        system_checks.check_os_support()

    assert "Unsupported Windows version" in caplog.text


def test_check_os_support_warns_for_non_debian_linux(monkeypatch, caplog):
    class FakeDistro:
        @staticmethod
        def id():
            return "ubuntu"

        @staticmethod
        def codename():
            return "noble"

    monkeypatch.setattr(system_checks.platform, "system", lambda: "Linux")
    monkeypatch.setattr(system_checks, "distro", FakeDistro())
    monkeypatch.setattr(system_checks.platform, "freedesktop_os_release", lambda: {})

    with caplog.at_level(logging.WARNING):
        system_checks.check_os_support()

    assert "Unsupported Linux distribution" in caplog.text


def test_check_python_version_warns_on_experimental_release(monkeypatch, caplog):
    class FakeInfo:
        major = 3
        minor = 15

    monkeypatch.setattr(system_checks.sys, "version_info", FakeInfo())

    with caplog.at_level(logging.WARNING):
        system_checks.check_python_version()

    assert "Python 3.15 detected" in caplog.text


def test_check_python_version_accepts_primary_target(monkeypatch, caplog):
    class FakeInfo:
        major = 3
        minor = 13

    monkeypatch.setattr(system_checks.sys, "version_info", FakeInfo())

    with caplog.at_level(logging.WARNING):
        system_checks.check_python_version()

    assert "Python 3.13" not in caplog.text


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
    def fake_os_check():
        return None

    monkeypatch.setattr(system_checks, "check_os_support", fake_os_check)
    monkeypatch.setattr(system_checks, "check_python_version", lambda: None)
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
