# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: System Checks module (src/huey/os)

"""System environment checks for the Monkey Head runtime."""

from __future__ import annotations

import logging
import platform
import re
import shutil
import sys
from typing import Any

from huey.os.core.platform_support import (
    HostPlatform,
    detect_host_platform,
    distro as platform_distro,
    require_admin_privileges,
)


logger = logging.getLogger(__name__)
distro = platform_distro

SUPPORTED_DISTRO_ID = "debian"
SUPPORTED_DISTRO_CODENAME = "forky"
SUPPORTED_KERNEL_FAMILY = "hueyos"
KERNEL_ROLE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LAB_KERNEL_ROLES = frozenset({"lab", "test"})
PRODUCTION_KERNEL_ROLES = frozenset({"core", "pulse"})
DEFAULT_RUNTIME_POLICY = "production"
MIN_PYTHON_VERSION = (3, 13)
MAX_PYTHON_VERSION = (3, 14)
MIN_WINDOWS_RELEASE = 10
MIN_MACOS_MAJOR = 12
BASE_REQUIRED_TOOLS: tuple[str, ...] = (
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

ROLE_REQUIRED_TOOLS: dict[str, tuple[str, ...]] = {
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

WINDOWS_REQUIRED_TOOLS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("git", ("git",)),
    ("python", ("python", "py")),
    ("powershell", ("pwsh", "powershell")),
)

MACOS_REQUIRED_TOOLS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("git", ("git",)),
    ("python3", ("python3",)),
    ("bash", ("bash",)),
    ("pmset", ("pmset",)),
    ("networksetup", ("networksetup",)),
)

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

    try:
        require_admin_privileges()
    except PermissionError as exc:
        logger.error(str(exc))
        raise


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


def _detect_linux_distribution(host: HostPlatform | None = None) -> tuple[str, str]:
    """Return a tuple of ``(distribution_id, codename)`` for Linux hosts."""

    host = host or detect_host_platform()
    return host.distribution_id, host.distribution_codename


def _leading_version_number(value: str) -> int | None:
    """Extract the first integer version component from a platform string."""

    match = re.search(r"\d+", value)
    if not match:
        return None
    return int(match.group(0))


def _check_windows_support(host: HostPlatform) -> bool:
    release = host.release or host.version
    major = _leading_version_number(host.release) or _leading_version_number(host.version)
    if major is None or major < MIN_WINDOWS_RELEASE:
        logger.warning(
            "Unsupported Windows version detected: %s. HueyOS requires Windows %s or newer.",
            release or "unknown",
            MIN_WINDOWS_RELEASE,
        )
        return False
    return True


def _check_macos_support(host: HostPlatform) -> bool:
    version = platform.mac_ver()[0] or host.release or host.version
    major = _leading_version_number(version)
    if major is None or major < MIN_MACOS_MAJOR:
        logger.warning(
            "Unsupported macOS version detected: %s. HueyOS requires macOS %s or newer.",
            version or "unknown",
            MIN_MACOS_MAJOR,
        )
        return False
    return True


def check_os_support(host: HostPlatform | None = None) -> bool:
    """Verify the host operating system matches the supported matrix."""

    host = host or detect_host_platform()
    if host.is_windows:
        return _check_windows_support(host)

    if host.is_macos:
        return _check_macos_support(host)

    if not host.is_linux:
        logger.warning("Unsupported operating system detected: %s", host.system or "unknown")
        return False

    dist_id, codename = _detect_linux_distribution(host)
    supported = dist_id == SUPPORTED_DISTRO_ID and codename == SUPPORTED_DISTRO_CODENAME

    if not supported:
        logger.warning(
            "Unsupported Linux distribution detected (%s %s). Debian Forky is required.",
            dist_id or "unknown",
            codename or "unknown",
        )

    return supported


def _platform_runtime_policy(
    host: HostPlatform,
    *,
    os_supported: bool,
) -> dict[str, Any]:
    """Return platform support metadata for non-Linux hosts."""

    errors = (
        []
        if os_supported
        else [f"{host.runtime_display_name} runtime support check failed."]
    )
    return {
        "release": host.release or host.version,
        "version": host.version or host.release,
        "version_prefix": (),
        "family": host.family,
        "detected_family": host.family,
        "family_role_present": False,
        "detected_role": "",
        "role": "",
        "role_valid": True,
        "is_lab_kernel": False,
        "is_release_candidate": False,
        "production_supported": os_supported,
        "lab_supported": os_supported,
        "runtime_policy": DEFAULT_RUNTIME_POLICY,
        "runtime_allowed": os_supported,
        "errors": errors,
        "platform_specific": True,
    }


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


def _parse_numeric_kernel_prefix(version_str: str) -> tuple[int, ...]:
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


def check_kernel_policy() -> dict[str, Any]:
    """Evaluate kernel naming and policy support for production and lab modes."""

    release = platform.release()
    version_str = _extract_kernel_version(release)
    lowered = release.strip().lower()
    runtime_policy = DEFAULT_RUNTIME_POLICY

    result: dict[str, Any] = {
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


def _python_version_parts(info: object) -> tuple[int, int]:
    """Return the active interpreter's ``(major, minor)`` version tuple."""

    if isinstance(info, tuple):  # pragma: no cover - compatibility for patched tuples
        major, minor = (info + (0, 0))[:2]
        return int(major), int(minor)

    major = getattr(info, "major", 0)
    minor = getattr(info, "minor", 0)
    return int(major), int(minor)


def _is_free_threaded_build() -> bool:
    """Return ``True`` when running on an experimental free-threaded CPython build."""

    version_text = str(getattr(sys, "version", "")).lower()
    if "free-threading build" in version_text:
        return True
    return str(getattr(sys, "abiflags", "")) == "t"


def _python_gil_enabled() -> bool | None:
    """Return the current GIL state when the interpreter exposes it."""

    checker = getattr(sys, "_is_gil_enabled", None)
    if not callable(checker):
        return None

    try:
        return bool(checker())
    except Exception:  # pragma: no cover - interpreter-specific edge cases
        return None


def check_python_version() -> bool:
    """Ensure the active Python interpreter falls within the supported range."""

    major, minor = _python_version_parts(sys.version_info)

    supported = (major, minor) >= MIN_PYTHON_VERSION and (
        major,
        minor,
    ) < MAX_PYTHON_VERSION

    if not supported:
        if (major, minor) == MAX_PYTHON_VERSION:
            logger.warning(
                "Python %s.%s detected. Python %s.%s.x is a testing-only "
                "compatibility lane; supported target is Python %s.%s.x.",
                major,
                minor,
                MAX_PYTHON_VERSION[0],
                MAX_PYTHON_VERSION[1],
                MIN_PYTHON_VERSION[0],
                MIN_PYTHON_VERSION[1],
            )
        else:
            logger.warning(
                "Python %s.%s detected. Supported target is Python %s.%s.x.",
                major,
                minor,
                MIN_PYTHON_VERSION[0],
                MIN_PYTHON_VERSION[1],
            )
        return False

    if _is_free_threaded_build():
        gil_enabled = _python_gil_enabled()
        gil_suffix = ""
        if gil_enabled is False:
            gil_suffix = " with the GIL disabled"
        elif gil_enabled is True:
            gil_suffix = " with the GIL re-enabled"
        logger.warning(
            "Experimental free-threaded Python %s.%s build detected%s. "
            "HueyOS currently supports the standard GIL-enabled Python %s.%s.x runtime only.",
            major,
            minor,
            gil_suffix,
            MIN_PYTHON_VERSION[0],
            MIN_PYTHON_VERSION[1],
        )
        return False

    return True


def _required_tools_for_role(role: str) -> tuple[str, ...]:
    """Return required executables for the detected kernel role."""

    normalized_role = role.strip().lower()
    role_tools = ROLE_REQUIRED_TOOLS.get(normalized_role, ())
    ordered_tools: list[str] = []
    for tool in (*BASE_REQUIRED_TOOLS, *role_tools):
        if tool not in ordered_tools:
            ordered_tools.append(tool)
    return tuple(ordered_tools)


def _required_tool_candidates(
    host: HostPlatform,
    role: str,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if host.is_windows:
        return WINDOWS_REQUIRED_TOOLS
    if host.is_macos:
        return MACOS_REQUIRED_TOOLS
    return tuple((tool, (tool,)) for tool in _required_tools_for_role(role))


def _check_required_tools(
    role: str = "",
    host: HostPlatform | None = None,
) -> dict[str, bool]:
    """Return a mapping of required tool names to their availability."""

    host = host or detect_host_platform()
    results: dict[str, bool] = {}
    for tool, candidates in _required_tool_candidates(host, role):
        available = any(shutil.which(candidate) is not None for candidate in candidates)
        if not available:
            logger.warning(
                "Required executable '%s' not found on PATH (checked: %s)",
                tool,
                ", ".join(candidates),
            )
        results[tool] = available
    return results


def system_check() -> dict[str, Any]:
    """Run the suite of system checks and return their boolean results."""

    logger.info("Performing system checks...")
    results: dict[str, Any] = {}
    host = detect_host_platform()

    results["os_supported"] = check_os_support(host)
    kernel_policy = (
        check_kernel_policy()
        if host.is_linux
        else _platform_runtime_policy(host, os_supported=results["os_supported"])
    )
    results["kernel_supported"] = bool(kernel_policy["production_supported"])
    results["kernel_policy"] = kernel_policy
    results["python_supported"] = check_python_version()

    tool_results = _check_required_tools(
        str(kernel_policy.get("detected_role", "")),
        host=host,
    )
    for name, status in tool_results.items():
        results[f"{name}_available"] = status
    results["tools_available"] = all(tool_results.values()) if tool_results else True

    return results
