#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Uninstall shell script (setup/macOS)

set -euo pipefail

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:     https://dlrp.ca
# GitHub:      https://github.com/DylanLRPollock/Monkey-Head-Project
# License:     https://opensource.org/license/gpl-3-0
# Overseen By: Dylan L.R. Pollock
# Updated:     2026-01-05
# ==================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEFAULT_INSTALL_DIR="/Applications/MonkeyHeadProject"

INSTALL_DIR="$DEFAULT_INSTALL_DIR"
YES=0
REMOVE_MEMORY=0
PURGE_BREW_DEPS=0
VERBOSE=0

# These may be overridden by the install metadata file.
VENV_DIR=""
MEMORY_PATH=""
ENV_FILE=""
BREW_DEPS_FILE=""
REPO_URL=""

REAL_USER="${SUDO_USER:-$USER}"
REAL_GROUP="$(id -gn "$REAL_USER")"

log() { printf '[HueyOS][uninstall] %s\n' "$*"; }
warn() { printf '[HueyOS][uninstall][WARN] %s\n' "$*" >&2; }
die() { printf '[HueyOS][uninstall][ERROR] %s\n' "$*" >&2; exit 1; }

on_error() {
  local lineno="$1" cmd="$2"
  warn "Failed at line ${lineno}: ${cmd}"
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

command_exists() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'EOF'
HueyOS / Monkey Head Project (macOS) uninstaller

Usage:
  ./uninstall.sh [options]

Options:
  --install-dir PATH   Installation directory (default: /Applications/MonkeyHeadProject)
  --yes                Do not prompt for confirmation
  --remove-memory      Delete the memory directory (by default, memory is preserved when possible)
  --purge-brew-deps    Attempt to uninstall Homebrew formulae installed by install.sh (requires --yes)
  -v, --verbose        Extra logging
  -h, --help           Show this help

Safety defaults:
  • This script does NOT run "docker system prune".
  • This script does NOT uninstall Homebrew packages unless --purge-brew-deps is explicitly provided.
  • If the memory path is inside the install dir, it will be moved to the user's Application Support
    directory unless --remove-memory is specified.
EOF
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    die "This uninstaller is intended for macOS (Darwin)."
  fi
}

load_install_metadata_if_present() {
  ENV_FILE="$INSTALL_DIR/.hueyos_install.env"
  if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$ENV_FILE" || true
  fi

  VENV_DIR="${VENV_DIR:-$INSTALL_DIR/venv}"
  MEMORY_PATH="${MEMORY_PATH:-$INSTALL_DIR/memory}"
  BREW_DEPS_FILE="${BREW_DEPS_FILE:-$INSTALL_DIR/.hueyos_brew_deps.installed}"
}

SUDO=""

ensure_admin_if_needed() {
  if [[ "$EUID" -eq 0 ]]; then
    SUDO=""
    return 0
  fi

  if [[ -e "$INSTALL_DIR" ]]; then
    [[ -w "$INSTALL_DIR" ]] || SUDO="sudo"
  else
    [[ -w "$(dirname "$INSTALL_DIR")" ]] || SUDO="sudo"
  fi

  if [[ -n "$SUDO" ]]; then
    log "Administrator privileges may be required to remove: $INSTALL_DIR"
    sudo -v
  fi
}

confirm() {
  [[ "$YES" -eq 1 ]] && return 0

  echo ""
  echo "This will uninstall HueyOS / Monkey Head Project from:"
  echo "  $INSTALL_DIR"
  echo ""
  if [[ "$REMOVE_MEMORY" -eq 1 ]]; then
    echo "The memory directory will be deleted:"
    echo "  $MEMORY_PATH"
  else
    echo "The memory directory will be preserved when possible."
  fi
  echo ""

  local answer
  read -r -p "Continue? [y/N] " answer
  case "$answer" in
    y|Y|yes|YES) return 0 ;;
    *) die "Uninstall cancelled." ;;
  esac
}

path_is_within() {
  # Usage: path_is_within <path> <parent>
  local p="$1" parent="$2"
  # Normalize trailing slashes.
  p="${p%/}"
  parent="${parent%/}"

  [[ "$p" == "$parent" ]] && return 0
  [[ "$p" == "$parent"/* ]] && return 0
  return 1
}

preserve_memory_if_needed() {
  if [[ "$REMOVE_MEMORY" -eq 1 ]]; then
    [[ "$VERBOSE" -eq 1 ]] && log "--remove-memory specified; memory will not be preserved."
    return 0
  fi

  # Only preserve automatically if memory resides inside the install directory.
  if ! path_is_within "$MEMORY_PATH" "$INSTALL_DIR"; then
    [[ "$VERBOSE" -eq 1 ]] && log "Memory path is outside install dir; leaving in place: $MEMORY_PATH"
    return 0
  fi

  if [[ ! -d "$MEMORY_PATH" ]]; then
    [[ "$VERBOSE" -eq 1 ]] && log "No memory directory found at: $MEMORY_PATH"
    return 0
  fi

  local target_base="$HOME/Library/Application Support/MonkeyHeadProject"
  local target="$target_base/memory"

  mkdir -p "$target_base"

  if [[ -e "$target" ]]; then
    # Avoid overwriting an existing preserved memory directory.
    local ts
    ts="$(date '+%Y%m%d-%H%M%S')"
    target="$target_base/memory-$ts"
  fi

  log "Preserving memory by moving:"
  log "  from: $MEMORY_PATH"
  log "  to:   $target"

  # This should be user-owned under normal installs. If not, attempt sudo.
  if [[ -n "$SUDO" && "$EUID" -ne 0 && ! -w "$(dirname "$MEMORY_PATH")" ]]; then
    sudo mv "$MEMORY_PATH" "$target"
    sudo chown -R "$REAL_USER":"$REAL_GROUP" "$target"
  else
    mv "$MEMORY_PATH" "$target"
  fi
}

remove_launchd_jobs_if_present() {
  # Best-effort cleanup for common LaunchAgent/Daemon names.
  # (No-op if none exist.)
  local agents=(
    "$HOME/Library/LaunchAgents/ca.dlrp.hueyos.plist"
    "$HOME/Library/LaunchAgents/ca.dlrp.monkeyheadproject.plist"
  )
  local daemons=(
    "/Library/LaunchDaemons/ca.dlrp.hueyos.plist"
    "/Library/LaunchDaemons/ca.dlrp.monkeyheadproject.plist"
  )

  for p in "${agents[@]}"; do
    if [[ -f "$p" ]]; then
      warn "Removing LaunchAgent: $p"
      launchctl bootout gui/"$(id -u)" "$p" >/dev/null 2>&1 || true
      rm -f "$p"
    fi
  done

  for p in "${daemons[@]}"; do
    if [[ -f "$p" ]]; then
      warn "Removing LaunchDaemon: $p"
      ${SUDO:-} launchctl bootout system "$p" >/dev/null 2>&1 || true
      ${SUDO:-} rm -f "$p"
    fi
  done
}

purge_homebrew_deps_if_requested() {
  [[ "$PURGE_BREW_DEPS" -eq 1 ]] || return 0
  [[ "$YES" -eq 1 ]] || die "--purge-brew-deps requires --yes (non-interactive confirmation)."

  if ! command_exists brew; then
    warn "Homebrew not found; cannot purge dependencies."
    return 0
  fi

  if [[ ! -f "$BREW_DEPS_FILE" ]]; then
    warn "No recorded Homebrew dependency list found at: $BREW_DEPS_FILE"
    warn "Nothing to purge."
    return 0
  fi

  log "Purging Homebrew formulae recorded as installed by install.sh (best-effort)..."
  while IFS= read -r formula; do
    [[ -z "$formula" ]] && continue
    if brew list --formula "$formula" >/dev/null 2>&1; then
      warn "Uninstalling: $formula"
      brew uninstall "$formula" || true
    fi
  done <"$BREW_DEPS_FILE"

  brew cleanup || true
}

remove_install_dir() {
  if [[ ! -d "$INSTALL_DIR" ]]; then
    warn "Install directory not found; nothing to remove: $INSTALL_DIR"
    return 0
  fi

  log "Removing install directory: $INSTALL_DIR"
  ${SUDO:-} rm -rf "$INSTALL_DIR"
}

remove_memory_if_requested() {
  [[ "$REMOVE_MEMORY" -eq 1 ]] || return 0

  if [[ ! -d "$MEMORY_PATH" ]]; then
    warn "Memory directory not found; nothing to remove: $MEMORY_PATH"
    return 0
  fi

  warn "Deleting memory directory: $MEMORY_PATH"
  if [[ -n "$SUDO" && "$EUID" -ne 0 && ! -w "$(dirname "$MEMORY_PATH")" ]]; then
    sudo rm -rf "$MEMORY_PATH"
  else
    rm -rf "$MEMORY_PATH"
  fi
}

# ----------------------------
# Argument parsing
# ----------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      [[ $# -ge 2 ]] || die "--install-dir requires a value"
      INSTALL_DIR="$2"
      shift 2
      ;;
    --yes)
      YES=1
      shift
      ;;
    --remove-memory)
      REMOVE_MEMORY=1
      shift
      ;;
    --purge-brew-deps)
      PURGE_BREW_DEPS=1
      shift
      ;;
    -v|--verbose)
      VERBOSE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1 (use --help)"
      ;;
  esac
done

# Derived defaults.
VENV_DIR="$INSTALL_DIR/venv"
MEMORY_PATH="$INSTALL_DIR/memory"
ENV_FILE="$INSTALL_DIR/.hueyos_install.env"
BREW_DEPS_FILE="$INSTALL_DIR/.hueyos_brew_deps.installed"

# ----------------------------
# Main
# ----------------------------

require_macos
load_install_metadata_if_present
ensure_admin_if_needed

confirm

remove_launchd_jobs_if_present

# Preserve memory BEFORE removing the install dir.
preserve_memory_if_needed

# Homebrew purge must happen before we delete the install directory, because the dependency
# record is stored inside it.
purge_homebrew_deps_if_requested

remove_install_dir

# If the user requested memory deletion and it was external, delete it now.
remove_memory_if_requested

echo ""
echo "Uninstallation completed."
if [[ "$REMOVE_MEMORY" -eq 1 ]]; then
  echo "Memory directory deleted: $MEMORY_PATH"
else
  echo "Memory directory preserved when possible."
fi