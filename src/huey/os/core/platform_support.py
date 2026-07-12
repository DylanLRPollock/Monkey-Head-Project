"""Shared host-platform detection and script path helpers for HueyOS."""

from __future__ import annotations

from dataclasses import dataclass
import os
import platform
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Literal, Sequence

try:  # pragma: no cover - optional dependency
    import distro  # type: ignore
except Exception:  # pragma: no cover - handled gracefully by helpers
    distro = None  # type: ignore[assignment]


PlatformFamily = Literal["windows", "macos", "linux", "unknown"]
InstallerTarget = Literal["windows", "macos", "debian", "linux", "unknown"]

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
    distribution_id: str = ""
    distribution_codename: str = ""
    distribution_like: tuple[str, ...] = ()

    @property
    def is_posix(self) -> bool:
        return self.is_macos or self.is_linux

    @property
    def shell_split_posix(self) -> bool:
        return not self.is_windows

    @property
    def is_debian_like(self) -> bool:
        return self.distribution_id == "debian" or "debian" in self.distribution_like

    @property
    def runtime_display_name(self) -> str:
        if self.is_wsl:
            return f"{self.display_name} (WSL)"
        return self.display_name

    @property
    def installer_target(self) -> InstallerTarget:
        if self.is_windows:
            return "windows"
        if self.is_macos:
            return "macos"
        if self.is_linux:
            return "debian" if self.is_debian_like else "linux"
        return "unknown"


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

    def script_for(self, action: str) -> Path | None:
        if action == "install":
            return self.install
        if action == "update":
            return self.update
        if action == "uninstall":
            return self.uninstall
        if action == "run":
            return self.run
        raise ValueError(f"Unsupported platform script action: {action}")

    def command_for(
        self,
        action: str,
        passthrough: Sequence[str] | None = None,
    ) -> list[str] | None:
        script_path = self.script_for(action)
        if script_path is None:
            return None
        return build_platform_script_command(script_path, passthrough)


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


def normalize_installer_target(
    target: str = "",
    sys_platform_name: str | None = None,
) -> InstallerTarget:
    """Normalize installer target names used by CLI and script resolution."""

    token = _tokenize_platform_name(target)
    if token == "debian":
        return "debian"

    family = normalize_platform_family(target, sys_platform_name)
    if family == "windows":
        return "windows"
    if family == "macos":
        return "macos"
    if family == "linux":
        return "linux"
    return "unknown"


def _read_text_if_present(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _strip_surrounding_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _read_os_release() -> dict[str, str]:
    release_info: dict[str, str] = {}

    if hasattr(platform, "freedesktop_os_release"):
        try:  # pragma: no cover - depends on interpreter/platform support
            release_info = {
                str(key): str(value)
                for key, value in platform.freedesktop_os_release().items()
            }
        except Exception:
            release_info = {}

    if release_info:
        return release_info

    os_release_path = Path("/etc/os-release")
    if not os_release_path.exists():
        return release_info

    for line in os_release_path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        release_info[key.strip()] = value.strip().strip('"')

    return release_info


def _read_linux_distribution_details() -> tuple[str, str, tuple[str, ...]]:
    dist_id = ""
    codename = ""

    if distro is not None:
        try:
            dist_id = str(distro.id() or "").strip().lower()
            codename = str(distro.codename() or "").strip().lower()
        except Exception:  # pragma: no cover - distro implementation details
            dist_id = ""
            codename = ""

    release_info = _read_os_release()
    if not dist_id:
        dist_id = str(release_info.get("ID", "")).strip().lower()
    if not codename:
        codename = str(release_info.get("VERSION_CODENAME", "")).strip().lower()

    id_like = tuple(
        item.strip().lower()
        for item in str(release_info.get("ID_LIKE", "")).split()
        if item.strip()
    )
    return dist_id, codename, id_like


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

    distribution_id = ""
    distribution_codename = ""
    distribution_like: tuple[str, ...] = ()
    if family == "linux":
        (
            distribution_id,
            distribution_codename,
            distribution_like,
        ) = _read_linux_distribution_details()

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
        distribution_id=distribution_id,
        distribution_codename=distribution_codename,
        distribution_like=distribution_like,
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
    normalized_target = normalize_installer_target(target)
    if normalized_target in {"debian", "linux"}:
        family: PlatformFamily = "linux"
    elif normalized_target in {"windows", "macos"}:
        family = normalized_target
    else:
        family = "unknown"

    display_name = _DISPLAY_NAMES[family]
    system = display_name if family != "unknown" else (target.strip() or display_name)
    distribution_id = "debian" if normalized_target == "debian" else ""

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
        distribution_id=distribution_id,
        distribution_codename="",
        distribution_like=("debian",) if distribution_id == "debian" else (),
    )


def _preferred_path(*candidates: Path) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def resolve_platform_script_paths(
    project_root: Path | None = None,
    *,
    target: str | None = None,
) -> PlatformScriptPaths:
    """Resolve installer, updater, uninstaller, and run-script paths by platform."""

    root = find_project_root(project_root)
    host = (
        _host_platform_from_target(target)
        if target is not None
        else detect_host_platform()
    )

    installers_root = root / "src" / "huey" / "platform" / "installers"
    memory_root = root / "src" / "huey" / "memory"

    install = update = uninstall = run = None
    if host.is_windows:
        installer_dir = installers_root / "windows" / "Windows"
        install = _preferred_path(
            installer_dir / "install-win.ps1",
            installer_dir / "install-win.bat",
        )
        update = _preferred_path(
            installer_dir / "update-win.ps1",
            installer_dir / "update-win.bat",
        )
        uninstall = _preferred_path(
            installer_dir / "uninstall-win.ps1",
            installer_dir / "uninstall-win.bat",
        )
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
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            return [
                powershell,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                *extra_args,
            ]
        batch_fallback = script_path.with_suffix(".bat")
        if batch_fallback.exists():
            return ["cmd", "/c", str(batch_fallback), *extra_args]
        return [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            *extra_args,
        ]
    if suffix == ".bat":
        return ["cmd", "/c", str(script_path), *extra_args]
    if suffix == ".sh":
        return ["bash", str(script_path), *extra_args]
    return [str(script_path), *extra_args]


def split_command_line(
    command_line: str,
    host: HostPlatform | None = None,
) -> list[str]:
    """Split a user-provided command line using platform-appropriate quoting."""

    text = command_line.strip()
    if not text:
        return []
    host = host or detect_host_platform()
    parts = shlex.split(text, posix=host.shell_split_posix)
    if host.is_windows:
        return [_strip_surrounding_quotes(part) for part in parts]
    return parts


def require_admin_privileges(
    host: HostPlatform | None = None,
    *,
    posix_message: str = "Please run this script as root or with sudo.",
    windows_message: str = "Administrator privileges are required to continue.",
) -> None:
    """Raise :class:`PermissionError` when elevated privileges are missing."""

    host = host or detect_host_platform()
    if host.is_windows:
        try:
            import ctypes

            if ctypes.windll.shell32.IsUserAnAdmin():  # type: ignore[attr-defined]
                return
        except Exception as exc:  # pragma: no cover - interpreter/environment specific
            raise PermissionError(windows_message) from exc
        raise PermissionError(windows_message)

    geteuid = getattr(os, "geteuid", None)
    if callable(geteuid) and geteuid() == 0:
        return
    raise PermissionError(posix_message)


__all__ = [
    "HostPlatform",
    "InstallerTarget",
    "PlatformFamily",
    "PlatformScriptPaths",
    "build_platform_script_command",
    "detect_host_platform",
    "distro",
    "find_project_root",
    "normalize_installer_target",
    "normalize_platform_family",
    "require_admin_privileges",
    "resolve_platform_script_paths",
    "split_command_line",
]
