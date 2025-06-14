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
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$(uname)" in
    Linux*)  UNINSTALL_SCRIPT="$SCRIPT_DIR/setup/Debian13/uninstall.sh" ;;
    Darwin*) UNINSTALL_SCRIPT="$SCRIPT_DIR/setup/macOS/uninstall.sh" ;;
    *)
        echo "Unsupported operating system" >&2
        exit 1
        ;;
esac
"$UNINSTALL_SCRIPT"
