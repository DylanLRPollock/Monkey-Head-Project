#!/usr/bin/env python3
# ==================================================
# Monkey Head Project - HostOS Orchestrator
# Overseen By: Dylan L.R. Pollock
# Updated: 2025-08-09
# ==================================================
"""HostOS setup and deployment orchestration."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("hostos")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator_utils import (  # noqa: E402 - path injection required
    apt_install as apt_install_packages,
    check_virtualization as utils_check_virtualization,
    configure_firewall as utils_configure_firewall,
    enable_services as utils_enable_services,
    ensure_system_requirements as utils_ensure_system_requirements,
    ensure_workspace as utils_ensure_workspace,
    run,
)

REQUIRED_APT = [
    "git",
    "docker.io",
    "docker-compose-plugin",  # provides `docker compose`
    "python3",
    "python3-venv",
    "qemu-kvm",
    "libvirt-daemon-system",
    "libvirt-clients",
    "curl",
    "ufw",
]
SUPPORTED_OS = ["debian trixie", "debian testing", "debian bookworm", "debian stable"]
DEFAULT_VNC_PORT = 5901


def ensure_system_requirements(
    *,
    skip_os_check: bool = False,
    allowed_overrides: Iterable[str] | None = None,
    min_free_gib: float = 15.0,
) -> None:
    """Validate host prerequisites with shared helper logic."""

    allowed = SUPPORTED_OS + list(allowed_overrides or [])
    utils_ensure_system_requirements(
        logger=log,
        skip_os_check=skip_os_check,
        allowed_distros=allowed,
        required_commands=("git", "docker", "kubectl"),
        min_free_gib=min_free_gib,
    )


def apt_install() -> None:
    """Install apt dependencies required by HostOS."""

    log.info("Installing HostOS tools via apt…")
    apt_install_packages(REQUIRED_APT, log)


def enable_services() -> None:
    """Ensure Docker is ready for HostOS workloads."""

    utils_enable_services(log)


def check_virtualization() -> None:
    """Verify virtualization availability for local emulation."""

    utils_check_virtualization(log)


def configure_firewall(port: int) -> None:
    """Open the VNC port via ufw if available."""

    utils_configure_firewall(port, log)


def ensure_workspace(path: Path) -> None:
    """Create HostOS workspace and expose HOSTOS_PATH."""

    utils_ensure_workspace(path, "HOSTOS_PATH", log)


def deploy_hostos(workspace: Path, kube_manifest: Path) -> None:
    """Run docker compose and apply the HostOS manifest."""

    log.info("Deploying HostOS from %s …", workspace)
    os.chdir(workspace)

    compose_cmd = ["docker", "compose", "up", "-d"] if shutil.which("docker") else None
    if compose_cmd:
        res = run(compose_cmd, log, check=False)
        if res.returncode != 0 and shutil.which("docker-compose"):
            run(["docker-compose", "up", "-d"], log)
    else:
        log.warning("Docker not found; skipping docker compose step.")

    if kube_manifest.exists() and shutil.which("kubectl"):
        run(["kubectl", "apply", "-f", str(kube_manifest)], log)
    elif kube_manifest.exists():
        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)
    else:
        log.info("No Kubernetes manifest found at %s (skipping).", kube_manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="HostOS setup & deployment tool")
    parser.add_argument(
        "--workspace", default=str(Path.home() / "HostOS"), help="Workspace directory"
    )
    parser.add_argument(
        "--vnc-port", type=int, default=DEFAULT_VNC_PORT, help="VNC port to open via ufw"
    )
    parser.add_argument(
        "--skip-os-check",
        action="store_true",
        help="Bypass OS distribution validation",
    )
    parser.add_argument(
        "--allow-os",
        action="append",
        default=[],
        help="Additional OS release strings to accept (case-insensitive)",
    )
    parser.add_argument(
        "--min-free-gib",
        type=float,
        default=15.0,
        help="Minimum recommended free space on / in GiB",
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("setup", help="Install packages, enable services, prepare workspace")
    sub.add_parser("deploy", help="Run docker compose and apply HostOS.yaml")
    sub.add_parser("all", help="Run setup then deploy (default)")

    args = parser.parse_args()
    ws = Path(args.workspace)
    kube_manifest = ws / "HostOS.yaml"
    cmd = args.cmd or "all"

    if cmd in ("setup", "all"):
        ensure_system_requirements(
            skip_os_check=args.skip_os_check,
            allowed_overrides=args.allow_os,
            min_free_gib=args.min_free_gib,
        )
        apt_install()
        enable_services()
        check_virtualization()
        configure_firewall(args.vnc_port)
        ensure_workspace(ws)

    if cmd in ("deploy", "all"):
        deploy_hostos(ws, kube_manifest)

    log.info("Done. You may need to log out/in for docker group to take effect.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pragma: no cover - CLI tool
        log.error("HostOS failed: %s", e)
        sys.exit(1)
