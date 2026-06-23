# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Subos Manager module (huey/memory/PY)

import logging

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import os

try:
    import pwd
except ImportError:  # pragma: no cover - Windows fallback for tests

    class _PwdModule:
        @staticmethod
        def getpwnam(_user: str):
            raise KeyError(_user)

    pwd = _PwdModule()  # type: ignore[assignment]

from huey.os.core.system_checks import ensure_admin

from .commands import run_command

logger = logging.getLogger(__name__)


def update_system() -> None:
    """Update package lists and installed packages."""
    logger.info("Updating system packages...")
    run_command(["apt-get", "update"])
    run_command(["apt-get", "upgrade", "-y"])


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
        "mate-desktop-environment-core",
    ]
    run_command(["apt-get", "install", "-y", *tools])


def create_user(user: str = "subos") -> None:
    """Create a dedicated SubOS user if missing."""
    logger.info("Ensuring %s user exists...", user)
    try:
        pwd.getpwnam(user)
        logger.info("User %s already exists", user)
    except KeyError:
        run_command(["useradd", "-m", user])


def configure_environment() -> None:
    """Configure directories and environment variables."""
    logger.info("Configuring SubOS environment...")
    base = os.path.expanduser("~/SubOS")
    os.makedirs(base, exist_ok=True)
    os.environ["SUBOS_PATH"] = base
    bashrc_path = os.path.expanduser("~/.bashrc")
    line = "export SUBOS_PATH=$HOME/SubOS"
    if os.path.exists(bashrc_path):
        with open(bashrc_path) as bashrc:
            content = bashrc.read()
    else:
        content = ""
    if line not in content:
        with open(bashrc_path, "a") as bashrc:
            bashrc.write(f"\n{line}\n")


def deploy_subos() -> None:
    """Deploy the SubOS Docker environment."""
    logger.info("Deploying SubOS...")
    os.chdir(os.path.expanduser("~/SubOS"))
    run_command(["docker-compose", "up", "-d"])


def run() -> None:
    """Full SubOS setup routine."""
    ensure_admin()
    update_system()
    install_tools()
    create_user()
    configure_environment()
    deploy_subos()
