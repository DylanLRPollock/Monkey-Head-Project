"""Shared host-platform detection and script path helpers for HueyOS."""

from __future__ import annotations

from dataclasses import dataclass
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Literal, Sequence

PlatformFamily = Literal["windows", "macos", "linux", "unknown"]

_DISPLAY_NAMES: dict[PlatformFamily, str] = {
    "windows": "Windows",
    "macos": "macOS",
    "linux": "Linux",
    "unknown": "Unknown",
}


@dataclass(frozen=True, slots=True)
class HostPlatform:
    """Normalized description of the current host platform."""

    family: PlatformFamily
    system: str
    release: str
    version: str
    machine: str
    sys_platform: str
    display_name: str
    is_windows: bool
    is_macos: bool
    is_linux: bool
    is_unknown: bool
    is_wsl: bool


@dataclass(frozen=True, slots=True)
class PlatformScriptPaths:
    """Repository paths for the current host platform's launch scripts."""

    host: HostPlatform
    project_root: Path
    installers_root: Path
    memory_root: Path
    install: Path | None
    update: Path | None
    uninstall: Path | None
    run: Path | None


def _tokenize_platform_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def normalize_platform_family(
    system: str = "",
    sys_platform_name: str | None = None,
) -> PlatformFamily:
    """Collapse platform aliases into ``windows``, ``macos``, ``linux``, or ``unknown``."""

    candidates = [system]
    if sys_platform_name is not None:
        candidates.append(sys_platform_name)
    else:
        candidates.append(sys.platform)

    for candidate in candidates:
        token = _tokenize_platform_name(candidate)
        if token.startswith(("windows", "win32", "msys", "cygwin", "mingw")):
            return "windows"
        if token.startswith(("darwin", "macos", "macosx", "osx")):
            return "macos"
        if token.startswith("linux"):
            return "linux"
    return "unknown"


def _read_text_if_present(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def detect_host_platform() -> HostPlatform:
    """Return a normalized description of the active host platform."""

    system = str(platform.system() or "").strip()
    release = str(platform.release() or "").strip()
    version = str(platform.version() or "").strip()
    machine = str(platform.machine() or "").strip()
    sys_platform_name = str(sys.platform or "").strip()
    family = normalize_platform_family(system, sys_platform_name)
    display_name = _DISPLAY_NAMES[family]

    if not system:
        system = display_name

    wsl_markers = " ".join(
        part
        for part in (
            release,
            version,
            _read_text_if_present(Path("/proc/sys/kernel/osrelease")),
            _read_text_if_present(Path("/proc/version")),
        )
        if part
    ).casefold()

    return HostPlatform(
        family=family,
        system=system,
        release=release,
        version=version,
        machine=machine,
        sys_platform=sys_platform_name,
        display_name=display_name,
        is_windows=family == "windows",
        is_macos=family == "macos",
        is_linux=family == "linux",
        is_unknown=family == "unknown",
        is_wsl=family == "linux" and "microsoft" in wsl_markers,
    )


def find_project_root(start: Path | None = None) -> Path:
    """Locate the repository root by walking upward to ``pyproject.toml``."""

    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate

    raise RuntimeError(f"Unable to locate the project root from {current}")


def _host_platform_from_target(target: str) -> HostPlatform:
    token = _tokenize_platform_name(target)
    family: PlatformFamily
    if token == "debian":
        family = "linux"
    else:
        family = normalize_platform_family(target)

    display_name = _DISPLAY_NAMES[family]
    system = target.strip() or display_name
    if family != "unknown":
        system = display_name

    return HostPlatform(
        family=family,
        system=system,
        release="",
        version="",
        machine="",
        sys_platform="",
        display_name=display_name,
        is_windows=family == "windows",
        is_macos=family == "macos",
        is_linux=family == "linux",
        is_unknown=family == "unknown",
        is_wsl=False,
    )


def resolve_platform_script_paths(
    project_root: Path | None = None,
    *,
    target: str | None = None,
) -> PlatformScriptPaths:
    """Resolve installer, updater, uninstaller, and run-script paths by platform."""

    root = find_project_root(project_root)
    host = _host_platform_from_target(target) if target is not None else detect_host_platform()

    installers_root = root / "src" / "huey" / "platform" / "installers"
    memory_root = root / "src" / "huey" / "memory"

    install = update = uninstall = run = None
    if host.is_windows:
        installer_dir = installers_root / "windows" / "Windows"
        install = installer_dir / "install-win.bat"
        update = installer_dir / "update-win.bat"
        uninstall = installer_dir / "uninstall-win.bat"
        run = memory_root / "BAT" / "run.bat"
    elif host.is_macos:
        installer_dir = installers_root / "macos" / "macOS"
        install = installer_dir / "install-mac.sh"
        update = installer_dir / "update-mac.sh"
        uninstall = installer_dir / "uninstall-mac.sh"
        run = memory_root / "SH" / "run.sh"
    elif host.is_linux:
        installer_dir = installers_root / "debian" / "Debian"
        install = installer_dir / "install-deb.sh"
        update = installer_dir / "update-deb.sh"
        uninstall = installer_dir / "uninstall-deb.sh"
        run = memory_root / "SH" / "run.sh"

    return PlatformScriptPaths(
        host=host,
        project_root=root,
        installers_root=installers_root,
        memory_root=memory_root,
        install=install,
        update=update,
        uninstall=uninstall,
        run=run,
    )


def build_platform_script_command(
    script_path: Path,
    passthrough: Sequence[str] | None = None,
) -> list[str]:
    """Build a non-interactive command line for a platform-specific script."""

    extra_args = list(passthrough or ())
    suffix = script_path.suffix.casefold()
    if suffix == ".ps1":
        powershell = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
        return [
            powershell,
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            *extra_args,
        ]
    if suffix == ".bat":
        return ["cmd", "/c", str(script_path), *extra_args]
    return ["bash", str(script_path), *extra_args]


__all__ = [
    "HostPlatform",
    "PlatformFamily",
    "PlatformScriptPaths",
    "build_platform_script_command",
    "detect_host_platform",
    "find_project_root",
    "normalize_platform_family",
    "resolve_platform_script_paths",
]
