# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import logging
import os
import platform
import subprocess

import distro
from ..logging_setup import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def ensure_admin() -> None:
    """Raise PermissionError if the current user is not root."""
    if os.geteuid() != 0:
        logger.error("Please run this script as root or with sudo.")
        raise PermissionError("Please run this script as root or with sudo.")


def log_error(description):
    logger.error(description)


def check_error(command, description):
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        log_error(error_message)
        raise RuntimeError(error_message)


def check_os_support() -> None:
    """Log a warning if the current OS is not officially supported."""
    system = platform.system()
    if system == "Windows":
        release = platform.release()
        try:
            major = int(release.split(".")[0])
        except ValueError:
            major = 0
        if major < 10:
            logger.warning(
                "Unsupported Windows version detected (%s). Windows 10 or newer is required.",
                release,
            )
    elif system == "Darwin":
        ver_str, _, _ = platform.mac_ver()
        try:
            major = int(ver_str.split(".")[0])
        except ValueError:
            major = 0
        if major < 13:
            logger.warning(
                "Unsupported macOS version detected (%s). macOS Ventura or newer is required.",
                ver_str,
            )
    elif system == "Linux":
        if distro.id() != "debian" or distro.codename().lower() not in {"trixie", "testing"}:
            logger.warning(
                "Unsupported Linux distribution detected (%s %s). Debian Trixie/testing is required.",
                distro.id(),
                distro.codename(),
            )
    else:
        logger.warning("Unsupported operating system detected: %s", system)


def system_check():
    logger.info("Performing system checks...")
    # Check for Debian version
    with open("/etc/os-release") as f:
        if "Debian GNU/Linux 13" not in f.read():
            error_message = "Debian Trixie Check failed"
            log_error(error_message)
            raise RuntimeError(error_message)

    # Check for available disk space
    free_space = subprocess.check_output(["df", "/"]).splitlines()[-1].split()[3]
    logger.info(f"Free space on /: {free_space}K")

    # Check for internet connectivity
    ping = subprocess.run(
        ["ping", "-c", "1", "google.com"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if ping.returncode != 0:
        error_message = "Internet Connectivity Check failed"
        log_error(error_message)
        raise RuntimeError(error_message)

    # Check for required software (e.g., Git)
    git_check = subprocess.run(
        ["which", "git"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(git_check, "Git Availability Check")
