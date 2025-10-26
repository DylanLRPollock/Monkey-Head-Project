# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Orchestrator Utils module (docker)

"""Shared helpers for the HostOS/SubOS/NanoOS orchestrators."""
from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

_LOG = logging.getLogger(__name__)

_DEFAULT_PING_HOSTS = ("1.1.1.1", "8.8.8.8", "google.com")


def run(
    cmd: Sequence[str],
    logger: logging.Logger | None = None,
    *,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    **popen_kwargs,
) -> subprocess.CompletedProcess[str]:
    """Wrapper around :func:`subprocess.run` with logging and error handling."""

    logger = logger or _LOG
    logger.debug("→ %s", " ".join(cmd))

    if capture_output:
        popen_kwargs.setdefault("stdout", subprocess.PIPE)
        popen_kwargs.setdefault("stderr", subprocess.PIPE)

    popen_kwargs.setdefault("text", text)

    proc = subprocess.run(cmd, **popen_kwargs)
    if check and proc.returncode != 0:
        stdout = getattr(proc, "stdout", "")
        stderr = getattr(proc, "stderr", "")
        logger.error(
            "Command failed (%s): %s\nstdout:%s%s\nstderr:%s%s",
            proc.returncode,
            " ".join(cmd),
            "\n" if stdout else " ",
            stdout or "<no stdout>",
            "\n" if stderr else " ",
            stderr or "<no stderr>",
        )
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)} (exit code {proc.returncode})"
        )
    return proc


def _read_os_release() -> dict[str, str]:
    data: dict[str, str] = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue
                key, value = raw.split("=", 1)
                data[key.lower()] = value.strip('"')
    except FileNotFoundError:
        pass
    return data


def ensure_system_requirements(
    *,
    logger: logging.Logger,
    skip_os_check: bool = False,
    allowed_distros: Iterable[str] | None = None,
    min_free_gib: float = 5.0,
    ping_hosts: Iterable[str] = _DEFAULT_PING_HOSTS,
    required_commands: Iterable[str] | None = None,
) -> None:
    """Perform common system validations for orchestrators."""

    logger.info("Performing system checks…")
    os_release = _read_os_release()
    descriptor = " ".join(
        filter(
            None,
            (
                os_release.get("pretty_name"),
                os_release.get("name"),
                os_release.get("version"),
                os_release.get("version_id"),
                os_release.get("version_codename"),
                os_release.get("id"),
            ),
        )
    ).lower()

    if allowed_distros and not skip_os_check:
        allowed = [token.lower() for token in allowed_distros]
        if not descriptor:
            logger.warning("Unable to detect OS release; continuing cautiously.")
        elif not any(token in descriptor for token in allowed):
            pretty = os_release.get("pretty_name", "unknown")
            raise RuntimeError(
                "Unsupported distribution detected: "
                f"{pretty}. Pass --skip-os-check or --allow-os to override."
            )
    elif skip_os_check:
        logger.info("Skipping OS validation per user request.")

    if descriptor:
        logger.info("Detected host OS: %s", os_release.get("pretty_name", descriptor))

    usage = shutil.disk_usage("/")
    free_gib = usage.free / (1024**3)
    logger.info("Free space on /: %.2f GiB", free_gib)
    if free_gib < min_free_gib:
        logger.warning(
            "Recommended free space is %.1f GiB; only %.2f GiB detected.",
            min_free_gib,
            free_gib,
        )

    for host in ping_hosts:
        try:
            proc = run(["ping", "-c", "1", "-W", "2", host], logger, check=False)
            if proc.returncode == 0:
                logger.info("Internet connectivity verified via %s", host)
                break
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Ping to %s failed: %s", host, exc)
    else:
        raise RuntimeError(
            "Internet connectivity check failed (ping targets exhausted)."
        )

    for command in required_commands or ():
        if shutil.which(command) is None:
            logger.warning(
                "Required command '%s' not found; it will be installed if possible.",
                command,
            )


def apt_install(packages: Sequence[str], logger: logging.Logger) -> None:
    """Install the provided packages via apt-get."""

    if not packages:
        logger.info("No apt packages requested – skipping install.")
        return

    logger.info("Installing apt dependencies: %s", ", ".join(packages))
    run(["sudo", "apt-get", "update"], logger)
    run(
        ["sudo", "apt-get", "install", "-y", "--no-install-recommends", *packages],
        logger,
    )


def ensure_workspace(path: Path, env_var: str, logger: logging.Logger) -> None:
    """Create a persistent workspace and expose it via an environment variable."""

    path.mkdir(parents=True, exist_ok=True)
    logger.info("Workspace ready at %s", path)

    bashrc = Path.home() / ".bashrc"
    export_line = f"\nexport {env_var}={path}\n"
    try:
        content = bashrc.read_text(encoding="utf-8")
    except FileNotFoundError:
        bashrc.write_text(export_line, encoding="utf-8")
        logger.debug("Created %s with %s export", bashrc, env_var)
        return

    if env_var not in content:
        bashrc.write_text(content + export_line, encoding="utf-8")
        logger.debug("Appended %s export to %s", env_var, bashrc)


def enable_services(logger: logging.Logger) -> None:
    """Ensure Docker services are running."""

    logger.info("Enabling Docker service…")
    if shutil.which("systemctl"):
        run(["sudo", "systemctl", "enable", "--now", "docker"], logger, check=False)
    else:
        run(["sudo", "service", "docker", "start"], logger, check=False)

    try:
        run(["sudo", "usermod", "-aG", "docker", os.getlogin()], logger, check=False)
    except Exception:  # pragma: no cover - best-effort
        logger.debug("Unable to add current user to docker group.")


def _detect_cpu_flags() -> set[str]:
    flags: set[str] = set()
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.lower().startswith("flags"):
                    _, _, value = line.partition(":")
                    flags.update(value.strip().split())
    except FileNotFoundError:
        pass
    return {flag.lower() for flag in flags}


def _probe_virtualization_environment(logger: logging.Logger) -> str | None:
    """Return the detected virtualization environment, if any."""

    if shutil.which("systemd-detect-virt") is None:
        logger.debug("systemd-detect-virt not available on this host.")
        return None

    proc = run(["systemd-detect-virt"], logger, check=False)
    if proc.returncode == 0:
        output = (proc.stdout or proc.stderr or "").strip()
        return output or "unknown"
    if proc.returncode == 1:
        return "bare-metal"

    logger.debug(
        "systemd-detect-virt returned %s (stdout=%r, stderr=%r)",
        proc.returncode,
        getattr(proc, "stdout", ""),
        getattr(proc, "stderr", ""),
    )
    return None


def check_virtualization(logger: logging.Logger) -> None:
    """Verify that hardware virtualization is available for KVM/QEMU."""

    logger.info("Checking virtualization support…")
    virt_env = _probe_virtualization_environment(logger)
    if virt_env:
        logger.info("Detected virtualization environment: %s", virt_env)

    flags = _detect_cpu_flags()
    kvm_path = Path("/dev/kvm")
    kvm_ok = kvm_path.exists()

    logger.debug(
        "CPU virtualization flags detected: %s", ", ".join(sorted(flags)) or "<none>"
    )
    logger.debug("/dev/kvm present: %s", kvm_ok)

    if {"vmx", "svm"} & flags and kvm_ok:
        logger.info(
            "Hardware virtualization available (flags: %s).",
            ", ".join(sorted({"vmx", "svm"} & flags)),
        )
        return

    platform_hint = platform.system()
    guidance = (
        "Hardware virtualization was not detected. Ensure that VT-x/AMD-V is enabled in BIOS/UEFI. "
        "If you are running inside a macOS hypervisor or unsupported cloud VM, enable nested virtualization or "
        "consider using a QEMU/KVM capable host."
    )
    if platform_hint.lower() == "darwin":
        guidance += " macOS hosts require a hypervisor that exposes /dev/kvm (for example via UTM or QEMU)."
    elif virt_env and virt_env != "bare-metal":
        guidance += f" Detected virtualization layer: {virt_env}. Ensure it supports nested virtualization."

    missing_bits: list[str] = []
    if not ({"vmx", "svm"} & flags):
        missing_bits.append("CPU flags")
    if not kvm_ok:
        missing_bits.append("/dev/kvm")
    logger.error(
        "Virtualization prerequisites missing: %s", ", ".join(missing_bits) or "unknown"
    )
    raise RuntimeError(guidance)


def configure_firewall(
    port: int, logger: logging.Logger, *, proto: str = "tcp"
) -> None:
    """Open the requested port via UFW if available."""

    if shutil.which("ufw") is None:
        logger.warning(
            "UFW not installed; skipping firewall configuration for %d/%s.", port, proto
        )
        return

    rule = f"{port}/{proto}"
    status = run(["sudo", "ufw", "status"], logger, check=False)
    stdout = (status.stdout or "").lower()

    if rule in stdout:
        logger.info("UFW already allows %s", rule)
        return

    logger.info("Allowing %s via UFW", rule)
    run(["sudo", "ufw", "allow", rule], logger, check=False)


__all__ = [
    "apt_install",
    "check_virtualization",
    "configure_firewall",
    "enable_services",
    "ensure_system_requirements",
    "ensure_workspace",
    "run",
]
