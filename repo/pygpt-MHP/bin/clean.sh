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
# This script is used to recursive remove the __pycache__ directories

cd "$(dirname "$0")" || exit
DIR_CURRENT="$(pwd)"
DIR_PARENT="$(dirname "$DIR_CURRENT")"
TARGET_DIR="$DIR_PARENT/src" # clear '__pycache__'

find "$TARGET_DIR" -type d -name "__pycache__" | while read -r dir
do
    echo "Removing $dir"
    rm -rf "${dir}"
done
