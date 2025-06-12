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
from ..utils.logger import get_logger
from ..utils.commands import run_command

logger = get_logger(__name__)


DEFAULT_REPO_URL = "https://github.com/DylanLRPollock/Monkey-Head-Project.git"


def clone_repository(repo_url: str = DEFAULT_REPO_URL, dest: str = "~/Source/repo") -> None:
    """Clone the repository to the given destination."""
    logger.info("Cloning repository...")
    dest_path = os.path.expanduser(dest)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    run_command(["git", "clone", repo_url, dest_path], check=True)


def setup_python_env(dest: str = "~/Source/repo") -> None:
    """Create a virtual environment and install requirements."""
    logger.info("Setting up Python environment...")
    repo_path = os.path.expanduser(dest)
    venv_path = os.path.join(repo_path, "venv")
    if not os.path.isdir(venv_path):
        run_command(["python3", "-m", "venv", venv_path])

    pip_path = os.path.join(venv_path, "bin", "pip")
    run_command(
        [pip_path, "install", "-r", "requirements.txt"],
        cwd=repo_path,
    )


def configure_git(name: str = "Your Name", email: str = "your.email@example.com") -> None:
    """Configure global git username and email."""
    logger.info("Configuring Git...")
    current_name = subprocess.run(
        ["git", "config", "--global", "user.name"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.decode().strip()
    if current_name != name:
        run_command(["git", "config", "--global", "user.name", name])

    current_email = subprocess.run(
        ["git", "config", "--global", "user.email"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.decode().strip()
    if current_email != email:
        run_command(["git", "config", "--global", "user.email", email])


def create_directories():
    logger.info("Creating common directories...")
    os.makedirs(os.path.expanduser("~/Projects"), exist_ok=True)
    os.makedirs(os.path.expanduser("~/Tools"), exist_ok=True)


def update_env_variables():
    logger.info("Updating environment variables...")
    os.environ["PATH"] += os.pathsep + os.path.expanduser("~/Tools")
    bashrc_path = os.path.expanduser("~/.bashrc")
    line = "export PATH=$PATH:$HOME/Tools"
    if os.path.exists(bashrc_path):
        with open(bashrc_path) as bashrc:
            content = bashrc.read()
    else:
        content = ""
    if line not in content:
        with open(bashrc_path, "a") as bashrc:
            bashrc.write(f"\n{line}\n")
