# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Legacy container management import path

"""Compatibility re-exports for the canonical guarded container helpers."""

from __future__ import annotations

from huey.services.container_management import (
    DEFAULT_K8S_MANIFEST,
    build_docker_image,
    cleanup_images,
    cleanup_kubernetes,
    deploy_kubernetes,
    get_container_logs,
    get_pod_logs,
    kubernetes_management,
    list_containers,
    manage_containers,
    manage_networks,
    manage_volumes,
    scale_deployment,
    stop_containers,
)

K8S_MANIFEST = str(DEFAULT_K8S_MANIFEST)

__all__ = [
    "K8S_MANIFEST",
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
