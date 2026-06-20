# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: System Checks module (src/huey/os)

"""System environment checks for the Monkey Head runtime."""

from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import sys
from typing import Any, Dict, Tuple

try:  # pragma: no cover - optional dependency on Linux only
    import distro  # type: ignore
except Exception:  # pragma: no cover - handled gracefully in tests
    distro = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

SUPPORTED_DISTRO_ID = "debian"
SUPPORTED_DISTRO_CODENAME = "forky"
SUPPORTED_KERNEL_FAMILY = "hueyos"
KERNEL_ROLE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LAB_KERNEL_ROLES = frozenset({"lab", "test"})
PRODUCTION_KERNEL_ROLES = frozenset({"core", "pulse"})
DEFAULT_RUNTIME_POLICY = "production"
MIN_PYTHON_VERSION = (3, 13)
MAX_PYTHON_VERSION = (3, 15)
BASE_REQUIRED_TOOLS: Tuple[str, ...] = (
    "git",
    "python3",
    "bash",
    "systemctl",
    "journalctl",
    "modprobe",
    "udevadm",
    "ip",
    "mount",
)

ROLE_REQUIRED_TOOLS: Dict[str, Tuple[str, ...]] = {
    "core": (
        "lsblk",
        "blkid",
        "findmnt",
        "partprobe",
        "mdadm",
        "cryptsetup",
        "lvdisplay",
    ),
    "pulse": (
        "lsblk",
        "blkid",
        "findmnt",
        "tc",
        "ethtool",
        "nmcli",
        "iostat",
        "pavucontrol",
    ),
}

__all__ = [
    "logger",
    "ensure_admin",
    "log_error",
    "check_error",
    "check_os_support",
    "check_python_version",
    "check_kernel_policy",
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


def log_error(description: str) -> None:
    """Log an error message through the module logger."""

    logger.error(description)


def check_error(command: object, description: str) -> None:
    """Raise a :class:`RuntimeError` when a command returns a non-zero code."""

    returncode = getattr(command, "returncode", 0)
    if returncode != 0:
        message = f"Error: {description} failed with error code {returncode}."
        log_error(message)
        raise RuntimeError(message)


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
    supported = dist_id == SUPPORTED_DISTRO_ID and codename == SUPPORTED_DISTRO_CODENAME

    if not supported:
        logger.warning(
            "Unsupported Linux distribution detected (%s %s). Debian Forky is required.",
            dist_id or "unknown",
            codename or "unknown",
        )

    return supported


def _extract_kernel_version(raw_release: str) -> str:
    """Return the numeric kernel version prefix from a release string."""

    version = raw_release.split("-")[0]
    version = version.split("+")[0]
    return version.strip()


def _extract_kernel_role(raw_release: str) -> str:
    """Extract the HueyOS kernel role segment from a release string."""

    lowered = raw_release.strip().lower()
    marker = f"{SUPPORTED_KERNEL_FAMILY}-"
    index = lowered.find(marker)
    if index < 0:
        return ""

    role_start = index + len(marker)
    remainder = lowered[role_start:]
    if not remainder:
        return ""

    role = re.split(r"[+._]", remainder, maxsplit=1)[0]
    return role.strip()


def _parse_numeric_kernel_prefix(version_str: str) -> Tuple[int, ...]:
    """Convert a dotted kernel version prefix into a numeric tuple."""

    if not version_str:
        return ()

    parts = []
    for segment in version_str.split("."):
        if not segment.isdigit():
            break
        parts.append(int(segment))
    return tuple(parts)


def _is_release_candidate_kernel(raw_release: str) -> bool:
    """Return ``True`` when the kernel release includes an ``-rcN`` segment."""

    lowered = raw_release.strip().lower()
    marker = f"-{SUPPORTED_KERNEL_FAMILY}-"
    marker_index = lowered.find(marker)
    candidate_segment = lowered if marker_index < 0 else lowered[:marker_index]
    return re.search(r"-rc\d+\b", candidate_segment) is not None


def _check_kernel_naming() -> bool:
    """Return ``True`` when the running kernel satisfies production policy."""

    kernel_result = check_kernel_policy()
    return bool(kernel_result["production_supported"])


def check_kernel_policy() -> Dict[str, Any]:
    """Evaluate kernel naming and policy support for production and lab modes."""

    release = platform.release()
    version_str = _extract_kernel_version(release)
    lowered = release.strip().lower()
    runtime_policy = DEFAULT_RUNTIME_POLICY

    result: Dict[str, Any] = {
        "release": release,
        "version": version_str,
        "version_prefix": _parse_numeric_kernel_prefix(version_str),
        "family": SUPPORTED_KERNEL_FAMILY,
        "detected_family": "",
        "family_role_present": f"{SUPPORTED_KERNEL_FAMILY}-" in lowered,
        "detected_role": "",
        "role": "",
        "role_valid": False,
        "is_lab_kernel": False,
        "is_release_candidate": False,
        "production_supported": False,
        "lab_supported": False,
        "runtime_policy": runtime_policy,
        "runtime_allowed": False,
        "errors": [],
    }

    if not version_str:
        message = f"Unable to parse kernel version from release '{release}'"
        logger.warning(message)
        result["errors"].append(message)
        return result

    if not result["family_role_present"]:
        message = (
            f"Kernel release '{release}' is missing the "
            f"'{SUPPORTED_KERNEL_FAMILY}-<role>' family/role suffix."
        )
        logger.warning(message)
        result["errors"].append(message)
        return result

    role = _extract_kernel_role(lowered)
    result["detected_family"] = SUPPORTED_KERNEL_FAMILY
    result["detected_role"] = role
    result["role"] = role
    role_valid = bool(role and KERNEL_ROLE_PATTERN.match(role))
    result["role_valid"] = role_valid

    if not role_valid:
        message = (
            f"Kernel release '{release}' has an invalid HueyOS role segment "
            f"'{role or 'missing'}'."
        )
        logger.warning(message)
        result["errors"].append(message)
        return result

    is_rc = _is_release_candidate_kernel(lowered)
    result["is_release_candidate"] = is_rc
    is_production_role = role in PRODUCTION_KERNEL_ROLES
    is_lab_role = role in LAB_KERNEL_ROLES
    result["is_lab_kernel"] = is_lab_role

    production_supported = is_production_role and not is_rc
    lab_supported = is_production_role or is_lab_role
    if is_rc:
        lab_supported = lab_supported or is_production_role

    result["production_supported"] = production_supported
    result["lab_supported"] = lab_supported
    result["runtime_allowed"] = production_supported

    if is_rc and not lab_supported:
        message = (
            f"Kernel release '{release}' uses an rc kernel outside accepted lab roles "
            f"({', '.join(sorted(LAB_KERNEL_ROLES))}) and production roles "
            f"({', '.join(sorted(PRODUCTION_KERNEL_ROLES))})."
        )
        logger.warning(message)
        result["errors"].append(message)

    if is_lab_role:
        kernel_type = "release-candidate" if is_rc else "stable/lab"
        logger.info(
            "Detected explicit HueyOS %s kernel role '%s' (%s).",
            SUPPORTED_KERNEL_FAMILY,
            role,
            kernel_type,
        )

    if is_production_role and not is_rc:
        logger.info("Detected production-ready HueyOS kernel role '%s'.", role)

    return result


def _check_kernel_version() -> bool:
    """Compatibility wrapper for legacy callers expecting this function name."""

    return _check_kernel_naming()


def check_python_version() -> bool:
    """Ensure the active Python interpreter falls within the supported range."""

    info = sys.version_info
    if isinstance(info, tuple):  # pragma: no cover - compatibility for patched tuples
        major, minor, micro = (info + (0, 0, 0))[:3]
    else:
        major = getattr(info, "major", 0)
        minor = getattr(info, "minor", 0)
        micro = getattr(info, "micro", 0)

    supported = (major, minor) >= MIN_PYTHON_VERSION and (
        major,
        minor,
    ) < MAX_PYTHON_VERSION

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


def _required_tools_for_role(role: str) -> Tuple[str, ...]:
    """Return required executables for the detected kernel role."""

    normalized_role = role.strip().lower()
    role_tools = ROLE_REQUIRED_TOOLS.get(normalized_role, ())
    ordered_tools: list[str] = []
    for tool in (*BASE_REQUIRED_TOOLS, *role_tools):
        if tool not in ordered_tools:
            ordered_tools.append(tool)
    return tuple(ordered_tools)


def _check_required_tools(role: str = "") -> Dict[str, bool]:
    """Return a mapping of required tool names to their availability."""

    results: Dict[str, bool] = {}
    for tool in _required_tools_for_role(role):
        available = shutil.which(tool) is not None
        if not available:
            logger.warning("Required executable '%s' not found on PATH", tool)
        results[tool] = available
    return results


def system_check() -> Dict[str, Any]:
    """Run the suite of system checks and return their boolean results."""

    logger.info("Performing system checks...")
    results: Dict[str, Any] = {}

    results["os_supported"] = check_os_support()
    kernel_policy = check_kernel_policy()
    results["kernel_supported"] = bool(kernel_policy["production_supported"])
    results["kernel_policy"] = kernel_policy
    results["python_supported"] = check_python_version()

    tool_results = _check_required_tools(str(kernel_policy.get("detected_role", "")))
    for name, status in tool_results.items():
        results[f"{name}_available"] = status
    results["tools_available"] = all(tool_results.values()) if tool_results else True

    return results
