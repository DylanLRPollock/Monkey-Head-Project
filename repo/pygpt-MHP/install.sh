#!/usr/bin/env bash
set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.07.2025
# ==================================================
# This script is used to install the app dependencies and run the app using the virtual environment
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
python3 run.py "$@"
