#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Update shell script (setup/macOS)

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
DEFAULT_REPO_URL="https://github.com/DylanLRPollock/Monkey-Head-Project"

INSTALL_DIR="$DEFAULT_INSTALL_DIR"
REPO_URL="$DEFAULT_REPO_URL"
REPO_URL_FROM_CLI=""

FORCE=0
RECREATE_VENV=0
NON_INTERACTIVE=0
SKIP_BREW=0
SKIP_XCODE=0
WITH_COLIMA=0
VERBOSE=0

VENV_DIR=""
MEMORY_PATH=""
ENV_FILE=""
BREW_DEPS_FILE=""
PYTHON_BIN=""

REAL_USER="${SUDO_USER:-$USER}"
REAL_GROUP="$(id -gn "$REAL_USER")"

log() { printf '[HueyOS][update] %s\n' "$*"; }
warn() { printf '[HueyOS][update][WARN] %s\n' "$*" >&2; }
die() { printf '[HueyOS][update][ERROR] %s\n' "$*" >&2; exit 1; }

on_error() {
  local lineno="$1" cmd="$2"
  warn "Failed at line ${lineno}: ${cmd}"
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

command_exists() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'EOF'
HueyOS / Monkey Head Project (macOS) updater

Usage:
  ./update.sh [options]

Options:
  --install-dir PATH     Installation directory (default: /Applications/MonkeyHeadProject)
  --repo URL             Repository URL (used when the install dir is not a git checkout)
  --force                If the install dir is a git repo: discard local changes before updating
                         If updating from a cloned snapshot: use rsync --delete

  --recreate-venv         Recreate the Python virtual environment from scratch
  --non-interactive       Do not prompt (fails instead of asking)

  --skip-brew             Do not install/use Homebrew (requires deps already present)
  --skip-xcode            Do not check/install Xcode Command Line Tools
  --with-colima           Ensure Colima + Docker CLI are installed via Homebrew

  -v, --verbose           Extra logging
  -h, --help              Show this help

Behavior:
  • If INSTALL_DIR is a git working tree, this script runs git fetch/pull and updates submodules.
  • If INSTALL_DIR is not a git working tree (e.g., installed from a zip), this script clones the
    repo to a temporary directory and rsyncs it over the installation (preserving venv/ and memory/).
EOF
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    die "This updater is intended for macOS (Darwin)."
  fi
}

ensure_xcode_cli() {
  [[ "$SKIP_XCODE" -eq 1 ]] && return 0

  if xcode-select -p >/dev/null 2>&1; then
    [[ "$VERBOSE" -eq 1 ]] && log "Xcode Command Line Tools detected."
    return 0
  fi

  warn "Xcode Command Line Tools were not detected."
  warn "Launching the Apple installer UI (xcode-select --install)."
  warn "After the installation completes, re-run this script."
  xcode-select --install || true
  exit 2
}

BREW=""

ensure_homebrew() {
  [[ "$SKIP_BREW" -eq 1 ]] && return 0

  if command_exists brew; then
    BREW="$(command -v brew)"
  elif [[ -x /opt/homebrew/bin/brew ]]; then
    BREW="/opt/homebrew/bin/brew"
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    BREW="/usr/local/bin/brew"
    eval "$(/usr/local/bin/brew shellenv)"
  else
    log "Homebrew not found. Installing Homebrew..."
    command_exists curl || die "curl is required to install Homebrew."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    if [[ -x /opt/homebrew/bin/brew ]]; then
      BREW="/opt/homebrew/bin/brew"
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x /usr/local/bin/brew ]]; then
      BREW="/usr/local/bin/brew"
      eval "$(/usr/local/bin/brew shellenv)"
    else
      die "Homebrew installation completed, but brew could not be found on PATH. Open a new terminal and re-run."
    fi
  fi

  [[ -n "$BREW" ]] || die "brew could not be resolved."
}

brew_install_if_missing() {
  local formula="$1"
  [[ -n "$BREW" ]] || die "Internal error: brew not initialized."

  if "$BREW" list --formula "$formula" >/dev/null 2>&1; then
    [[ "$VERBOSE" -eq 1 ]] && log "Homebrew formula already installed: $formula"
    return 0
  fi

  log "Installing Homebrew formula: $formula"
  "$BREW" install "$formula"
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
  REPO_URL="${REPO_URL:-$DEFAULT_REPO_URL}"

  # CLI override takes precedence over metadata.
  if [[ -n "$REPO_URL_FROM_CLI" ]]; then
    REPO_URL="$REPO_URL_FROM_CLI"
  fi
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
    log "Administrator privileges may be required to update: $INSTALL_DIR"
    sudo -v
  fi
}

ensure_dir_owned_by_real_user() {
  local path="$1"
  if [[ -z "$path" ]]; then
    return 0
  fi

  if [[ "$EUID" -eq 0 ]]; then
    chown -R "$REAL_USER":"$REAL_GROUP" "$path"
  elif [[ -n "$SUDO" ]]; then
    sudo chown -R "$REAL_USER":"$REAL_GROUP" "$path"
  fi
}

python_is_compatible() {
  local py="$1"
  "$py" - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 10) else 1)
PY
}

select_python() {
  # Prefer venv python if it exists (ensures we use the same interpreter used at install time).
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    PYTHON_BIN="$VENV_DIR/bin/python"
    [[ "$VERBOSE" -eq 1 ]] && log "Using venv python: $PYTHON_BIN"
    return 0
  fi

  if command_exists python3 && python_is_compatible "$(command -v python3)"; then
    PYTHON_BIN="$(command -v python3)"
    [[ "$VERBOSE" -eq 1 ]] && log "Using python3: $PYTHON_BIN"
    return 0
  fi

  if [[ "$SKIP_BREW" -eq 1 ]]; then
    die "python3 >= 3.10 is required (or an existing venv). Install Python 3.10+ and re-run."
  fi

  ensure_homebrew
  brew_install_if_missing python

  command_exists python3 || die "Homebrew Python installed, but python3 is not on PATH. Open a new terminal and re-run."
  python_is_compatible "$(command -v python3)" || die "python3 is older than 3.10. Please install/enable Python 3.10+."
  PYTHON_BIN="$(command -v python3)"
}

git_update_in_place() {
  log "Updating installation via git (in place)..."

  if ! command_exists git; then
    if [[ "$SKIP_BREW" -eq 1 ]]; then
      die "git is required to update but was not found. Install git and re-run."
    fi
    ensure_homebrew
    brew_install_if_missing git
  fi

  if ! git -C "$INSTALL_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 1
  fi

  local status
  status="$(git -C "$INSTALL_DIR" status --porcelain || true)"
  if [[ -n "$status" && "$FORCE" -ne 1 ]]; then
    warn "Local changes detected in $INSTALL_DIR."
    warn "Commit/stash your changes, or re-run with --force to discard them."
    exit 3
  fi

  local branch
  branch="$(git -C "$INSTALL_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"

  local before after
  before="$(git -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"

  git -C "$INSTALL_DIR" fetch --all --tags

  if [[ "$FORCE" -eq 1 ]]; then
    warn "--force specified: discarding local changes and resetting to origin/${branch}"
    git -C "$INSTALL_DIR" reset --hard "origin/${branch}" || git -C "$INSTALL_DIR" reset --hard
    git -C "$INSTALL_DIR" clean -fd
  else
    git -C "$INSTALL_DIR" pull --ff-only
  fi

  if [[ -f "$INSTALL_DIR/.gitmodules" ]]; then
    git -C "$INSTALL_DIR" submodule update --init --recursive
  fi

  after="$(git -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  if [[ "$before" != "$after" ]]; then
    log "Updated code: ${before} -> ${after}"
  else
    log "Code already up to date (${after})."
  fi

  return 0
}

rsync_update_from_clone() {
  log "Updating installation from a temporary clone (install dir is not a git working tree)..."

  if ! command_exists git; then
    if [[ "$SKIP_BREW" -eq 1 ]]; then
      die "git is required to update but was not found. Install git and re-run."
    fi
    ensure_homebrew
    brew_install_if_missing git
  fi

  local tmpdir
  tmpdir="$(mktemp -d)"
  [[ -n "$tmpdir" && -d "$tmpdir" ]] || die "Failed to create temp directory."

  # Ensure cleanup.
  cleanup_tmp() { rm -rf "$tmpdir"; }
  trap 'cleanup_tmp' EXIT

  log "Cloning: $REPO_URL"
  git clone --depth 1 "$REPO_URL" "$tmpdir"

  local rsync_bin
  rsync_bin="$(command -v rsync || true)"
  [[ -n "$rsync_bin" ]] || die "rsync is required but was not found."

  log "Syncing updated files into: $INSTALL_DIR"
  if [[ "$FORCE" -eq 1 ]]; then
    warn "--force specified: rsync will delete files in the install dir that are not in the repo snapshot."
    "$rsync_bin" -a --delete \
      --exclude 'venv' \
      --exclude 'memory' \
      --exclude '.hueyos_install.env' \
      --exclude '.hueyos_brew_deps.installed' \
      "$tmpdir/" "$INSTALL_DIR/"
  else
    "$rsync_bin" -a \
      --exclude 'venv' \
      --exclude 'memory' \
      --exclude '.hueyos_install.env' \
      --exclude '.hueyos_brew_deps.installed' \
      "$tmpdir/" "$INSTALL_DIR/"
  fi

  # Explicitly clean up now (and clear EXIT trap).
  cleanup_tmp
  trap - EXIT
}

create_or_update_venv() {
  if [[ "$RECREATE_VENV" -eq 1 && -d "$VENV_DIR" ]]; then
    warn "Recreating virtual environment (--recreate-venv): $VENV_DIR"
    rm -rf "$VENV_DIR"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment: $VENV_DIR"
    select_python
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  else
    [[ "$VERBOSE" -eq 1 ]] && log "Virtual environment present; updating packages in place."
  fi

  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip setuptools wheel
}

install_python_deps() {
  log "Installing/updating Python dependencies..."

  if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
    python -m pip install -r "$INSTALL_DIR/requirements.txt"
  else
    warn "requirements.txt not found at $INSTALL_DIR/requirements.txt (skipping)."
  fi

  if [[ -d "$INSTALL_DIR/vendor/pygpt/pygpt-mhp" ]]; then
    python -m pip install -e "$INSTALL_DIR/vendor/pygpt/pygpt-mhp"
  else
    [[ "$VERBOSE" -eq 1 ]] && warn "Local package vendor/pygpt/pygpt-mhp not found (skipping)."
  fi
}

post_update_checks() {
  if [[ -f "$INSTALL_DIR/sync_pygpt_structure.py" ]]; then
    log "Synchronizing submodule files..."
    python "$INSTALL_DIR/sync_pygpt_structure.py"
  fi

  if [[ -f "$INSTALL_DIR/scripts/check_inter_program_connectivity.py" ]]; then
    log "Checking inter-program connectivity..."
    python "$INSTALL_DIR/scripts/check_inter_program_connectivity.py"
  fi
}

preload_data() {
  log "Preloading bundled data (best-effort)..."
  if python -c 'import importlib; importlib.import_module("hueyos")' >/dev/null 2>&1; then
    python -m hueyos.scripts.preload_data --summary || warn "Data preload failed (continuing)."
  else
    [[ "$VERBOSE" -eq 1 ]] && warn "HueyOS module not importable; skipping data preload."
  fi
}

record_update_metadata() {
  ENV_FILE="$INSTALL_DIR/.hueyos_install.env"
  # Update the env file (keep MEMORY_PATH and other values as-is).
  cat >"$ENV_FILE" <<EOF
# Updated by HueyOS update.sh on $(date -u '+%Y-%m-%dT%H:%M:%SZ')
INSTALL_DIR="$INSTALL_DIR"
VENV_DIR="$VENV_DIR"
MEMORY_PATH="$MEMORY_PATH"
REPO_URL="$REPO_URL"
PYTHON_BIN="${VENV_DIR}/bin/python"
EOF
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
    --repo)
      [[ $# -ge 2 ]] || die "--repo requires a value"
      REPO_URL="$2"
      REPO_URL_FROM_CLI="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --recreate-venv)
      RECREATE_VENV=1
      shift
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    --skip-brew)
      SKIP_BREW=1
      shift
      ;;
    --skip-xcode)
      SKIP_XCODE=1
      shift
      ;;
    --with-colima)
      WITH_COLIMA=1
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

if [[ ! -d "$INSTALL_DIR" ]]; then
  die "Install directory not found: $INSTALL_DIR\nRun install.sh first."
fi

load_install_metadata_if_present
ensure_admin_if_needed

ensure_xcode_cli

if [[ "$SKIP_BREW" -eq 0 ]]; then
  ensure_homebrew
  if [[ "$WITH_COLIMA" -eq 1 ]]; then
    log "Ensuring Colima + Docker CLI are installed (Homebrew)..."
    "$BREW" update
    brew_install_if_missing colima
    brew_install_if_missing docker
  fi
fi

# Ensure content is writable by the real user for venv/pip operations.
ensure_dir_owned_by_real_user "$INSTALL_DIR"

if ! git_update_in_place; then
  rsync_update_from_clone
fi

ensure_dir_owned_by_real_user "$INSTALL_DIR"

create_or_update_venv
install_python_deps
post_update_checks
preload_data
record_update_metadata

echo ""
echo "Update completed successfully."
echo "Install directory: $INSTALL_DIR"
echo "Virtualenv:        $VENV_DIR"
echo "Memory path:       $MEMORY_PATH"
