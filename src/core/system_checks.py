import os
import logging
import subprocess

logger = logging.getLogger(__name__)


def log_error(description):
    logger.error(description)


def check_error(command, description):
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        log_error(error_message)
        raise RuntimeError(error_message)


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
