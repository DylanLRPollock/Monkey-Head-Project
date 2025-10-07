#!/usr/bin/env python3
# ==================================================
# Monkey Head Project - NanoOS Orchestrator
# Overseen By: Dylan L.R. Pollock
# Updated: 2025-08-09
# ==================================================
import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

UTILS_ROOT = Path(__file__).resolve().parents[1]
if str(UTILS_ROOT) not in sys.path:
    sys.path.insert(0, str(UTILS_ROOT))

from orchestrator_utils import (
    apt_install,
    configure_firewall,
    ensure_system_requirements,
    ensure_workspace,
    run,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("nanoos")

REQUIRED_APT = [
    "git",
    "docker.io",
    "docker-compose-plugin",
    "python3",
    "python3-venv",
    "curl",
]

DEFAULT_ALLOWED_DISTROS = [
    "debian:trixie",
    "debian:testing",
    "debian:bookworm",
    "debian:stable",
]


def deploy_nanoos(workspace: Path, kube_manifest: Path):
    log.info("Deploying NanoOS from %s", workspace)
    os.chdir(workspace)
    # Prefer modern docker compose plugin
    res = run(["docker", "compose", "up", "-d"], check=False, logger=log)
    if res.returncode != 0 and shutil.which("docker-compose"):
        run(["docker-compose", "up", "-d"], logger=log)
    if kube_manifest.exists() and shutil.which("kubectl"):
        run(["kubectl", "apply", "-f", str(kube_manifest)], check=False, logger=log)


def main():
    p = argparse.ArgumentParser(description="NanoOS setup & deployment")
    p.add_argument("--workspace", default=str(Path.home() / "NanoOS"))
    p.add_argument("--skip-os-check", action="store_true")
    p.add_argument(
        "--allow-distro",
        action="append",
        dest="allowed_distros",
        help="Additional distribution identifiers to allow (format distro:codename)",
    )
    p.add_argument(
        "--service-port",
        type=int,
        default=8081,
        help="Service port to permit via UFW (default: 8081)",
    )
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("setup")
    sub.add_parser("deploy")
    sub.add_parser("all")
    args = p.parse_args()
    ws = Path(args.workspace)
    kube_manifest = ws / "NanoOS.yaml"
    cmd = args.cmd or "all"
    if cmd in ("setup", "all"):
        allowed = DEFAULT_ALLOWED_DISTROS.copy()
        if args.allowed_distros:
            allowed.extend(args.allowed_distros)
        ensure_system_requirements(
            component_name="NanoOS",
            skip_os_check=args.skip_os_check,
            allowed_distributions=allowed,
            logger=log,
        )
        apt_install(REQUIRED_APT, logger=log)
        ensure_workspace(ws, "NANOOS_PATH", logger=log)
        configure_firewall(args.service_port, comment="NanoOS Services", logger=log)
    if cmd in ("deploy", "all"):
        deploy_nanoos(ws, kube_manifest)
    log.info("Done.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("NanoOS failed: %s", e)
        sys.exit(1)
