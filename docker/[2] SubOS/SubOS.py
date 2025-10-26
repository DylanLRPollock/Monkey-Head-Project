#!/usr/bin/env python3
# ==================================================
# Monkey Head Project - SubOS Orchestrator
# Overseen By: Dylan L.R. Pollock
# Updated: 2025-08-09
# ==================================================
"""SubOS setup and deployment orchestration."""

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
log = logging.getLogger("subos")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator_utils import (  # noqa: E402 - injected path
    apt_install as apt_install_packages,
)
from orchestrator_utils import (
    configure_firewall,
    enable_services,
)
from orchestrator_utils import (
    ensure_system_requirements as utils_ensure_system_requirements,
)
from orchestrator_utils import ensure_workspace as utils_ensure_workspace
from orchestrator_utils import (
    run,
)

REQUIRED_APT = [
    "git",
    "docker.io",
    "docker-compose-plugin",
    "python3",
    "python3-venv",
    "curl",
]
SUPPORTED_OS = ["debian trixie", "debian testing", "debian bookworm", "debian stable"]
DEFAULT_SERVICE_PORT = 8080


def ensure_system_requirements(
    *,
    skip_os_check: bool = False,
    allowed_overrides: Iterable[str] | None = None,
    min_free_gib: float = 8.0,
) -> None:
    allowed = SUPPORTED_OS + list(allowed_overrides or [])
    utils_ensure_system_requirements(
        logger=log,
        skip_os_check=skip_os_check,
        allowed_distros=allowed,
        required_commands=("git", "docker"),
        min_free_gib=min_free_gib,
    )


def apt_install() -> None:
    log.info("Installing SubOS tools…")
    apt_install_packages(REQUIRED_APT, log)


def ensure_workspace(path: Path) -> None:
    utils_ensure_workspace(path, "SUBOS_PATH", log)


def deploy_subos(workspace: Path, kube_manifest: Path) -> None:
    log.info("Deploying SubOS from %s", workspace)
    os.chdir(workspace)

    if shutil.which("docker"):
        res = run(["docker", "compose", "up", "-d"], log, check=False)
        if res.returncode != 0 and shutil.which("docker-compose"):
            run(["docker-compose", "up", "-d"], log)
    else:
        log.warning("Docker not found; skipping docker compose step.")

    if kube_manifest.exists() and shutil.which("kubectl"):
        run(["kubectl", "apply", "-f", str(kube_manifest)], log)
    elif kube_manifest.exists():
        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="SubOS setup & deployment")
    parser.add_argument("--workspace", default=str(Path.home() / "SubOS"))
    parser.add_argument("--service-port", type=int, default=DEFAULT_SERVICE_PORT)
    parser.add_argument("--skip-os-check", action="store_true")
    parser.add_argument(
        "--allow-os",
        action="append",
        default=[],
        help="Additional OS release strings to accept (case-insensitive)",
    )
    parser.add_argument(
        "--min-free-gib",
        type=float,
        default=8.0,
        help="Minimum recommended free space on / in GiB",
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("setup")
    sub.add_parser("deploy")
    sub.add_parser("all")

    args = parser.parse_args()
    ws = Path(args.workspace)
    kube_manifest = ws / "SubOS.yaml"
    cmd = args.cmd or "all"

    if cmd in ("setup", "all"):
        ensure_system_requirements(
            skip_os_check=args.skip_os_check,
            allowed_overrides=args.allow_os,
            min_free_gib=args.min_free_gib,
        )
        apt_install()
        enable_services(log)
        configure_firewall(args.service_port, log)
        ensure_workspace(ws)

    if cmd in ("deploy", "all"):
        deploy_subos(ws, kube_manifest)

    log.info("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pragma: no cover - CLI tool
        log.error("SubOS failed: %s", e)
        sys.exit(1)
