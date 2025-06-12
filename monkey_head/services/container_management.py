# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.09.2025
# ==================================================
import os
import subprocess
from ..utils.logger import get_logger

from ..core.system_checks import check_error

logger = get_logger(__name__)


def manage_containers():
    logger.info("Managing Containers...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    start_containers = subprocess.run(
        ["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(start_containers, "Start Docker Containers")

    list_containers = subprocess.run(
        ["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(list_containers, "List Running Containers")


def manage_volumes():
    logger.info("Managing Volumes...")
    list_volumes = subprocess.run(
        ["docker", "volume", "ls"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(list_volumes, "List Docker Volumes")

    prune_volumes = subprocess.run(
        ["docker", "volume", "prune", "-f"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(prune_volumes, "Prune Docker Volumes")


def deploy_kubernetes():
    logger.info("Deploying with Kubernetes...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    deploy = subprocess.run(
        ["kubectl", "apply", "-f", "deployment.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(deploy, "Deploy Kubernetes Resources")

    get_pods = subprocess.run(
        ["kubectl", "get", "pods"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(get_pods, "Get Kubernetes Pods")


def kubernetes_management():
    logger.info("Managing Kubernetes...")
    get_nodes = subprocess.run(
        ["kubectl", "get", "nodes"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(get_nodes, "Get Kubernetes Nodes")

    get_services = subprocess.run(
        ["kubectl", "get", "services"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    check_error(get_services, "Get Kubernetes Services")


def cleanup_kubernetes(manifest: str = "deployment.yaml") -> None:
    """Delete resources defined in the given manifest."""
    logger.info("Cleaning up Kubernetes resources...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    delete = subprocess.run(
        ["kubectl", "delete", "-f", manifest],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(delete, "Delete Kubernetes Resources")


def scale_deployment(name: str, replicas: int) -> None:
    """Scale a deployment to the specified replica count."""
    logger.info("Scaling deployment %s to %d replicas...", name, replicas)
    scale = subprocess.run(
        ["kubectl", "scale", "deployment", name, f"--replicas={replicas}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(scale, "Scale Kubernetes Deployment")


def get_pod_logs(pod_name: str) -> str:
    """Return logs for the specified pod."""
    logger.info("Fetching logs for pod %s...", pod_name)
    logs = subprocess.run(
        ["kubectl", "logs", pod_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(logs, "Get Pod Logs")
    return logs.stdout.decode()


def build_docker_image(tag: str = "monkey-head-project:latest") -> None:
    """Build the project's Docker image."""
    logger.info("Building Docker image %s...", tag)
    build = subprocess.run(
        ["docker", "build", "-t", tag, "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(build, "Build Docker Image")


def stop_containers() -> None:
    """Stop and remove running containers."""
    logger.info("Stopping Docker containers...")
    os.chdir(os.path.expanduser("~/Source/repo"))
    stop = subprocess.run(
        ["docker-compose", "down"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(stop, "Stop Docker Containers")


def cleanup_images() -> None:
    """Remove dangling Docker images."""
    logger.info("Pruning unused Docker images...")
    prune_images = subprocess.run(
        ["docker", "image", "prune", "-f"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(prune_images, "Prune Docker Images")


def manage_networks() -> None:
    """List and prune Docker networks."""
    logger.info("Managing Docker networks...")
    list_networks = subprocess.run(
        ["docker", "network", "ls"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(list_networks, "List Docker Networks")

    prune_networks = subprocess.run(
        ["docker", "network", "prune", "-f"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    check_error(prune_networks, "Prune Docker Networks")
