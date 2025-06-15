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
import argparse
import logging
import os
import shutil
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_error(command: subprocess.CompletedProcess, description: str) -> None:
    """Raise RuntimeError if the command failed."""
    if command.returncode != 0:
        error_message = (
            f"Error: {description} failed with error code {command.returncode}."
        )
        logger.error(error_message)
        raise RuntimeError(error_message)


DEFAULT_WORKDIR = os.path.expanduser("~/GenCore")
DEFAULT_TAG = "gencore-aios:latest"
DEFAULT_COMPOSE_FILE = "docker-compose.yml"
DEFAULT_K8S_FILE = "GenCore.yaml"


def require_tools(tools: list[str]) -> None:
    """Ensure that required command line tools are available."""
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        names = ", ".join(missing)
        raise EnvironmentError(f"Required tools not found in PATH: {names}")


def prepare_environment(workdir: str = DEFAULT_WORKDIR) -> None:
    """Create required directories for GenCore."""
    logger.info("Preparing GenCore environment directory at %s...", workdir)
    os.makedirs(workdir, exist_ok=True)


def build_image(tag: str = DEFAULT_TAG, context: str = ".") -> None:
    """Build the Docker image for GenCore."""
    logger.info("Building GenCore Docker image %s from %s...", tag, context)
    build = subprocess.run(
        ["docker", "build", "-t", tag, context],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(build, "Build GenCore Docker Image")


def deploy_gencore(
    workdir: str = DEFAULT_WORKDIR,
    compose_file: str = DEFAULT_COMPOSE_FILE,
    k8s_file: str = DEFAULT_K8S_FILE,
) -> None:
    """Deploy GenCore using Docker Compose and Kubernetes."""
    logger.info("Deploying GenCore environment...")
    os.chdir(workdir)
    deploy = subprocess.run(
        ["docker-compose", "-f", compose_file, "up", "-d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(deploy, "GenCore Deployment")

    kubectl = subprocess.run(
        ["kubectl", "apply", "-f", k8s_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(kubectl, "Kubernetes Deployment")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build and deploy the GenCore AI/OS using Docker and Kubernetes."
    )
    parser.add_argument("--tag", default=DEFAULT_TAG, help="Docker image tag")
    parser.add_argument(
        "--context", default=".", help="Path to Docker build context"
    )
    parser.add_argument(
        "--compose-file",
        default=DEFAULT_COMPOSE_FILE,
        help="Docker Compose file to use",
    )
    parser.add_argument(
        "--k8s-file",
        default=DEFAULT_K8S_FILE,
        help="Kubernetes manifest to apply",
    )
    parser.add_argument(
        "--workdir",
        default=DEFAULT_WORKDIR,
        help="Working directory for GenCore",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build the Docker image",
    )
    parser.add_argument(
        "--deploy-only",
        action="store_true",
        help="Only deploy existing images",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    require_tools(["docker", "docker-compose", "kubectl"])
    prepare_environment(args.workdir)

    if not args.deploy_only:
        build_image(args.tag, args.context)

    if not args.build_only:
        deploy_gencore(args.workdir, args.compose_file, args.k8s_file)


if __name__ == "__main__":
    main()
