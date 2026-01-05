#!/usr/bin/env bash
# HueyOS Debian Forky Uninstaller Script
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
#   Uninstalls HueyOS components on Debian Forky.
#
# Safety notes:
#   - By default, this script removes HueyOS files under /opt/hueyos ONLY.
#   - It will NOT remove system packages (docker/libvirt/etc.) unless you explicitly request it.
#   - Docker pruning is OFF by default because it can delete unrelated images/volumes.

set -Eeuo pipefail

trap 'echo "ERROR: Uninstall failed (line $LINENO)." >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Installation directory (override by exporting INSTALL_DIR before running)
INSTALL_DIR="${INSTALL_DIR:-/opt/hueyos}"

# Virtual environment inside the installation directory
VENV_DIR="$INSTALL_DIR/venv"

# Memory path (override by exporting MEMORY_PATH before running).
# Default matches installer behavior.
MEMORY_PATH="${MEMORY_PATH:-$INSTALL_DIR/memory}"

# Edge repo artifacts created by the installer (only removed if requested)
EDGE_LIST_FILE="/etc/apt/sources.list.d/microsoft-edge-beta.list"
EDGE_KEYRING="/usr/share/keyrings/microsoft.gpg"

export DEBIAN_FRONTEND=noninteractive

# Options
ASSUME_YES=0
DRY_RUN=0
REMOVE_PACKAGES=0
REMOVE_GUI_PACKAGES=0
REMOVE_EDGE=0
REMOVE_EDGE_KEYRING=0
PRUNE_DOCKER=0
KEEP_MEMORY=0
REMOVE_EXTERNAL_MEMORY=0

BASE_PACKAGES_TO_REMOVE=(
    docker.io
    docker-compose-plugin
    qemu-kvm
    libvirt-daemon-system
    libvirt-clients
    python3-venv
    ufw
)

GUI_PACKAGES_TO_REMOVE=(
    mate-desktop-environment-core
)

function usage() {
    cat <<USAGE
Usage: $0 [options]

Default behavior:
  - Removes HueyOS files under INSTALL_DIR (default: /opt/hueyos)
  - Does NOT remove system apt packages
  - Does NOT prune Docker

Options:
  -y, --yes               Run non-interactively (assume "yes" to prompts).
  --dry-run               Print actions without executing them.

  --keep-memory            Preserve MEMORY_PATH. If MEMORY_PATH is inside INSTALL_DIR,
                           this removes everything under INSTALL_DIR except the memory folder.

  --remove-external-memory Delete MEMORY_PATH if it is OUTSIDE INSTALL_DIR.
                           (Guarded to avoid deleting unrelated data by default.)

  --remove-packages        Attempt to remove base packages used by HueyOS
                           (docker/libvirt/venv tooling). Use with care.
  --remove-gui-packages    Also remove GUI packages (Mate desktop core). Requires --remove-packages.

  --remove-edge            Purge Microsoft Edge Beta and remove its apt list file.
  --remove-edge-keyring    Also remove /usr/share/keyrings/microsoft.gpg (may affect other MS repos).

  --prune-docker           Run: docker system prune -a --volumes (VERY destructive).

Environment:
  INSTALL_DIR              Install root (default: /opt/hueyos)
  MEMORY_PATH              Memory directory (default: \$INSTALL_DIR/memory)

Examples:
  sudo ./uninstaller.sh
  sudo ./uninstaller.sh --yes --remove-packages --remove-edge
  sudo MEMORY_PATH=/data/huey/memory ./uninstaller.sh --remove-external-memory

USAGE
}

function error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

function run() {
    if [[ $DRY_RUN -eq 1 ]]; then
        printf 'DRY-RUN:'
        printf ' %q' "$@"
        printf '\n'
        return 0
    fi
    "$@"
}

function ensure_root() {
    if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
        error_exit "Please run this script with sudo or as root."
    fi
}

function parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -y|--yes)
                ASSUME_YES=1
                shift
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            --keep-memory)
                KEEP_MEMORY=1
                shift
                ;;
            --remove-external-memory)
                REMOVE_EXTERNAL_MEMORY=1
                shift
                ;;
            --remove-packages)
                REMOVE_PACKAGES=1
                shift
                ;;
            --remove-gui-packages)
                REMOVE_GUI_PACKAGES=1
                shift
                ;;
            --remove-edge)
                REMOVE_EDGE=1
                shift
                ;;
            --remove-edge-keyring)
                REMOVE_EDGE_KEYRING=1
                shift
                ;;
            --prune-docker)
                PRUNE_DOCKER=1
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

function sanity_check_paths() {
    if [[ -z ${INSTALL_DIR:-} || "$INSTALL_DIR" == "/" ]]; then
        error_exit "Refusing to operate with INSTALL_DIR='$INSTALL_DIR'"
    fi

    # Reduce foot-gun risk: refuse to rm -rf if INSTALL_DIR looks too broad.
    # Allow override only by explicitly setting INSTALL_DIR (already possible),
    # but still require it to be an absolute path.
    if [[ "$INSTALL_DIR" != /* ]]; then
        error_exit "INSTALL_DIR must be an absolute path (got '$INSTALL_DIR')"
    fi

    if [[ "$MEMORY_PATH" != /* ]]; then
        error_exit "MEMORY_PATH must be an absolute path (got '$MEMORY_PATH')"
    fi

    if [[ $REMOVE_GUI_PACKAGES -eq 1 && $REMOVE_PACKAGES -eq 0 ]]; then
        error_exit "--remove-gui-packages requires --remove-packages"
    fi
}

function prompt_confirm() {
    if [[ $ASSUME_YES -eq 1 ]]; then
        return 0
    fi

    # If not a TTY, refuse unless --yes was provided.
    if [[ ! -t 0 ]]; then
        error_exit "Non-interactive shell detected. Re-run with --yes to proceed."
    fi

    echo
    echo "About to uninstall HueyOS with the following plan:"
    echo "  INSTALL_DIR:   $INSTALL_DIR"
    echo "  VENV_DIR:      $VENV_DIR"
    echo "  MEMORY_PATH:   $MEMORY_PATH"
    echo
    echo "Actions:"
    echo "  - Remove HueyOS install files"
    if [[ $KEEP_MEMORY -eq 1 ]]; then
        echo "  - KEEP memory directory"
    else
        echo "  - REMOVE memory directory if it is inside INSTALL_DIR"
    fi
    if [[ $REMOVE_EXTERNAL_MEMORY -eq 1 ]]; then
        echo "  - REMOVE external MEMORY_PATH (if outside INSTALL_DIR)"
    fi
    if [[ $REMOVE_EDGE -eq 1 ]]; then
        echo "  - Remove Microsoft Edge Beta + repo list"
    fi
    if [[ $REMOVE_EDGE_KEYRING -eq 1 ]]; then
        echo "  - Remove Microsoft keyring: $EDGE_KEYRING"
    fi
    if [[ $REMOVE_PACKAGES -eq 1 ]]; then
        echo "  - Attempt apt removal of base packages: ${BASE_PACKAGES_TO_REMOVE[*]}"
    fi
    if [[ $REMOVE_GUI_PACKAGES -eq 1 ]]; then
        echo "  - Attempt apt removal of GUI packages: ${GUI_PACKAGES_TO_REMOVE[*]}"
    fi
    if [[ $PRUNE_DOCKER -eq 1 ]]; then
        echo "  - PRUNE DOCKER: docker system prune -a --volumes"
    fi
    echo

    read -r -p "Proceed? [y/N] " ans
    case "${ans,,}" in
        y|yes) return 0 ;;
        *) error_exit "Aborted by user." ;;
    esac
}

function remove_python_env() {
    if [[ -d "$VENV_DIR" ]]; then
        echo "Removing virtual environment: $VENV_DIR"
        run rm -rf "$VENV_DIR"
    else
        echo "Virtual environment not found at: $VENV_DIR (skipping)"
    fi
}

function remove_edge() {
    if [[ $REMOVE_EDGE -ne 1 ]]; then
        return 0
    fi

    if ! command -v apt-get >/dev/null 2>&1; then
        echo "apt-get not available; cannot remove Edge via apt (skipping)" >&2
    else
        echo "Removing Microsoft Edge Beta package (if installed) ..."
        run apt-get purge -y microsoft-edge-beta || true
    fi

    if [[ -f "$EDGE_LIST_FILE" ]]; then
        echo "Removing Edge apt list: $EDGE_LIST_FILE"
        run rm -f "$EDGE_LIST_FILE"
    else
        echo "Edge apt list not found at: $EDGE_LIST_FILE (skipping)"
    fi

    if [[ $REMOVE_EDGE_KEYRING -eq 1 ]]; then
        if [[ -f "$EDGE_KEYRING" ]]; then
            echo "Removing Microsoft keyring: $EDGE_KEYRING"
            run rm -f "$EDGE_KEYRING"
        else
            echo "Microsoft keyring not found at: $EDGE_KEYRING (skipping)"
        fi
    fi

    if command -v apt-get >/dev/null 2>&1; then
        echo "Refreshing apt metadata ..."
        run apt-get update -y || true
    fi
}

function cleanup_docker() {
    if [[ $PRUNE_DOCKER -ne 1 ]]; then
        return 0
    fi

    if ! command -v docker >/dev/null 2>&1; then
        echo "Docker not installed; skipping prune."
        return 0
    fi

    echo "Pruning Docker (ALL images/containers/volumes not in use will be deleted) ..."
    run docker system prune -a -f --volumes || true
}

function remove_packages() {
    if [[ $REMOVE_PACKAGES -ne 1 ]]; then
        return 0
    fi

    if ! command -v apt-get >/dev/null 2>&1; then
        echo "apt-get not available; skipping package removal." >&2
        return 0
    fi

    echo "Removing HueyOS-related packages (best effort) ..."
    run apt-get remove -y "${BASE_PACKAGES_TO_REMOVE[@]}" || true

    if [[ $REMOVE_GUI_PACKAGES -eq 1 ]]; then
        echo "Removing optional GUI packages (best effort) ..."
        run apt-get remove -y "${GUI_PACKAGES_TO_REMOVE[@]}" || true
    fi

    run apt-get autoremove -y || true
}

function remove_install_dir() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        echo "Install directory not found at: $INSTALL_DIR (skipping)"
        return 0
    fi

    # If KEEP_MEMORY is set and memory is inside INSTALL_DIR, remove everything EXCEPT the memory dir.
    if [[ $KEEP_MEMORY -eq 1 ]]; then
        # Only preserve when the memory path is within INSTALL_DIR and exists.
        if [[ "$MEMORY_PATH" == "$INSTALL_DIR"* && -d "$MEMORY_PATH" ]]; then
            echo "Removing installed files under $INSTALL_DIR (preserving memory: $MEMORY_PATH) ..."
            # Remove everything directly under INSTALL_DIR except the memory directory name.
            local mem_base
            mem_base="$(basename "$MEMORY_PATH")"
            run find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 ! -name "$mem_base" -exec rm -rf {} +
            echo "Preserved memory directory: $MEMORY_PATH"
            return 0
        fi
        echo "KEEP_MEMORY requested, but MEMORY_PATH is not an existing directory under INSTALL_DIR; proceeding with normal uninstall of INSTALL_DIR."
    fi

    echo "Removing installed files: $INSTALL_DIR"
    run rm -rf "$INSTALL_DIR"
}

function remove_external_memory() {
    if [[ $REMOVE_EXTERNAL_MEMORY -ne 1 ]]; then
        return 0
    fi

    # Only remove external memory (outside INSTALL_DIR) to avoid accidental deletion.
    if [[ "$MEMORY_PATH" == "$INSTALL_DIR"* ]]; then
        echo "MEMORY_PATH is inside INSTALL_DIR; external memory removal not applicable (skipping)."
        return 0
    fi

    if [[ -d "$MEMORY_PATH" ]]; then
        echo "Removing external memory directory: $MEMORY_PATH"
        run rm -rf "$MEMORY_PATH"
    else
        echo "External memory directory not found at: $MEMORY_PATH (skipping)"
    fi
}

function main() {
    parse_args "$@"
    ensure_root
    sanity_check_paths
    prompt_confirm

    echo "Starting HueyOS uninstall..."
    echo "PROJECT_ROOT (informational): $PROJECT_ROOT"

    # Order: stop depending components first, then remove files, then optional system-level cleanup.
    remove_python_env
    remove_edge
    cleanup_docker
    remove_install_dir
    remove_external_memory
    remove_packages

    echo "Uninstallation completed successfully."
}

main "$@"
