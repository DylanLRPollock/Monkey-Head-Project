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

# Application install location
INSTALL_DIR="/Applications/MonkeyHeadProject"

# Virtual environment inside the install directory
VENV_DIR="$INSTALL_DIR/venv"

function command_exists() {
    command -v "$1" >/dev/null 2>&1
}

function copy_project_files() {
    if [ "$PROJECT_ROOT" != "$INSTALL_DIR" ]; then
        echo "Copying project files to $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR" || exit 1
        rsync -a --exclude 'venv' "$PROJECT_ROOT/" "$INSTALL_DIR/" || exit 1
        PROJECT_ROOT="$INSTALL_DIR"
        cd "$PROJECT_ROOT" || exit 1
    fi
}

function install_homebrew() {
    if ! command_exists brew; then
        echo "Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "Homebrew already installed."
    fi
}

function install_packages() {
    echo "Installing required packages..."
    brew update
    brew install git python docker || true
}

function setup_python_env() {
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo "Upgrading pip..."
    pip install --upgrade pip
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Installing local pygpt-MHP package..."
    pip install -e repo/pygpt-MHP
}

function show_license_gui() {
    echo "Displaying license agreement..."
    source "$VENV_DIR/bin/activate"
    python src/license_gui.py || echo "License dialog could not be displayed"
}

function update_submodules() {
    echo "Initializing git submodules..."
    git submodule update --init --recursive
}

install_homebrew
copy_project_files
install_packages
update_submodules
setup_python_env
show_license_gui

function preload_data() {
    echo "Preloading bundled data..."
    source "$VENV_DIR/bin/activate"
    python -m monkey_head.scripts.preload_data --summary || echo "Data preload failed"
}

preload_data

echo "Installation completed successfully."
