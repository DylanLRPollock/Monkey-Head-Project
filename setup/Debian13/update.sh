#!/bin/bash

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
source $VENV_DIR/bin/activate || error_exit "Failed to activate virtual environment."

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip || error_exit "Failed to upgrade pip."

# Update dependencies
echo "Updating dependencies..."
pip install --upgrade -r requirements.txt || error_exit "Failed to update dependencies."

echo "Update completed successfully."
