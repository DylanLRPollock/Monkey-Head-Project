#!/bin/bash
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


# Default package list if MHP_SOFTWARE is set to "auto" or empty
DEFAULT_PACKAGES="git build-essential g++ nodejs python3 python3-venv docker.io mate-desktop-environment-core"

function install_selected_packages {
    local packages="${MHP_SOFTWARE:-auto}"
    if [ "$packages" = "auto" ] || [ -z "$packages" ]; then
        packages="$DEFAULT_PACKAGES"
    fi
    echo "Installing packages: $packages..."
    apt-get install -y $packages || error_exit "Failed to install packages."
}

# Remove Firefox and install Microsoft Edge Dev
function install_edge_dev {
    echo "Purging Firefox..."
    apt-get purge -y firefox || true
    apt-get autoremove -y || true
    echo "Adding Microsoft Edge repository..."
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | \
        gpg --dearmor -o microsoft.gpg || error_exit "Failed to download key."
    install -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/ || \
        error_exit "Failed to install key."
    sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list'
    rm -f microsoft.gpg
    apt-get update -y || error_exit "apt-get update failed."
    apt-get install -y microsoft-edge-dev || \
        error_exit "Failed to install Microsoft Edge Dev."
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
install_selected_packages
install_edge_dev
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
echo ""
echo "***********************************************"
echo "  Thank you for supporting the Monkey Head Project!"
echo "  We hope you enjoy using it."
echo "***********************************************"
