#!/usr/bin/env bash
# HueyOS Debian Forky Updater Script
#
# Part of the Monkey Head Project
# Author: Dylan L.R. Pollock
#
# Website: https://dlrp.ca
# Source:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License: GPL-3.0-only
# Last-Updated: 2026-01-05
#
# Description:
#   Updates HueyOS components on Debian Forky.

set -euo pipefail

# Define the directory for the virtual environment
VENV_DIR="venv"

# Function to display error messages
function error_exit {
    echo "$1" 1>&2
    exit 1
}

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    error_exit "Virtual environment not found. Please run the installation script first."
fi

# Activate the virtual environment
source "$VENV_DIR"/bin/activate || error_exit "Failed to activate virtual environment."

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip || error_exit "Failed to upgrade pip."

# Update dependencies
echo "Updating dependencies..."
pip install --upgrade -r requirements.txt || error_exit "Failed to update dependencies."

echo "Update completed successfully."
