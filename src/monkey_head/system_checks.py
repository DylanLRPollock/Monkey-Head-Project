"""System environment checks for the Monkey Head runtime."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import sys
from typing import Dict, Tuple

from packaging.version import InvalidVersion, Version

try:  # pragma: no cover - optional dependency on Linux only
    import distro  # type: ignore
except Exception:  # pragma: no cover - handled gracefully in tests
    distro = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

SUPPORTED_DISTRO_ID = "debian"
SUPPORTED_DISTRO_CODENAME = "trixie"
MIN_KERNEL_VERSION = Version("6.16.12")
MIN_PYTHON_VERSION = (3, 12)
MAX_PYTHON_VERSION = (3, 14)
REQUIRED_TOOLS: Tuple[str, ...] = ("git", "python3")

__all__ = [
    "logger",
    "ensure_admin",
    "check_os_support",
    "check_python_version",
    "system_check",
    "platform",
    "shutil",
    "sys",
    "distro",
]


def ensure_admin() -> None:
    """Raise :class:`PermissionError` when administrator privileges are missing."""

    if hasattr(os, "geteuid"):
        if os.geteuid() != 0:
            message = "Please run this script as root or with sudo."
            logger.error(message)
            raise PermissionError(message)
        return

    if os.name == "nt":  # pragma: no cover - Windows specific
        try:
            import ctypes

            if not ctypes.windll.shell32.IsUserAnAdmin():  # type: ignore[attr-defined]
                message = "Administrator privileges are required to continue."
                logger.error(message)
                raise PermissionError(message)
        except Exception:  # pragma: no cover - defensive fallback
            logger.debug(
                "Unable to determine administrator privileges on Windows.",
                exc_info=True,
            )


def _detect_linux_distribution() -> Tuple[str, str]:
    """Return a tuple of ``(distribution_id, codename)`` for Linux hosts."""

    dist_id = ""
    codename = ""

    if distro is not None:
        try:
            dist_id = str(distro.id() or "").strip().lower()
            codename = str(distro.codename() or "").strip().lower()
        except Exception:  # pragma: no cover - distro implementation details
            dist_id = ""
            codename = ""

    if not dist_id:
        release_info = {}
        if hasattr(platform, "freedesktop_os_release"):
            try:  # pragma: no cover - platform API may be unavailable
                release_info = platform.freedesktop_os_release()  # type: ignore[assignment]
            except Exception:
                release_info = {}
        dist_id = str(release_info.get("ID", "")).strip().lower()
        codename = str(release_info.get("VERSION_CODENAME", "")).strip().lower()

    return dist_id, codename


def check_os_support() -> bool:
    """Verify the host operating system matches the supported matrix."""

    system = platform.system()
    if system != "Linux":
        logger.warning("Unsupported operating system detected: %s", system or "unknown")
        return False

    dist_id, codename = _detect_linux_distribution()
    supported = (
        dist_id == SUPPORTED_DISTRO_ID and codename == SUPPORTED_DISTRO_CODENAME
    )

    if not supported:
        logger.warning(
            "Unsupported Linux distribution detected (%s %s). Debian Trixie is required.",
            dist_id or "unknown",
            codename or "unknown",
        )

    return supported


def _extract_kernel_version(raw_release: str) -> str:
    """Normalise the kernel release string for comparison."""

    version = raw_release.split("-")[0]
    version = version.split("+")[0]
    return version.strip()


def _check_kernel_version() -> bool:
    """Return ``True`` when the running kernel meets the minimum requirement."""

    release = platform.release()
    version_str = _extract_kernel_version(release)
    try:
        version = Version(version_str)
    except InvalidVersion:
        logger.warning("Unable to parse kernel version from release '%s'", release)
        return False

    if version < MIN_KERNEL_VERSION:
        logger.warning(
            "Kernel version %s is below the required minimum of %s.",
            version,
            MIN_KERNEL_VERSION,
        )
        return False

    return True


def check_python_version() -> bool:
    """Ensure the active Python interpreter falls within the supported range."""

    info = sys.version_info
    if isinstance(info, tuple):  # pragma: no cover - compatibility for patched tuples
        major, minor, micro = (info + (0, 0, 0))[:3]
    else:
        major = getattr(info, "major", 0)
        minor = getattr(info, "minor", 0)
        micro = getattr(info, "micro", 0)

    supported = (
        (major, minor) >= MIN_PYTHON_VERSION and (major, minor) < MAX_PYTHON_VERSION
    )

    if not supported:
        logger.warning(
            "Unsupported Python version detected (%s.%s.%s). Supported range is %s.%s to %s.x.",
            major,
            minor,
            micro,
            MIN_PYTHON_VERSION[0],
            MIN_PYTHON_VERSION[1],
            MAX_PYTHON_VERSION[1] - 1,
        )

    return supported


def _check_required_tools() -> Dict[str, bool]:
    """Return a mapping of required tool names to their availability."""

    results: Dict[str, bool] = {}
    for tool in REQUIRED_TOOLS:
        available = shutil.which(tool) is not None
        if not available:
            logger.warning("Required executable '%s' not found on PATH", tool)
        results[tool] = available
    return results


def system_check() -> Dict[str, bool]:
    """Run the suite of system checks and return their boolean results."""

    logger.info("Performing system checks...")
    results: Dict[str, bool] = {}

    results["os_supported"] = check_os_support()
    results["kernel_supported"] = _check_kernel_version()
    results["python_supported"] = check_python_version()

    tool_results = _check_required_tools()
    for name, status in tool_results.items():
        results[f"{name}_available"] = status
    results["tools_available"] = all(tool_results.values()) if tool_results else True

    return results

