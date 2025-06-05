import logging
import subprocess
from core.system_checks import check_error

logger = logging.getLogger(__name__)


def install_common_tools():
    logger.info("Installing common tools...")
    git_install = subprocess.run(
        ["apt-get", "install", "-y", "git", "nodejs"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(git_install, "Common Tools Installation")


def install_additional_tools():
    logger.info("Installing additional tools...")
    additional_tools_install = subprocess.run(
        ["apt-get", "install", "-y", "python3", "python3-venv", "docker.io"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(additional_tools_install, "Additional Tools Installation")


def install_optional_tools():
    logger.info("Installing optional tools...")
    optional_tools_install = subprocess.run(
        [
            "apt-get",
            "install",
            "-y",
            "postman",
            "slack",
            "zoom",
            "wget",
            "curl",
            "terraform",
            "kubectl",
            "minikube",
            "awscli",
            "azure-cli",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(optional_tools_install, "Optional Tools Installation")
