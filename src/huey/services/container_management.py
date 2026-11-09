# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Container Management module (huey/services)

"""Utility helpers for orchestrating external container and cluster tooling."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

from huey.os.core.privileged_operations import authorize_privileged_operation
from huey.os.core.platform_support import find_project_root

LOGGER = logging.getLogger(__name__)

DEFAULT_K8S_MANIFEST = Path("src") / "huey" / "memory" / "YAML" / "deployment.yaml"


def _project_root() -> Path:
    env = os.getenv("MONKEY_HEAD_WORKDIR")
    if env:
        return Path(env).expanduser().resolve()
    return find_project_root(Path(__file__).resolve())


def _run_command(
    command: Iterable[str], description: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[bytes]:
    command = list(command)
    LOGGER.info("%s", description)
    if cwd is None:
        cwd = _project_root()
    executable = command[0]
    if shutil.which(executable) is None:
        LOGGER.warning(
            "Skipping '%s' because the executable is not available.", " ".join(command)
        )
        return subprocess.CompletedProcess(command, 0, b"", b"")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        shell=False,
        timeout=600,
    )
    if result.returncode != 0:
        LOGGER.error(
            "Command '%s' failed with exit code %s",
            " ".join(command),
            result.returncode,
        )
    else:
        LOGGER.debug("Command '%s' completed successfully", " ".join(command))
    return result


def build_docker_image(
    tag: str = "monkey-head-project:latest",
    *,
    confirmed: bool = False,
    actor_role: str | None = None,
    dry_run: bool = False,
) -> None:
    """Build the project's Docker image if Docker is available."""
    if not authorize_privileged_operation(
        "project.container.build", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", tag):
        raise ValueError("Invalid Docker image tag")
    _run_command(["docker", "build", "-t", tag, "."], "Building Docker image")


def manage_containers(
    *, confirmed: bool = False, actor_role: str | None = None, dry_run: bool = False
) -> None:
    """Start the docker-compose stack for the project."""
    if not authorize_privileged_operation(
        "project.container.start", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    workdir = _project_root()
    _run_command(
        ["docker-compose", "up", "-d"], "Starting Docker containers", cwd=workdir
    )
    _run_command(["docker", "ps"], "Listing running containers", cwd=workdir)


def stop_containers(
    *, confirmed: bool = False, actor_role: str | None = None, dry_run: bool = False
) -> None:
    """Stop the docker-compose stack for the project."""
    if not authorize_privileged_operation(
        "project.container.stop", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    workdir = _project_root()
    _run_command(["docker-compose", "down"], "Stopping Docker containers", cwd=workdir)


def cleanup_images(
    *, confirmed: bool = False, actor_role: str | None = None, dry_run: bool = False
) -> None:
    """Remove dangling Docker images to free space."""
    if not authorize_privileged_operation(
        "project.container.cleanup", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    _run_command(["docker", "image", "prune", "-f"], "Pruning Docker images")


def manage_volumes(
    *, confirmed: bool = False, actor_role: str | None = None, dry_run: bool = False
) -> None:
    """List Docker volumes without removing resources."""
    if not authorize_privileged_operation(
        "project.container.volumes", confirmed=confirmed,
        actor_role=actor_role or "reader",
        dry_run=dry_run,
    ):
        return
    _run_command(["docker", "volume", "ls"], "Listing Docker volumes")


def manage_networks(
    *, confirmed: bool = False, actor_role: str | None = None, dry_run: bool = False
) -> None:
    """List Docker networks without removing resources."""
    if not authorize_privileged_operation(
        "project.container.networks", confirmed=confirmed,
        actor_role=actor_role or "reader",
        dry_run=dry_run,
    ):
        return
    _run_command(["docker", "network", "ls"], "Listing Docker networks")


def _manifest_path(manifest: str | Path | None = None) -> Path:
    if manifest is None:
        manifest = DEFAULT_K8S_MANIFEST
    manifest_path = Path(manifest)
    if not manifest_path.is_absolute():
        manifest_path = _project_root() / manifest_path
    return manifest_path


def deploy_kubernetes(
    manifest: str | Path | None = None,
    *,
    confirmed: bool = False,
    actor_role: str | None = None,
    dry_run: bool = False,
) -> None:
    """Apply the Kubernetes manifests to the current cluster."""
    if not authorize_privileged_operation(
        "project.kubernetes.deploy", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    manifest_path = _manifest_path(manifest)
    _validate_manifest_path(manifest_path)
    _run_command(
        ["kubectl", "apply", "-f", str(manifest_path)],
        f"Deploying Kubernetes resources from {manifest_path}",
    )
    _run_command(["kubectl", "get", "pods"], "Fetching Kubernetes pods")


def cleanup_kubernetes(
    manifest: str | Path | None = None,
    *,
    confirmed: bool = False,
    actor_role: str | None = None,
    dry_run: bool = False,
) -> None:
    """Delete resources defined by the Kubernetes manifest."""
    if not authorize_privileged_operation(
        "project.kubernetes.cleanup", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    manifest_path = _manifest_path(manifest)
    _validate_manifest_path(manifest_path)
    _run_command(
        ["kubectl", "delete", "-f", str(manifest_path)],
        f"Cleaning up Kubernetes resources from {manifest_path}",
    )


def scale_deployment(
    name: str,
    replicas: int,
    *,
    confirmed: bool = False,
    actor_role: str | None = None,
    dry_run: bool = False,
) -> None:
    """Scale a deployment to the given number of replicas."""
    if not authorize_privileged_operation(
        "project.kubernetes.scale", confirmed=confirmed, actor_role=actor_role,
        dry_run=dry_run,
    ):
        return
    if not re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", name) or replicas < 0:
        raise ValueError("Invalid Kubernetes deployment name or replica count")
    _run_command(
        ["kubectl", "scale", "deployment", name, f"--replicas={replicas}"],
        f"Scaling deployment {name} to {replicas} replicas",
    )


def _validate_manifest_path(path: Path) -> None:
    root = _project_root().resolve()
    resolved = path.resolve()
    if path.is_symlink() or not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("Kubernetes manifest must be a regular file inside the project")


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
