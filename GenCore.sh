#!/bin/bash
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.11.2025
# ==================================================
# GenCore.sh - Prepare a Debian Trixie environment and
# auto-install the Monkey Head Project for running Huey

set -e

REPO_URL="https://github.com/DylanLRPollock/Monkey-Head-Project.git"
INSTALL_DIR="/opt/monkey_head"
DEFAULT_PACKAGES="git nodejs python3 python3-venv docker.io mate-desktop-environment-core"

function ensure_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script as root." >&2
        exit 1
    fi
}

function update_system() {
    echo "Updating system to Debian Trixie..."
    python3 "$(dirname "$0")/scripts/update_sources_to_trixie.py" || true
    apt-get update -y
    apt-get upgrade -y
}

function install_packages() {
    echo "Installing required packages: $DEFAULT_PACKAGES"
    apt-get install -y $DEFAULT_PACKAGES
}

function clone_repo() {
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        echo "Cloning Monkey Head Project into $INSTALL_DIR..."
        rm -rf "$INSTALL_DIR"
        git clone --recurse-submodules "$REPO_URL" "$INSTALL_DIR"
    else
        echo "Repository already exists, updating..."
        git -C "$INSTALL_DIR" pull
        git -C "$INSTALL_DIR" submodule update --init --recursive
    fi
}

function run_installer() {
    echo "Running project installer..."
    cd "$INSTALL_DIR"
    MHP_SOFTWARE=auto bash install.sh
}

ensure_root
update_system
install_packages
clone_repo
run_installer

echo "GenCore setup completed successfully."

