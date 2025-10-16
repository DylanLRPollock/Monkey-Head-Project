#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Install shell script (huey/memory/SH)

set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.11.2025
# ==================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname)" in
    Linux*)  INSTALL_SCRIPT="$SCRIPT_DIR/setup/Debian13/install.sh" ;;
    Darwin*) INSTALL_SCRIPT="$SCRIPT_DIR/setup/macOS/install.sh" ;;
    *)
        echo "Unsupported operating system" >&2
        exit 1
        ;;
esac

cd "$SCRIPT_DIR" || exit 1
if [ ! -f "$INSTALL_SCRIPT" ]; then
    echo "Installation script not found: $INSTALL_SCRIPT" >&2
    exit 1
fi
bash "$INSTALL_SCRIPT"
echo ""
echo "***********************************************"
echo "  Thank you for supporting the Monkey Head Project!"
echo "  We hope you enjoy using it."
echo "***********************************************"
