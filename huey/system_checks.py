# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: System Checks module (huey)

"""System environment checks for the Monkey Head compatibility layer."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import sys
from typing import Dict

try:  # pragma: no cover - optional dependency
    import distro  # type: ignore
except Exception:  # pragma: no cover - handled gracefully in tests
    distro = None  # type: ignore[assignment]

from .logging_setup import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

__all__ = [
    "logger",
    "ensure_admin",
    "check_os_support",
    "check_python_version",
    "system_check",
]

_SUPPORTED_LINUX_CODENAMES = {"trixie", "testing"}


def ensure_admin() -> None:
    """Ensure the current process has administrative privileges."""

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
        except Exception:  # pragma: no cover - safety net
            logger.debug(
                "Unable to determine administrator privileges on Windows.",
                exc_info=True,
            )
        return

    logger.debug("Skipping administrator privilege check on platform %s", os.name)


def check_os_support() -> None:
    """Warn when the operating system is outside the supported matrix."""

    system = platform.system()
    if system == "Windows":
        release = platform.release()
        try:
            major = int(str(release).split(".")[0])
        except ValueError:
            major = 0
        if major < 10:
            logger.warning(
                "Unsupported Windows version detected (%s). Windows 10 or newer is required.",
                release,
            )
    elif system == "Darwin":
        version, _, _ = platform.mac_ver()
        try:
            major = int(str(version).split(".")[0])
        except ValueError:
            major = 0
        if major < 13:
            logger.warning(
                "Unsupported macOS version detected (%s). macOS Ventura or newer is required.",
                version,
            )
    elif system == "Linux":
        dist_id = ""
        codename = ""
        if distro is not None:
            try:
                dist_id = str(distro.id() or "").lower()
                codename = str(distro.codename() or "").lower()
            except Exception:  # pragma: no cover - distro implementation detail
                dist_id = ""
                codename = ""
        if not dist_id:
            release_info: Dict[str, str] = {}
            if hasattr(platform, "freedesktop_os_release"):
                try:
                    release_info = platform.freedesktop_os_release()  # type: ignore[assignment]
                except Exception:  # pragma: no cover - platform API not available
                    release_info = {}
            dist_id = str(release_info.get("ID", "")).lower()
            codename = str(release_info.get("VERSION_CODENAME", "")).lower()
        if dist_id != "debian" or codename not in _SUPPORTED_LINUX_CODENAMES:
            logger.warning(
                "Unsupported Linux distribution detected (%s %s). Debian Trixie/testing is required.",
                dist_id,
                codename,
            )
    else:
        logger.warning("Unsupported operating system detected: %s", system)


def check_python_version() -> None:
    """Warn when running on experimental Python versions."""

    info = sys.version_info
    if isinstance(info, tuple):  # pragma: no cover - compatibility
        major, minor = info[0], info[1]
    else:
        major = getattr(info, "major", 0)
        minor = getattr(info, "minor", 0)
    if major == 3 and minor == 13:
        logger.warning(
            "Python 3.13 detected. This version is experimental and not fully supported.",
        )


def system_check() -> Dict[str, bool]:
    """Run a suite of lightweight system checks and return their status."""

    logger.info("Performing system checks...")
    results: Dict[str, bool] = {}

    try:
        check_os_support()
        results["os_supported"] = True
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Operating system check failed")
        results["os_supported"] = False

    check_python_version()
    results["python_supported"] = True

    try:
        usage = shutil.disk_usage("/")
    except Exception:  # pragma: no cover - non-POSIX platforms
        logger.debug("Unable to determine disk usage for root filesystem.", exc_info=True)
    else:
        free_gb = usage.free / (1024 ** 3)
        if free_gb < 1:
            logger.warning("Low disk space detected on root filesystem: %.2f GiB free", free_gb)
            results["disk_space_ok"] = False
        else:
            logger.info("Available disk space on root filesystem: %.2f GiB", free_gb)
            results["disk_space_ok"] = True

    for tool in ("git", "python3"):
        available = shutil.which(tool) is not None
        if not available:
            logger.warning("Required executable '%s' not found on PATH", tool)
        results[f"{tool}_available"] = available

    return results
