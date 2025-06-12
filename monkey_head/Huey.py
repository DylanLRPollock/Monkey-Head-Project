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
from flask import Flask, jsonify

from .core.system_checks import system_check, ensure_admin
from .modules.updates import update_system, update_python_packages
from .core.installations import (
    install_common_tools,
    install_additional_tools,
    install_optional_tools,
)
from .services.environment_setup import (
    clone_repository,
    setup_python_env,
    configure_git,
    create_directories,
    update_env_variables,
)
from .services.container_management import (
    manage_containers,
    manage_volumes,
    deploy_kubernetes,
    kubernetes_management,
)
from . import subos_manager
from .scripts.backup_restore import backup_config, restore_config
from .logging_setup import configure_logging

app = Flask(__name__)

# Configure logging using project settings
configure_logging()
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="healthy"), 200


@app.route("/ready", methods=["GET"])
def readiness_check():
    return jsonify(status="ready"), 200


def check_error(command: subprocess.CompletedProcess, description: str) -> None:
    """Raise RuntimeError if command failed."""
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        logger.error(error_message)
        raise RuntimeError(error_message)


def build_system() -> None:
    logger.info("Building System...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    build = subprocess.run(
        ["python", "setup.py", "build"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(build, "Build System")


def start_system() -> None:
    logger.info("Starting System...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    start = subprocess.run(
        ["python", "main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(start, "Start System")


def setup_hostos() -> None:
    logger.info("Setting up HostOS...")
    install_htop = subprocess.run(
        ["apt-get", "install", "-y", "htop"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(install_htop, "Install htop")


def setup_subos() -> None:
    logger.info("Setting up SubOS...")
    subos_manager.run()


def setup_nanoos() -> None:
    logger.info("Setting up NanoOS...")

    install = subprocess.run(
        [
            "apt-get",
            "install",
            "-y",
            "git",
            "docker.io",
            "python3",
            "python3-venv",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(install, "Install NanoOS tools")

    nanoos_dir = os.path.expanduser("~/NanoOS")
    os.makedirs(nanoos_dir, exist_ok=True)
    os.environ["NANOOS_PATH"] = nanoos_dir
    with open(os.path.expanduser("~/.bashrc"), "a") as bashrc:
        bashrc.write("\nexport NANOOS_PATH=$HOME/NanoOS\n")

    deploy = subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd=nanoos_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(deploy, "Deploy NanoOS")


def status() -> None:
    logger.info("Checking System Status...")
    docker_status = subprocess.run(
        ["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(docker_status, "Check Docker Status")

    kubernetes_status = subprocess.run(
        ["kubectl", "get", "pods"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(kubernetes_status, "Check Kubernetes Status")


def check_dependencies() -> None:
    logger.info("Checking and Installing Dependencies...")
    terraform_check = subprocess.run(
        ["which", "terraform"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if terraform_check.returncode != 0:
        install_terraform = subprocess.run(
            ["apt-get", "install", "-y", "terraform"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        check_error(install_terraform, "Install Terraform")


if __name__ == "__main__":
    ensure_admin()
    system_check()
    update_system()
    install_common_tools()
    install_additional_tools()
    install_optional_tools()
    clone_repository()
    setup_python_env()
    configure_git()
    create_directories()
    update_env_variables()
    update_python_packages()
    build_system()
    manage_containers()
    manage_volumes()
    deploy_kubernetes()
    start_system()
    setup_hostos()
    setup_subos()
    setup_nanoos()
    kubernetes_management()
    status()
    backup_config()
    restore_config()
    check_dependencies()

    app.run(host="0.0.0.0", port=4488)
