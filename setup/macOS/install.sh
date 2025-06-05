#!/bin/bash

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
}

install_homebrew
install_packages
setup_python_env

echo "Installation completed successfully."
