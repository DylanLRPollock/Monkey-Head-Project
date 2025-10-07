#!/usr/bin/env python3
# ==================================================
# Monkey Head Project - HostOS Orchestrator
# Overseen By: Dylan L.R. Pollock
# Updated: 2025-08-09
# ==================================================
import argparse
import logging
import os
import platform
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

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("hostos")

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

DEFAULT_ALLOWED_DISTROS = [
    "debian:trixie",
    "debian:testing",
    "debian:bookworm",
    "debian:stable",
]


def enable_services():
    log.info("Enabling and starting Docker…")
    if shutil.which("systemctl"):
        run(["sudo", "systemctl", "enable", "--now", "docker"], logger=log)
    else:
        run(["sudo", "service", "docker", "start"], check=False, logger=log)

    try:
        run(["sudo", "usermod", "-aG", "docker", os.getlogin()], check=False, logger=log)
    except Exception:
        pass


def check_virtualization(skip_check: bool = False) -> None:
    if skip_check:
        log.warning("Skipping virtualization capability verification.")
        return

    log.info("Checking virtualization support…")
    flags = ""
    try:
        flags = (
            run(
                [
                    "bash",
                    "-lc",
                    "egrep -o 'vmx|svm' /proc/cpuinfo | sort -u | tr '\n' ' '",
                ],
                check=False,
                logger=log,
            ).stdout.strip()
        )
    except Exception:
        pass
    kvm_ok = Path("/dev/kvm").exists()
    if not flags and not kvm_ok:
        guidance = [
            "Hardware virtualization was not detected (no vmx/svm CPU flags and /dev/kvm is missing).",
            "Enable virtualization extensions in your BIOS/UEFI or cloud instance settings.",
        ]
        if platform.system() == "Darwin":
            guidance.append(
                "On macOS hosts consider installing QEMU (brew install qemu) and using HVF/TCG acceleration."
            )
        else:
            guidance.append(
                "If hardware acceleration cannot be enabled, use QEMU's software emulation (qemu-system-x86_64 -accel tcg)."
            )
        raise RuntimeError(" ".join(guidance))

    if not kvm_ok:
        log.warning(
            "/dev/kvm is unavailable; KVM acceleration will be disabled. QEMU software emulation will be used instead."
        )

    log.info(
        "Virtualization flags: %s | /dev/kvm: %s",
        flags or "none",
        "present" if kvm_ok else "absent",
    )


def deploy_hostos(workspace: Path, kube_manifest: Path):
    log.info("Deploying HostOS from %s …", workspace)
    os.chdir(workspace)

    # docker compose up -d (prefer plugin)
    compose_cmd = ["docker", "compose", "up", "-d"] if shutil.which("docker") else None
    if compose_cmd:
        res = run(compose_cmd, check=False, logger=log)
        if res.returncode != 0 and shutil.which("docker-compose"):
            run(["docker-compose", "up", "-d"], logger=log)
    else:
        log.warning("Docker not found; skipping docker compose step.")

    # kubectl apply if available and manifest exists
    if kube_manifest.exists() and shutil.which("kubectl"):
        run(["kubectl", "apply", "-f", str(kube_manifest)], logger=log)
    elif kube_manifest.exists():
        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)
    else:
        log.info("No Kubernetes manifest found at %s (skipping).", kube_manifest)


def main():
    parser = argparse.ArgumentParser(description="HostOS setup & deployment tool")
    parser.add_argument("--workspace", default=str(Path.home() / "HostOS"), help="Workspace directory (default: ~/HostOS)")
    parser.add_argument("--vnc-port", type=int, default=5901, help="Port to open in firewall")
    parser.add_argument("--skip-os-check", action="store_true", help="Bypass Debian Trixie check")
    parser.add_argument(
        "--allow-distro",
        action="append",
        dest="allowed_distros",
        help="Additional distribution identifiers to allow (format distro:codename)",
    )
    parser.add_argument(
        "--skip-virtualization-check",
        action="store_true",
        help="Skip virtualization capability validation",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("setup", help="Install packages, enable services, prepare workspace")
    sub.add_parser("deploy", help="Run docker compose and apply HostOS.yaml")
    sub.add_parser("all", help="Run setup then deploy (default)")

    args = parser.parse_args()
    ws = Path(args.workspace)
    kube_manifest = ws / "HostOS.yaml"

    cmd = args.cmd or "all"

    allowed_distros = DEFAULT_ALLOWED_DISTROS.copy()
    if args.allowed_distros:
        allowed_distros.extend(args.allowed_distros)

    if cmd in ("setup", "all"):
        ensure_system_requirements(
            component_name="HostOS",
            skip_os_check=args.skip_os_check,
            allowed_distributions=allowed_distros,
            logger=log,
        )
        apt_install(REQUIRED_APT, logger=log)
        enable_services()
        check_virtualization(skip_check=args.skip_virtualization_check)
        configure_firewall(args.vnc_port, comment="HostOS VNC", logger=log)
        ensure_workspace(ws, "HOSTOS_PATH", logger=log)

    if cmd in ("deploy", "all"):
        deploy_hostos(ws, kube_manifest)

    log.info("Done. You may need to log out/in for docker group to take effect.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("HostOS failed: %s", e)
        sys.exit(1)
