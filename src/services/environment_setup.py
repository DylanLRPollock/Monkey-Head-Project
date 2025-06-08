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

from core.system_checks import check_error

logger = logging.getLogger(__name__)


DEFAULT_REPO_URL = "https://github.com/DylanLRPollock/Monkey-Head-Project.git"


def clone_repository(repo_url: str = DEFAULT_REPO_URL, dest: str = "~/Source/repo") -> None:
    """Clone the repository to the given destination."""
    logger.info("Cloning repository...")
    dest_path = os.path.expanduser(dest)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    clone = subprocess.run(
        ["git", "clone", repo_url, dest_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(clone, "Git Clone")


def setup_python_env(dest: str = "~/Source/repo") -> None:
    """Create a virtual environment and install requirements."""
    logger.info("Setting up Python environment...")
    repo_path = os.path.expanduser(dest)
    venv_path = os.path.join(repo_path, "venv")
    venv_create = subprocess.run(
        ["python3", "-m", "venv", venv_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(venv_create, "Python Virtual Environment Setup")

    pip_path = os.path.join(venv_path, "bin", "pip")
    install_requirements = subprocess.run(
        [pip_path, "install", "-r", "requirements.txt"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(install_requirements, "Install Python Requirements")


def configure_git(name: str = "Your Name", email: str = "your.email@example.com") -> None:
    """Configure global git username and email."""
    logger.info("Configuring Git...")
    git_config_name = subprocess.run(
        ["git", "config", "--global", "user.name", name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(git_config_name, "Git Config Username")

    git_config_email = subprocess.run(
        ["git", "config", "--global", "user.email", email],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(git_config_email, "Git Config Email")


def create_directories():
    logger.info("Creating common directories...")
    os.makedirs(os.path.expanduser("~/Projects"), exist_ok=True)
    os.makedirs(os.path.expanduser("~/Tools"), exist_ok=True)


def update_env_variables():
    logger.info("Updating environment variables...")
    os.environ["PATH"] += os.pathsep + os.path.expanduser("~/Tools")
    # Persist the change across sessions
    with open(os.path.expanduser("~/.bashrc"), "a") as bashrc:
        bashrc.write("\nexport PATH=$PATH:$HOME/Tools\n")
