#!/usr/bin/env python3
# ==================================================
# Monkey Head Project - NanoOS Orchestrator
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("nanoos")

REQUIRED_APT = [
    "git",
    "docker.io",
    "docker-compose-plugin",
    "python3",
    "python3-venv",
    "curl"
]


def run(cmd, check=True):
    log.debug("→ %s", " ".join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 and check:
        log.error("Command failed: %s\nstdout:\n%s\nstderr:\n%s", " ".join(cmd), p.stdout, p.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)} (code {p.returncode})")
    return p


def is_debian_trixie():
    try:
        with open("/etc/os-release") as f:
            content = f.read().lower()
        return "debian" in content and any(k in content for k in ("trixie", "testing"))
    except Exception:
        return False


def ensure_system(skip_os_check=False):
    log.info("Checking system requirements…")
    if not skip_os_check and not is_debian_trixie():
        raise RuntimeError("Debian Trixie/Testing not detected. Use --skip-os-check to bypass.")
    usage = shutil.disk_usage("/")
    log.info("Free space on /: %.2f GiB", usage.free / (1024 ** 3))
    # basic connectivity
    run(["ping", "-c", "1", "-W", "2", "1.1.1.1"], check=False)
    if shutil.which("git") is None:
        log.warning("git not found; will be installed.")


def apt_install():
    log.info("Installing NanoOS tools…")
    run(["sudo", "apt-get", "update"])
    run(["sudo", "apt-get", "install", "-y", "--no-install-recommends"] + REQUIRED_APT)


def ensure_workspace(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    bashrc = Path.home() / ".bashrc"
    export_line = f"\nexport NANOOS_PATH={str(path)}\n"
    try:
        content = bashrc.read_text()
        if "NANOOS_PATH" not in content:
            bashrc.write_text(content + export_line)
    except FileNotFoundError:
        bashrc.write_text(export_line)


def deploy_nanoos(workspace: Path, kube_manifest: Path):
    log.info("Deploying NanoOS from %s", workspace)
    os.chdir(workspace)
    # Prefer modern docker compose plugin
    res = run(["docker", "compose", "up", "-d"], check=False)
    if res.returncode != 0 and shutil.which("docker-compose"):
        run(["docker-compose", "up", "-d"])
    # Apply Kubernetes manifest if available
    if kube_manifest.exists() and shutil.which("kubectl"):
        run(["kubectl", "apply", "-f", str(kube_manifest)], check=False)


def main():
    p = argparse.ArgumentParser(description="NanoOS setup & deployment")
    p.add_argument("--workspace", default=str(Path.home()/ "NanoOS"))
    p.add_argument("--skip-os-check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("setup")
    sub.add_parser("deploy")
    sub.add_parser("all")
    args = p.parse_args()
    ws = Path(args.workspace)
    kube_manifest = ws / "NanoOS.yaml"
    cmd = args.cmd or "all"
    if cmd in ("setup", "all"):
        ensure_system(skip_os_check=args.skip_os_check)
        apt_install()
        ensure_workspace(ws)
    if cmd in ("deploy", "all"):
        deploy_nanoos(ws, kube_manifest)
    log.info("Done.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("NanoOS failed: %s", e)
        sys.exit(1)
