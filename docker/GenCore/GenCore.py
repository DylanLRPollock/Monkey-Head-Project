# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""GenCore environment generator.

This script builds and deploys the GenCore AI/OS using Docker and Kubernetes.
"""
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_error(command: subprocess.CompletedProcess, description: str) -> None:
    """Raise RuntimeError if the command failed."""
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        logger.error(error_message)
        raise RuntimeError(error_message)


def prepare_environment() -> None:
    """Create required directories for GenCore."""
    logger.info("Preparing GenCore environment directory...")
    os.makedirs(os.path.expanduser("~/GenCore"), exist_ok=True)


def build_image(tag: str = "gencore-aios:latest") -> None:
    """Build the Docker image for GenCore."""
    logger.info("Building GenCore Docker image...")
    build = subprocess.run(
        [
            "docker",
            "build",
            "-t",
            tag,
            ".",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(build, "Build GenCore Docker Image")


def deploy_gencore() -> None:
    """Deploy GenCore using Docker Compose and Kubernetes."""
    logger.info("Deploying GenCore environment...")
    os.chdir(os.path.expanduser("~/GenCore"))
    deploy = subprocess.run(
        [
            "docker-compose",
            "up",
            "-d",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(deploy, "GenCore Deployment")

    kubectl = subprocess.run(
        [
            "kubectl",
            "apply",
            "-f",
            "GenCore.yaml",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(kubectl, "Kubernetes Deployment")


if __name__ == "__main__":
    prepare_environment()
    build_image()
    deploy_gencore()
