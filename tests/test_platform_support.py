"""Tests for shared host-platform helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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
        platform_support.normalize_platform_family(system, sys_platform_name)
        == expected
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
        lambda tool: (
            "C:/Program Files/PowerShell/7/pwsh.exe" if tool == "pwsh" else None
        ),
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


def test_read_os_release_falls_back_to_quoted_file_values(monkeypatch):
    class ReleasePath:
        def __init__(self, _path):
            pass

        def exists(self):
            return True

        def read_text(self, *, encoding):
            assert encoding == "utf-8"
            return 'ID="TestOS"\\nVERSION_CODENAME=stable\\nID_LIKE="Debian Ubuntu"\\ninvalid'

    def unavailable():
        raise OSError("platform release helper unavailable")

    monkeypatch.setattr(platform_support.platform, "freedesktop_os_release", unavailable)
    monkeypatch.setattr(platform_support, "Path", ReleasePath)

    assert platform_support._read_os_release() == {
        "ID": "TestOS",
        "VERSION_CODENAME": "stable",
        "ID_LIKE": "Debian Ubuntu",
    }


def test_linux_distribution_details_use_fallback_and_normalize_id_like(monkeypatch):
    monkeypatch.setattr(
        platform_support,
        "distro",
        SimpleNamespace(id=lambda: "  ", codename=lambda: ""),
    )
    monkeypatch.setattr(
        platform_support,
        "_read_os_release",
        lambda: {
            "ID": " Ubuntu ",
            "VERSION_CODENAME": " Noble ",
            "ID_LIKE": "Debian  ubuntu ",
        },
    )

    assert platform_support._read_linux_distribution_details() == (
        "ubuntu",
        "noble",
        ("debian", "ubuntu"),
    )


def test_detect_host_platform_normalizes_empty_system_and_wsl_markers(monkeypatch):
    monkeypatch.setattr(platform_support.platform, "system", lambda: "")
    monkeypatch.setattr(platform_support.platform, "release", lambda: "5.15")
    monkeypatch.setattr(platform_support.platform, "version", lambda: "")
    monkeypatch.setattr(platform_support.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(platform_support.sys, "platform", "linux")
    monkeypatch.setattr(
        platform_support, "_read_text_if_present", lambda _path: "Microsoft"
    )
    monkeypatch.setattr(
        platform_support,
        "_read_linux_distribution_details",
        lambda: ("debian", "bookworm", ("debian",)),
    )

    host = platform_support.detect_host_platform()

    assert host.family == "linux"
    assert host.system == "Linux"
    assert host.is_linux is True
    assert host.is_wsl is True
    assert host.installer_target == "debian"


def test_detect_unknown_host_does_not_read_distribution(monkeypatch):
    monkeypatch.setattr(platform_support.platform, "system", lambda: "Plan9")
    monkeypatch.setattr(platform_support.platform, "release", lambda: "")
    monkeypatch.setattr(platform_support.platform, "version", lambda: "")
    monkeypatch.setattr(platform_support.platform, "machine", lambda: "")
    monkeypatch.setattr(platform_support.sys, "platform", "plan9")
    monkeypatch.setattr(
        platform_support,
        "_read_linux_distribution_details",
        lambda: pytest.fail("non-Linux host must not read distribution details"),
    )

    host = platform_support.detect_host_platform()

    assert host.family == "unknown"
    assert host.is_unknown is True
    assert host.is_posix is False
    assert host.installer_target == "unknown"


def test_find_project_root_reports_missing_project_marker(tmp_path: Path):
    start = tmp_path / "nested" / "file.py"
    start.parent.mkdir()
    start.write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Unable to locate the project root"):
        platform_support.find_project_root(start)


def test_unknown_target_has_no_scripts_and_script_lookup_is_validated(
    tmp_path: Path,
):
    paths = platform_support.resolve_platform_script_paths(
        platform_support.find_project_root(Path(__file__).resolve()),
        target="plan9",
    )

    assert paths.install is None
    assert paths.update is None
    assert paths.uninstall is None
    assert paths.run is None
    assert paths.command_for("install") is None
    with pytest.raises(ValueError, match="Unsupported platform script action"):
        paths.script_for("shutdown")


def test_script_command_builders_cover_shell_and_powershell_fallbacks(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(platform_support.shutil, "which", lambda _tool: None)
    powershell_script = tmp_path / "setup.ps1"
    assert platform_support.build_platform_script_command(powershell_script) == [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(powershell_script),
    ]
    assert platform_support.build_platform_script_command(tmp_path / "run.bat") == [
        "cmd",
        "/c",
        str(tmp_path / "run.bat"),
    ]
    assert platform_support.build_platform_script_command(tmp_path / "run.sh") == [
        "bash",
        str(tmp_path / "run.sh"),
    ]
    assert platform_support.build_platform_script_command(tmp_path / "custom") == [
        str(tmp_path / "custom")
    ]


def test_require_admin_privileges_checks_posix_and_windows(monkeypatch):
    monkeypatch.setattr(platform_support.os, "geteuid", lambda: 0)
    platform_support.require_admin_privileges(host=_host(family="linux", system="Linux"))
    monkeypatch.setattr(platform_support.os, "geteuid", lambda: 1000)
    with pytest.raises(PermissionError, match="root or with sudo"):
        platform_support.require_admin_privileges(
            host=_host(family="linux", system="Linux")
        )

    admin_check = SimpleNamespace(IsUserAnAdmin=lambda: True)
    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: True))
    )
    monkeypatch.setitem(__import__("sys").modules, "ctypes", fake_ctypes)
    platform_support.require_admin_privileges(
        host=_host(family="windows", system="Windows")
    )

    fake_ctypes.windll.shell32.IsUserAnAdmin = lambda: False
    with pytest.raises(
        PermissionError,
        match="Administrator privileges are required",
    ):
        platform_support.require_admin_privileges(
            host=_host(family="windows", system="Windows")
        )
