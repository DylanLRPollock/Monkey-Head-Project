#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Uninstall shell script (huey/memory/SH)

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
    Linux*)  UNINSTALL_SCRIPT="$SCRIPT_DIR/../../../../platform/installers/debian/Debian/uninstall-deb.sh" ;;
    Darwin*) UNINSTALL_SCRIPT="$SCRIPT_DIR/setup/macOS/uninstall.sh" ;;
    *)
        echo "Unsupported operating system" >&2
        exit 1
        ;;
esac
"$UNINSTALL_SCRIPT"
