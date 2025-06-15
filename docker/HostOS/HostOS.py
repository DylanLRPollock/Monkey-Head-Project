# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_error(command, description):
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        logger.error(error_message)
        raise RuntimeError(error_message)


def system_check():
    logger.info("Performing system checks for HostOS...")
    # Check for Debian version
    with open("/etc/os-release") as f:
        content = f.read().lower()
        if "debian" not in content or not any(
            x in content for x in ("trixie", "testing")
        ):
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
    logger.info("Installing tools for HostOS...")
    tools_install = subprocess.run(
        [
            "apt-get",
            "install",
            "-y",
            "git",
            "docker.io",
            "python3",
            "python3-venv",
            "qemu-kvm",
            "libvirt-daemon-system",
            "libvirt-clients",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(tools_install, "Tools Installation")


def configure_environment():
    logger.info("Configuring environment for HostOS...")
    os.makedirs(os.path.expanduser("~/HostOS"), exist_ok=True)
    os.environ["HOSTOS_PATH"] = os.path.expanduser("~/HostOS")
    with open(os.path.expanduser("~/.bashrc"), "a") as bashrc:
        bashrc.write("\nexport HOSTOS_PATH=$HOME/HostOS\n")


def enable_services():
    logger.info("Enabling Docker service...")
    enable_docker = subprocess.run(
        ["systemctl", "enable", "--now", "docker"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(enable_docker, "Enable Docker Service")


def check_virtualization():
    logger.info("Checking virtualization support...")
    try:
        output = subprocess.check_output(["grep", "-E", "vmx|svm", "/proc/cpuinfo"])
    except subprocess.CalledProcessError:
        output = b""
    if not output.strip():
        error_message = "Virtualization support not detected"
        logger.error(error_message)
        raise RuntimeError(error_message)


def configure_firewall(port: int = 5901):
    logger.info("Configuring firewall for port %d...", port)
    ufw_allow = subprocess.run(
        ["ufw", "allow", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(ufw_allow, "Configure Firewall")


def deploy_hostos():
    logger.info("Deploying HostOS environment...")
    os.chdir(os.path.expanduser("~/HostOS"))
    deploy = subprocess.run(
        ["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(deploy, "HostOS Deployment")
    kubectl = subprocess.run(
        ["kubectl", "apply", "-f", "HostOS.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(kubectl, "Kubernetes Deployment")


if __name__ == "__main__":
    system_check()
    install_tools()
    configure_environment()
    enable_services()
    check_virtualization()
    configure_firewall()
    deploy_hostos()
