#!/bin/bash
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.05.2025
# ==================================================
set -e
VENV_DIR="venv"

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

remove_python_env
remove_packages
cleanup_docker

echo "Uninstallation completed successfully."
