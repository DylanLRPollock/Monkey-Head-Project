#!/bin/bash

# Define the directory for the virtual environment
VENV_DIR="venv"

# Function to display error messages
function error_exit {
    echo "$1" 1>&2
    exit 1
}

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    error_exit "Python3 is not installed. Please install Python3 and try again."
fi

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv $VENV_DIR || error_exit "Failed to create virtual environment."

# Activate the virtual environment
source $VENV_DIR/bin/activate || error_exit "Failed to activate virtual environment."

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip || error_exit "Failed to upgrade pip."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt || error_exit "Failed to install dependencies."

echo "Installation completed successfully."
