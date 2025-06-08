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
install_packages
update_submodules
setup_python_env
show_license_gui

echo "Installation completed successfully."
