#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run shell script (huey/memory/SH)

set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.09.2025
# ==================================================
# This script is used to run the app using the virtual environment
cd "$(dirname "$0")" || exit 1
if [ ! -f "venv/bin/activate" ]; then
  echo "Virtual environment not found. Please run install.sh first." >&2
  exit 1
fi
source ./venv/bin/activate
python3 run.py "$@"
