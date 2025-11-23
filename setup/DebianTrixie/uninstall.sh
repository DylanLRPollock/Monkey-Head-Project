#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Uninstall shell script (setup/DebianTrixie)

set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.11.2025
# ==================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Installation directory
INSTALL_DIR="/opt/hueyos"

# Virtual environment inside the installation directory
VENV_DIR="$INSTALL_DIR/venv"

function error_exit() {
    echo "$1" >&2
    exit 1
}

function ensure_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script with sudo or as root." >&2
        exit 1
    fi
}

function remove_packages() {
    echo "Removing packages..."
    apt-get remove -y git nodejs python3 docker.io || true
    apt-get autoremove -y || true
}

function remove_python_env() {
    if [ -d "$VENV_DIR" ]; then
        echo "Removing virtual environment..."
        rm -rf "$VENV_DIR"
    fi
}

function cleanup_docker() {
    echo "Cleaning up Docker..."
    docker system prune -a -f --volumes || true
}

function remove_install_dir() {
    if [ -d "$INSTALL_DIR" ]; then
        echo "Removing installed files..."
        rm -rf "$INSTALL_DIR"
    fi
}

ensure_root
remove_python_env
remove_packages
cleanup_docker
remove_install_dir

echo "Uninstallation completed successfully."
