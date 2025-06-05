import os
import logging
import subprocess
from system_checks import check_error

logger = logging.getLogger(__name__)


def clone_repository():
    logger.info("Cloning repository...")
    os.makedirs(os.path.expanduser("~/Source"), exist_ok=True)
    clone = subprocess.run(
        [
            "git",
            "clone",
            "https://github.com/your/repo.git",
            os.path.expanduser("~/Source/repo"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(clone, "Git Clone")


def setup_python_env():
    logger.info("Setting up Python environment...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    venv_create = subprocess.run(
        ["python3", "-m", "venv", "venv"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(venv_create, "Python Virtual Environment Setup")

    activate_venv = subprocess.run(
        ["source", "venv/bin/activate"], shell=True, executable="/bin/bash"
    )
    check_error(activate_venv, "Activate Python Virtual Environment")

    install_requirements = subprocess.run(
        ["pip", "install", "-r", "requirements.txt"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(install_requirements, "Install Python Requirements")


def configure_git():
    logger.info("Configuring Git...")
    git_config_name = subprocess.run(
        ["git", "config", "--global", "user.name", "Your Name"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(git_config_name, "Git Config Username")

    git_config_email = subprocess.run(
        ["git", "config", "--global", "user.email", "your.email@example.com"],
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
