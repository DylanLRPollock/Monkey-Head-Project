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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Install location for the application
INSTALL_DIR="/opt/monkey_head"

# Virtual environment lives inside the install directory
VENV_DIR="$INSTALL_DIR/venv"

function error_exit {
    echo "$1" >&2
    exit 1
}

function ensure_root {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script with sudo or as root." >&2
        exit 1
    fi
}

function copy_project_files {
    if [ "$PROJECT_ROOT" != "$INSTALL_DIR" ]; then
        echo "Copying project files to $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR" || error_exit "Cannot create $INSTALL_DIR"
        rsync -a --exclude 'venv' "$PROJECT_ROOT/" "$INSTALL_DIR/" || \
            error_exit "Failed to copy project files"
        PROJECT_ROOT="$INSTALL_DIR"
        cd "$PROJECT_ROOT" || error_exit "Cannot cd to $PROJECT_ROOT"
    fi
}

function update_system {
    echo "Updating apt sources to Debian Trixie..."
    python3 "$PROJECT_ROOT/scripts/update_sources_to_trixie.py" || error_exit "Failed to update sources list."
    echo "Updating system..."
    apt-get update -y || error_exit "apt-get update failed."
    apt-get upgrade -y || error_exit "apt-get upgrade failed."
}

function install_common_tools {
    echo "Installing common tools..."
    apt-get install -y git nodejs || error_exit "Failed to install common tools."
}

function install_additional_tools {
    echo "Installing additional tools..."
    apt-get install -y python3 python3-venv docker.io || error_exit "Failed to install additional tools."
}

function setup_python_env {
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment."
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment."
    echo "Upgrading pip..."
    pip install --upgrade pip || error_exit "Failed to upgrade pip."
    echo "Installing dependencies..."
    pip install -r requirements.txt || error_exit "Failed to install dependencies."
    echo "Installing local pygpt-MHP package..."
    pip install -e repo/pygpt-MHP || error_exit "Failed to install pygpt-MHP."
}

function show_license_gui {
    echo "Displaying license agreement..."
    source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment."
    python src/license_gui.py || echo "License dialog could not be displayed"
}

function update_submodules {
    echo "Initializing git submodules..."
    git submodule update --init --recursive || error_exit "Failed to update submodules."
}

ensure_root
copy_project_files
update_system
install_common_tools
install_additional_tools
update_submodules
setup_python_env
show_license_gui

function preload_data {
    echo "Preloading bundled data..."
    source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment."
    python -m monkey_head.scripts.preload_data --summary || echo "Data preload failed"
}

preload_data

echo "Installation completed successfully."
