"""Tests for shared host-platform helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from huey.os.core import platform_support


def _host(
    *,
    family: str,
    system: str,
    distribution_id: str = "",
    distribution_like: tuple[str, ...] = (),
    is_wsl: bool = False,
) -> platform_support.HostPlatform:
    display_name = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}.get(
        family, system
    )
    return platform_support.HostPlatform(
        family=family,  # type: ignore[arg-type]
        system=system,
        release="",
        version="",
        machine="x86_64",
        sys_platform=family,
        display_name=display_name,
        is_windows=family == "windows",
        is_macos=family == "macos",
        is_linux=family == "linux",
        is_unknown=family == "unknown",
        is_wsl=is_wsl,
        distribution_id=distribution_id,
        distribution_codename="",
        distribution_like=distribution_like,
    )


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
    ("target", "expected"),
    [
        ("windows", "windows"),
        ("macos", "macos"),
        ("linux", "linux"),
        ("debian", "debian"),
        ("MSYS_NT-10.0", "windows"),
    ],
)
def test_normalize_installer_target_recognizes_supported_targets(
    target: str,
    expected: str,
) -> None:
    assert platform_support.normalize_installer_target(target) == expected


@pytest.mark.parametrize(
    ("target", "expected_install", "expected_run"),
    [
        (
            "windows",
            Path("src/huey/platform/installers/windows/Windows/install-win.ps1"),
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


def test_host_platform_installer_target_and_runtime_name() -> None:
    linux_host = _host(
        family="linux",
        system="Linux",
        distribution_id="debian",
        distribution_like=("debian",),
        is_wsl=True,
    )
    windows_host = _host(family="windows", system="Windows")

    assert linux_host.installer_target == "debian"
    assert linux_host.runtime_display_name == "Linux (WSL)"
    assert windows_host.installer_target == "windows"
    assert windows_host.shell_split_posix is False


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


def test_build_platform_script_command_falls_back_to_batch_when_needed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    script_path = tmp_path / "install-win.ps1"
    batch_path = tmp_path / "install-win.bat"
    script_path.write_text("Write-Host test", encoding="utf-8")
    batch_path.write_text("@echo off\r\necho test\r\n", encoding="utf-8")

    monkeypatch.setattr(platform_support.shutil, "which", lambda tool: None)

    command = platform_support.build_platform_script_command(
        script_path,
        ["--quiet"],
    )

    assert command == ["cmd", "/c", str(batch_path), "--quiet"]


def test_split_command_line_uses_platform_appropriate_rules() -> None:
    windows_parts = platform_support.split_command_line(
        'python -c "print(1)"',
        host=_host(family="windows", system="Windows"),
    )
    posix_parts = platform_support.split_command_line(
        'python -c "print(1)"',
        host=_host(family="linux", system="Linux"),
    )

    assert windows_parts == ["python", "-c", "print(1)"]
    assert posix_parts == ["python", "-c", "print(1)"]
