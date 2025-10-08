"""Utility helpers for orchestrating external container and cluster tooling."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

LOGGER = logging.getLogger(__name__)

DEFAULT_K8S_MANIFEST = Path("k8s") / "deployment.yaml"


def _project_root() -> Path:
    env = os.getenv("MONKEY_HEAD_WORKDIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def _run_command(command: Iterable[str], description: str, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
    command = list(command)
    LOGGER.info("%s", description)
    if cwd is None:
        cwd = _project_root()
    executable = command[0]
    if shutil.which(executable) is None:
        LOGGER.warning("Skipping '%s' because the executable is not available.", " ".join(command))
        return subprocess.CompletedProcess(command, 0, b"", b"")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        LOGGER.error(
            "Command '%s' failed with exit code %s", " ".join(command), result.returncode
        )
    else:
        LOGGER.debug("Command '%s' completed successfully", " ".join(command))
    return result


def build_docker_image(tag: str = "monkey-head-project:latest") -> None:
    """Build the project's Docker image if Docker is available."""

    _run_command(["docker", "build", "-t", tag, "."], "Building Docker image")


def manage_containers() -> None:
    """Start the docker-compose stack for the project."""

    workdir = _project_root()
    _run_command(
        ["docker-compose", "up", "-d"], "Starting Docker containers", cwd=workdir
    )
    _run_command(["docker", "ps"], "Listing running containers", cwd=workdir)


def stop_containers() -> None:
    """Stop the docker-compose stack for the project."""

    workdir = _project_root()
    _run_command(["docker-compose", "down"], "Stopping Docker containers", cwd=workdir)


def cleanup_images() -> None:
    """Remove dangling Docker images to free space."""

    _run_command(["docker", "image", "prune", "-f"], "Pruning Docker images")


def manage_volumes() -> None:
    """List and prune Docker volumes."""

    _run_command(["docker", "volume", "ls"], "Listing Docker volumes")
    _run_command(["docker", "volume", "prune", "-f"], "Pruning Docker volumes")


def manage_networks() -> None:
    """List and prune Docker networks."""

    _run_command(["docker", "network", "ls"], "Listing Docker networks")
    _run_command(["docker", "network", "prune", "-f"], "Pruning Docker networks")


def _manifest_path(manifest: str | Path | None = None) -> Path:
    if manifest is None:
        manifest = DEFAULT_K8S_MANIFEST
    manifest_path = Path(manifest)
    if not manifest_path.is_absolute():
        manifest_path = _project_root() / manifest_path
    return manifest_path


def deploy_kubernetes(manifest: str | Path | None = None) -> None:
    """Apply the Kubernetes manifests to the current cluster."""

    manifest_path = _manifest_path(manifest)
    _run_command(
        ["kubectl", "apply", "-f", str(manifest_path)],
        f"Deploying Kubernetes resources from {manifest_path}",
    )
    _run_command(["kubectl", "get", "pods"], "Fetching Kubernetes pods")


def cleanup_kubernetes(manifest: str | Path | None = None) -> None:
    """Delete resources defined by the Kubernetes manifest."""

    manifest_path = _manifest_path(manifest)
    _run_command(
        ["kubectl", "delete", "-f", str(manifest_path)],
        f"Cleaning up Kubernetes resources from {manifest_path}",
    )


def scale_deployment(name: str, replicas: int) -> None:
    """Scale a deployment to the given number of replicas."""

    _run_command(
        ["kubectl", "scale", "deployment", name, f"--replicas={replicas}"],
        f"Scaling deployment {name} to {replicas} replicas",
    )


def kubernetes_management() -> None:
    """Inspect cluster resources such as nodes and services."""

    _run_command(["kubectl", "get", "nodes"], "Listing Kubernetes nodes")
    _run_command(["kubectl", "get", "services"], "Listing Kubernetes services")


def list_containers() -> str:
    """Return the output of ``docker ps`` if Docker is available."""

    result = _run_command(["docker", "ps"], "Listing Docker containers")
    return (result.stdout or b"").decode()


def get_container_logs(container_name: str) -> str:
    """Return logs for the specified Docker container."""

    result = _run_command(
        ["docker", "logs", container_name],
        f"Fetching logs for container {container_name}",
    )
    return (result.stdout or b"").decode()


def get_pod_logs(pod_name: str) -> str:
    """Return logs for the specified Kubernetes pod."""

    result = _run_command(
        ["kubectl", "logs", pod_name],
        f"Fetching logs for pod {pod_name}",
    )
    return (result.stdout or b"").decode()


__all__ = [
    "build_docker_image",
    "cleanup_images",
    "cleanup_kubernetes",
    "deploy_kubernetes",
    "get_container_logs",
    "get_pod_logs",
    "kubernetes_management",
    "list_containers",
    "manage_containers",
    "manage_networks",
    "manage_volumes",
    "scale_deployment",
    "stop_containers",
]
