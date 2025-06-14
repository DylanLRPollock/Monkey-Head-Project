#!/usr/bin/env bash
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
INSTALL_DIR="/Applications/MonkeyHeadProject"

# Virtual environment path
VENV_DIR="$INSTALL_DIR/venv"

function command_exists() {
    command -v "$1" >/dev/null 2>&1
}

function remove_packages() {
    if command_exists brew; then
        echo "Removing Homebrew packages..."
        brew uninstall git python docker || true
        brew cleanup || true
    fi
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

remove_python_env
remove_packages
cleanup_docker
remove_install_dir

echo "Uninstallation completed successfully."
