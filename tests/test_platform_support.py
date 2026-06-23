"""Tests for shared host-platform helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from huey.os.core import platform_support


@pytest.mark.parametrize(
    ("system", "sys_platform_name", "expected"),
    [
        ("Windows", "win32", "windows"),
        ("MSYS_NT-10.0-22631", "msys", "windows"),
        ("Darwin", "darwin", "macos"),
        ("macOS", "darwin", "macos"),
        ("Linux", "linux", "linux"),
    ],
)
def test_normalize_platform_family_recognizes_common_aliases(
    system: str,
    sys_platform_name: str,
    expected: str,
) -> None:
    assert (
        platform_support.normalize_platform_family(system, sys_platform_name) == expected
    )


@pytest.mark.parametrize(
    ("target", "expected_install", "expected_run"),
    [
        (
            "windows",
            Path("src/huey/platform/installers/windows/Windows/install-win.bat"),
            Path("src/huey/memory/BAT/run.bat"),
        ),
        (
            "macos",
            Path("src/huey/platform/installers/macos/macOS/install-mac.sh"),
            Path("src/huey/memory/SH/run.sh"),
        ),
        (
            "linux",
            Path("src/huey/platform/installers/debian/Debian/install-deb.sh"),
            Path("src/huey/memory/SH/run.sh"),
        ),
        (
            "debian",
            Path("src/huey/platform/installers/debian/Debian/install-deb.sh"),
            Path("src/huey/memory/SH/run.sh"),
        ),
    ],
)
def test_resolve_platform_script_paths_for_supported_targets(
    target: str,
    expected_install: Path,
    expected_run: Path,
) -> None:
    project_root = platform_support.find_project_root(Path(__file__).resolve())
    paths = platform_support.resolve_platform_script_paths(project_root, target=target)

    assert paths.project_root == project_root
    assert paths.install == project_root / expected_install
    assert paths.run == project_root / expected_run
    assert paths.install is not None and paths.install.exists()
    assert paths.run is not None and paths.run.exists()


def test_build_platform_script_command_prefers_powershell(monkeypatch) -> None:
    monkeypatch.setattr(
        platform_support.shutil,
        "which",
        lambda tool: "C:/Program Files/PowerShell/7/pwsh.exe"
        if tool == "pwsh"
        else None,
    )

    command = platform_support.build_platform_script_command(
        Path("C:/tmp/install-win.ps1"),
        ["--dry-run"],
    )

    assert command[:4] == [
        "C:/Program Files/PowerShell/7/pwsh.exe",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
    ]
    assert command[4] == str(Path("C:/tmp/install-win.ps1"))
    assert command[5:] == ["--dry-run"]
