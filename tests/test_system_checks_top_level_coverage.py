"""Cover less common runtime policy branches in the canonical system checks."""

from __future__ import annotations

import sys
from types import SimpleNamespace

from huey import system_checks


def test_kernel_release_helpers_handle_missing_and_partial_versions():
    assert system_checks._extract_kernel_role("6.18.2-hueyos-core+custom") == "core"
    assert system_checks._extract_kernel_role("6.18.2-generic") == ""
    assert system_checks._extract_kernel_role("6.18.2-hueyos-") == ""
    assert system_checks._parse_numeric_kernel_prefix("") == ()
    assert system_checks._parse_numeric_kernel_prefix("6.18.rc2") == (6, 18)


def test_kernel_policy_handles_empty_release_rc_unknown_role_and_stable_core(
    monkeypatch,
):
    monkeypatch.setattr(system_checks.platform, "release", lambda: "")
    assert system_checks.check_kernel_policy()["errors"]

    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "6.18.2-rc1-hueyos-custom",
    )
    rc = system_checks.check_kernel_policy()
    assert rc["is_release_candidate"] is True
    assert rc["lab_supported"] is False
    assert "outside accepted lab roles" in rc["errors"][0]

    monkeypatch.setattr(
        system_checks.platform,
        "release",
        lambda: "6.18.2-hueyos-core",
    )
    stable = system_checks.check_kernel_policy()
    assert stable["production_supported"] is True
    assert stable["runtime_allowed"] is True
    assert system_checks._check_kernel_version() is True


def test_free_threaded_detection_and_gil_probe_edges(monkeypatch):
    monkeypatch.setattr(sys, "version", "CPython free-threading build", raising=False)
    assert system_checks._is_free_threaded_build() is True
    monkeypatch.setattr(sys, "version", "CPython standard build", raising=False)
    monkeypatch.setattr(sys, "abiflags", "t", raising=False)
    assert system_checks._is_free_threaded_build() is True
    monkeypatch.setattr(sys, "abiflags", "", raising=False)
    assert system_checks._is_free_threaded_build() is False

    monkeypatch.setattr(sys, "_is_gil_enabled", lambda: False, raising=False)
    assert system_checks._python_gil_enabled() is False
    monkeypatch.setattr(sys, "_is_gil_enabled", lambda: True, raising=False)
    assert system_checks._python_gil_enabled() is True

    def unavailable():
        raise RuntimeError("probe unavailable")

    monkeypatch.setattr(sys, "_is_gil_enabled", unavailable, raising=False)
    assert system_checks._python_gil_enabled() is None


def test_gil_enabled_free_threaded_python_is_rejected(monkeypatch, caplog):
    monkeypatch.setattr(system_checks, "_is_free_threaded_build", lambda: True)
    monkeypatch.setattr(system_checks, "_python_gil_enabled", lambda: True)
    assert system_checks.check_python_version() is False
    assert "GIL re-enabled" in caplog.text


def test_required_tool_candidates_cover_macos_and_preserve_order():
    macos = SimpleNamespace(is_windows=False, is_macos=True)
    assert system_checks._required_tool_candidates(macos, "core") == (
        ("git", ("git",)),
        ("python3", ("python3",)),
        ("bash", ("bash",)),
        ("pmset", ("pmset",)),
        ("networksetup", ("networksetup",)),
    )
    assert (
        system_checks._required_tools_for_role(" unknown ")
        == system_checks.BASE_REQUIRED_TOOLS
    )


def test_required_tool_check_accepts_any_platform_candidate(monkeypatch):
    host = SimpleNamespace(is_windows=True, is_macos=False)
    monkeypatch.setattr(
        system_checks.shutil,
        "which",
        lambda command: "/bin/py" if command == "py" else None,
    )
    assert system_checks._check_required_tools(host=host) == {
        "git": False,
        "python": True,
        "powershell": False,
    }
