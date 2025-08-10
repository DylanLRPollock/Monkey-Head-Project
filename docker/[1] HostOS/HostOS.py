#!/usr/bin/env python3
# ==================================================
# Monkey Head Project - HostOS Orchestrator
# Overseen By: Dylan L.R. Pollock
# Updated: 2025-08-09
# ==================================================
import argparse
import os
import shutil
import logging
import subprocess
import sys
from pathlib import Path

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


def run(cmd, check=True, **popen_kwargs):
    log.debug("→ %s", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **popen_kwargs)
    if proc.returncode != 0 and check:
        log.error("Command failed: %s\nstdout:\n%s\nstderr:\n%s", " ".join(cmd), proc.stdout, proc.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)} (code {proc.returncode})")
    return proc


def is_debian_trixie():
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
        return "debian" in content and any(k in content for k in ("trixie", "testing"))
    except Exception:
        return False


def ensure_system_requirements(skip_os_check=False):
    log.info("Performing system checks for HostOS…")
    if not skip_os_check and not is_debian_trixie():
        raise RuntimeError("Debian Trixie/Testing not detected. Set --skip-os-check to bypass.")

    # Disk space on /
    usage = shutil.disk_usage("/")
    free_gib = usage.free / (1024 ** 3)
    log.info("Free space on /: %.2f GiB", free_gib)

    # Internet connectivity (try multiple targets)
    for host in ("1.1.1.1", "8.8.8.8", "google.com"):
        try:
            proc = run(["ping", "-c", "1", "-W", "2", host], check=False)
            if proc.returncode == 0:
                log.info("Internet OK via %s", host)
                break
        except Exception:
            pass
    else:
        raise RuntimeError("Internet connectivity check failed.")

    # Git availability quick check
    if shutil.which("git") is None:
        log.warning("git not found; will be installed in setup phase.")


def apt_install():
    log.info("Installing HostOS tools via apt…")
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "--no-install-recommends"] + REQUIRED_APT)


def enable_services():
    log.info("Enabling and starting Docker…")
    if shutil.which("systemctl"):
        run(["sudo", "systemctl", "enable", "--now", "docker"])
    else:
        # Fallback for non-systemd
        run(["sudo", "service", "docker", "start"], check=False)

    # Add current user to docker group so `docker` works without sudo next session
    try:
        run(["sudo", "usermod", "-aG", "docker", os.getlogin()], check=False)
    except Exception:
        pass


def check_virtualization():
    log.info("Checking virtualization support…")
    flags = ""
    try:
        flags = run(["bash", "-lc", "egrep -o 'vmx|svm' /proc/cpuinfo | sort -u | tr '\\n' ' '"], check=False).stdout.strip()
    except Exception:
        pass
    kvm_ok = Path("/dev/kvm").exists()
    if not flags and not kvm_ok:
        raise RuntimeError("Virtualization not detected (no vmx/svm and /dev/kvm missing).")
    log.info("Virtualization flags: %s | /dev/kvm: %s", flags or "none", "present" if kvm_ok else "absent")


def configure_firewall(port: int):
    if shutil.which("ufw") is None:
        log.warning("ufw not installed; skipping firewall configuration.")
        return
    log.info("Configuring UFW: allow %d", port)
    run(["sudo", "ufw", "allow", str(port)], check=False)


def ensure_workspace(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    bashrc = Path.home() / ".bashrc"
    export_line = f"\nexport HOSTOS_PATH={str(path)}\n"
    try:
        content = bashrc.read_text()
        if "HOSTOS_PATH" not in content:
            bashrc.write_text(content + export_line)
    except FileNotFoundError:
        bashrc.write_text(export_line)


def deploy_hostos(workspace: Path, kube_manifest: Path):
    log.info("Deploying HostOS from %s …", workspace)
    os.chdir(workspace)

    # docker compose up -d (prefer plugin)
    compose_cmd = ["docker", "compose", "up", "-d"] if shutil.which("docker") else None
    if compose_cmd:
        res = run(compose_cmd, check=False)
        if res.returncode != 0 and shutil.which("docker-compose"):
            run(["docker-compose", "up", "-d"])
    else:
        log.warning("Docker not found; skipping docker compose step.")

    # kubectl apply if available and manifest exists
    if kube_manifest.exists() and shutil.which("kubectl"):
        run(["kubectl", "apply", "-f", str(kube_manifest)])
    elif kube_manifest.exists():
        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)
    else:
        log.info("No Kubernetes manifest found at %s (skipping).", kube_manifest)


def main():
    parser = argparse.ArgumentParser(description="HostOS setup & deployment tool")
    parser.add_argument("--workspace", default=str(Path.home()/ "HostOS"), help="Workspace directory (default: ~/HostOS)")
    parser.add_argument("--vnc-port", type=int, default=5901, help="Port to open in firewall")
    parser.add_argument("--skip-os-check", action="store_true", help="Bypass Debian Trixie check")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("setup", help="Install packages, enable services, prepare workspace")
    sub.add_parser("deploy", help="Run docker compose and apply HostOS.yaml")
    sub.add_parser("all", help="Run setup then deploy (default)")

    args = parser.parse_args()
    ws = Path(args.workspace)
    kube_manifest = ws / "HostOS.yaml"

    cmd = args.cmd or "all"

    if cmd in ("setup", "all"):
        ensure_system_requirements(skip_os_check=args.skip_os_check)
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
    except Exception as e:
        log.error("HostOS failed: %s", e)
        sys.exit(1)
