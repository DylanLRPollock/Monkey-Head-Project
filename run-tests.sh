#!/usr/bin/env bash
set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.09.2025
# ==================================================
# This script is used to run the tests using the virtual environment
if [ ! -f "venv/bin/activate" ]; then
  echo "Virtual environment not found. Please run install.sh first." >&2
  exit 1
fi

LOG_DIR="logs"
LOG_FILE="$LOG_DIR/test_results.log"
mkdir -p "$LOG_DIR"
echo "Test run started at $(date)" | tee "$LOG_FILE"

source ./venv/bin/activate
pytest -vv --cov=monkey_head --cov-report=term | tee -a "$LOG_FILE"
