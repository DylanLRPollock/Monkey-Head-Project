# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_error(command, description):
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        logger.error(error_message)
        raise RuntimeError(error_message)


def system_check():
    logger.info("Performing system checks for NanoOS...")
    # Check for Debian version
    with open("/etc/os-release") as f:
        content = f.read().lower()
        if "debian" not in content or not any(x in content for x in ("trixie", "testing")):
            error_message = "Debian Trixie/Testing Check failed"
            logger.error(error_message)
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
        logger.error(error_message)
        raise RuntimeError(error_message)

    # Check for required software (e.g., Git)
    git_check = subprocess.run(
        ["which", "git"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(git_check, "Git Availability Check")


def install_tools():
    logger.info("Installing tools for NanoOS...")
    tools_install = subprocess.run(
        ["apt-get", "install", "-y", "git", "docker.io", "python3", "python3-venv"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(tools_install, "Tools Installation")


def configure_environment():
    logger.info("Configuring environment for NanoOS...")
    os.makedirs(os.path.expanduser("~/NanoOS"), exist_ok=True)
    os.environ["NANOOS_PATH"] = os.path.expanduser("~/NanoOS")
    with open(os.path.expanduser("~/.bashrc"), "a") as bashrc:
        bashrc.write("\nexport NANOOS_PATH=$HOME/NanoOS\n")


def deploy_nanoos():
    logger.info("Deploying NanoOS environment...")
    os.chdir(os.path.expanduser("~/NanoOS"))
    deploy = subprocess.run(
        ["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(deploy, "NanoOS Deployment")


if __name__ == "__main__":
    system_check()
    install_tools()
    configure_environment()
    deploy_nanoos()
