# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os
import subprocess
from .logger import get_logger
import pwd

from .core.system_checks import check_error, ensure_admin

logger = get_logger(__name__)


def update_system() -> None:
    """Update package lists and installed packages."""
    logger.info("Updating system packages...")
    update = subprocess.run(
        ["apt-get", "update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(update, "apt-get update")
    upgrade = subprocess.run(
        ["apt-get", "upgrade", "-y"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(upgrade, "apt-get upgrade")


def install_tools() -> None:
    """Install required virtualization and container tools."""
    logger.info("Installing SubOS tools...")
    tools = [
        "git",
        "docker.io",
        "qemu-kvm",
        "libvirt-daemon-system",
        "libvirt-clients",
        "virt-manager",
        "python3",
        "python3-venv",
    ]
    install = subprocess.run(
        ["apt-get", "install", "-y", *tools],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(install, "Install SubOS tools")


def create_user(user: str = "subos") -> None:
    """Create a dedicated SubOS user if missing."""
    logger.info("Ensuring %s user exists...", user)
    try:
        pwd.getpwnam(user)
        logger.info("User %s already exists", user)
    except KeyError:
        add_user = subprocess.run(
            ["useradd", "-m", user],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        check_error(add_user, f"Create user {user}")


def configure_environment() -> None:
    """Configure directories and environment variables."""
    logger.info("Configuring SubOS environment...")
    base = os.path.expanduser("~/SubOS")
    os.makedirs(base, exist_ok=True)
    os.environ["SUBOS_PATH"] = base
    with open(os.path.expanduser("~/.bashrc"), "a") as bashrc:
        bashrc.write("\nexport SUBOS_PATH=$HOME/SubOS\n")


def deploy_subos() -> None:
    """Deploy the SubOS Docker environment."""
    logger.info("Deploying SubOS...")
    os.chdir(os.path.expanduser("~/SubOS"))
    deploy = subprocess.run(
        ["docker-compose", "up", "-d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(deploy, "SubOS deployment")


def run() -> None:
    """Full SubOS setup routine."""
    ensure_admin()
    update_system()
    install_tools()
    create_user()
    configure_environment()
    deploy_subos()
