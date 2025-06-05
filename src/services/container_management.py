import logging
import os
import subprocess

from core.system_checks import check_error

logger = logging.getLogger(__name__)


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
