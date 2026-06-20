#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Install shell script (setup/macOS)

set -euo pipefail

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:     https://dlrp.ca
# GitHub:      https://github.com/DylanLRPollock/Monkey-Head-Project
# License:     https://opensource.org/license/gpl-3-0
# Overseen By: Dylan L.R. Pollock
# Updated:     2026-01-05
# ==================================================

# ----------------------------
# Defaults
# ----------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DEFAULT_INSTALL_DIR="/Applications/MonkeyHeadProject"
DEFAULT_REPO_URL="https://github.com/DylanLRPollock/Monkey-Head-Project"

INSTALL_DIR="$DEFAULT_INSTALL_DIR"
REPO_URL="$DEFAULT_REPO_URL"
MEMORY_PATH=""            # default resolved after arg parsing

FORCE=0
NON_INTERACTIVE=0
ACCEPT_LICENSE=0
SKIP_LICENSE=0
SKIP_BREW=0
SKIP_XCODE=0
WITH_COLIMA=0
VERBOSE=0

# These are set once INSTALL_DIR is finalized
VENV_DIR=""
ENV_FILE=""
BREW_DEPS_FILE=""

REAL_USER="${SUDO_USER:-$USER}"
REAL_GROUP="$(id -gn "$REAL_USER")"

# ----------------------------
# Helpers
# ----------------------------

log() {
  printf '[HueyOS][install] %s\n' "$*"
}

warn() {
  printf '[HueyOS][install][WARN] %s\n' "$*" >&2
}

die() {
  printf '[HueyOS][install][ERROR] %s\n' "$*" >&2
  exit 1
}

on_error() {
  local lineno="$1"
  local cmd="$2"
  warn "Failed at line ${lineno}: ${cmd}"
  warn "If you believe this is a bug in the installer, please include the above line number in your report."
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

usage() {
  cat <<'EOF'
HueyOS / Monkey Head Project (macOS) installer

Usage:
  ./install.sh [options]

Options:
  --install-dir PATH     Install location (default: /Applications/MonkeyHeadProject)
  --user                 Install for current user under ~/Applications/MonkeyHeadProject
  --memory-path PATH     Override shared memory path (default: <install-dir>/memory)
  --repo URL             Repository URL used for update fallbacks / metadata
  --force                Replace an existing installation at the install dir

  --non-interactive      Do not prompt (requires --accept-license or --skip-license)
  --accept-license       Skip UI prompt and record acceptance locally
  --skip-license         Skip license step entirely (not recommended)

  --skip-brew            Do not install or use Homebrew (requires deps already present)
  --skip-xcode           Do not check/install Xcode Command Line Tools

  --with-colima          Install Colima (Docker runtime alternative) via Homebrew
  -v, --verbose          Extra logging
  -h, --help             Show this help

Notes:
  • This script will request admin privileges only if required by the chosen install path.
  • Dependencies are installed conservatively; uninstall.sh does NOT remove Homebrew packages by default.
EOF
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    die "This installer is intended for macOS (Darwin)."
  fi
}

require_network_tools() {
  command_exists curl || die "curl is required but was not found."
}

SUDO=""

ensure_admin_if_needed() {
  # Decide whether we need sudo for filesystem operations on INSTALL_DIR and MEMORY_PATH.
  local parent
  parent="$(dirname "$INSTALL_DIR")"

  if [[ "$EUID" -eq 0 ]]; then
    # Already root.
    SUDO=""
    return 0
  fi

  if [[ -e "$INSTALL_DIR" ]]; then
    [[ -w "$INSTALL_DIR" ]] || SUDO="sudo"
  else
    [[ -w "$parent" ]] || SUDO="sudo"
  fi

  if [[ -n "$SUDO" ]]; then
    log "Administrator privileges are required to install to: $INSTALL_DIR"
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

ensure_install_dir() {
  if [[ "$FORCE" -eq 1 && -d "$INSTALL_DIR" ]]; then
    log "Removing existing installation (--force): $INSTALL_DIR"
    ${SUDO:-} rm -rf "$INSTALL_DIR"
  fi

  if [[ ! -d "$INSTALL_DIR" ]]; then
    log "Creating install directory: $INSTALL_DIR"
    ${SUDO:-} mkdir -p "$INSTALL_DIR"
  fi

  # Ensure the installation directory is owned by the real user so that pip/venv do not run as root.
  ensure_dir_owned_by_real_user "$INSTALL_DIR"
}

ensure_xcode_cli() {
  [[ "$SKIP_XCODE" -eq 1 ]] && return 0

  # The common, reliable check.
  if xcode-select -p >/dev/null 2>&1; then
    [[ "$VERBOSE" -eq 1 ]] && log "Xcode Command Line Tools detected."
    return 0
  fi

  warn "Xcode Command Line Tools were not detected."
  warn "Launching the Apple installer UI (xcode-select --install)."
  warn "After the installation completes, re-run this script."

  # This triggers a GUI prompt; it may return non-zero if already in progress.
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
    require_network_tools
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Immediately make brew available to this shell.
    if [[ -x /opt/homebrew/bin/brew ]]; then
      BREW="/opt/homebrew/bin/brew"
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x /usr/local/bin/brew ]]; then
      BREW="/usr/local/bin/brew"
      eval "$(/usr/local/bin/brew shellenv)"
    else
      die "Homebrew installation completed, but brew could not be found on PATH. Open a new terminal and re-run the installer."
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
  echo "$formula" >>"$BREW_DEPS_FILE"
}

install_packages() {
  [[ "$SKIP_BREW" -eq 1 ]] && return 0

  # Record only formulae that this installer newly installs.
  : >"$BREW_DEPS_FILE"

  log "Updating Homebrew metadata..."
  "$BREW" update

  # Keep this list conservative; prefer adding project-specific deps in requirements.txt or per-feature flags.
  brew_install_if_missing git
  brew_install_if_missing python

  # rsync is present on macOS but is often very old; Homebrew rsync improves compatibility and features.
  brew_install_if_missing rsync

  if [[ "$WITH_COLIMA" -eq 1 ]]; then
    brew_install_if_missing colima
    brew_install_if_missing docker
  fi
}

PYTHON_BIN=""

python_is_compatible() {
  local py="$1"
  "$py" - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 10) else 1)
PY
}

select_python() {
  if command_exists python3 && python_is_compatible "$(command -v python3)"; then
    PYTHON_BIN="$(command -v python3)"
    [[ "$VERBOSE" -eq 1 ]] && log "Using python3: $PYTHON_BIN"
    return 0
  fi

  if [[ "$SKIP_BREW" -eq 1 ]]; then
    die "python3 >= 3.10 is required, but a compatible python3 was not found. Install Python 3.10+ and re-run."
  fi

  ensure_homebrew
  brew_install_if_missing python

  if ! command_exists python3; then
    die "Homebrew Python was installed, but python3 is not on PATH. Open a new terminal and re-run."
  fi

  if ! python_is_compatible "$(command -v python3)"; then
    die "python3 was found, but it is older than 3.10. Please install/enable Python 3.10+ and re-run."
  fi

  PYTHON_BIN="$(command -v python3)"
  [[ "$VERBOSE" -eq 1 ]] && log "Using python3: $PYTHON_BIN"
}

sync_project_files() {
  # If the installer is being executed from within the installation dir, do not re-copy.
  local resolved_project_root
  local resolved_install_dir
  resolved_project_root="$(cd "$PROJECT_ROOT" && pwd -P)"

  if [[ -d "$INSTALL_DIR" ]]; then
    resolved_install_dir="$(cd "$INSTALL_DIR" && pwd -P)"
  else
    resolved_install_dir="$INSTALL_DIR"
  fi

  if [[ "$resolved_project_root" == "$resolved_install_dir" ]]; then
    [[ "$VERBOSE" -eq 1 ]] && log "Project already located at install dir; skipping file sync."
    return 0
  fi

  log "Syncing project files to: $INSTALL_DIR"
  log "  Source: $PROJECT_ROOT"

  # Exclude runtime artifacts and user state.
  local rsync_bin
  rsync_bin="$(command -v rsync || true)"
  [[ -n "$rsync_bin" ]] || die "rsync is required but was not found."

  # Do not use --delete by default; preserve any local config or user files inside INSTALL_DIR.
  "$rsync_bin" -a \
    --exclude 'venv' \
    --exclude 'memory' \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    "$PROJECT_ROOT/" "$INSTALL_DIR/"
}

prepare_memory_dirs() {
  log "Preparing memory directories: $MEMORY_PATH"

  # Create memory path (may be outside of INSTALL_DIR).
  if [[ ! -d "$MEMORY_PATH" ]]; then
    if [[ -n "$SUDO" && "$EUID" -ne 0 && ! -w "$(dirname "$MEMORY_PATH")" ]]; then
      sudo mkdir -p "$MEMORY_PATH"
      sudo chown -R "$REAL_USER":"$REAL_GROUP" "$MEMORY_PATH"
    else
      mkdir -p "$MEMORY_PATH"
    fi
  fi

  mkdir -p "$MEMORY_PATH/LOGS" "$MEMORY_PATH/RAW"
}

update_submodules() {
  # Safe to call even if not a git checkout.
  if [[ ! -f "$INSTALL_DIR/.gitmodules" ]]; then
    [[ "$VERBOSE" -eq 1 ]] && log "No .gitmodules found; skipping submodule initialization."
    return 0
  fi

  if ! command_exists git; then
    warn "git is required for submodules but was not found. Skipping submodule initialization."
    return 0
  fi

  if ! git -C "$INSTALL_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    warn "This installation is not a git working tree; cannot update submodules."
    warn "If you installed from an archive/zip, consider installing from a git clone for easier updates."
    return 0
  fi

  log "Initializing/updating git submodules..."
  git -C "$INSTALL_DIR" submodule update --init --recursive
}

create_or_update_venv() {
  VENV_DIR="$INSTALL_DIR/venv"

  if [[ "$FORCE" -eq 1 && -d "$VENV_DIR" ]]; then
    log "Removing existing virtual environment (--force): $VENV_DIR"
    rm -rf "$VENV_DIR"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment: $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  else
    [[ "$VERBOSE" -eq 1 ]] && log "Virtual environment already exists; reusing: $VENV_DIR"
  fi

  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"

  log "Upgrading pip tooling..."
  python -m pip install --upgrade pip setuptools wheel
}

install_python_deps() {
  log "Installing Python dependencies..."

  if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
    python -m pip install -r "$INSTALL_DIR/requirements.txt"
  else
    warn "requirements.txt not found at $INSTALL_DIR/requirements.txt (skipping)."
  fi

  if [[ -d "$INSTALL_DIR/vendor/pygpt/pygpt-mhp" ]]; then
    log "Installing local package: vendor/pygpt/pygpt-mhp"
    python -m pip install -e "$INSTALL_DIR/vendor/pygpt/pygpt-mhp"
  else
    warn "Local package vendor/pygpt/pygpt-mhp not found (skipping editable install)."
  fi
}

post_install_checks() {
  if [[ -f "$INSTALL_DIR/sync_pygpt_structure.py" ]]; then
    log "Synchronizing submodule files..."
    python "$INSTALL_DIR/sync_pygpt_structure.py"
  else
    [[ "$VERBOSE" -eq 1 ]] && warn "sync_pygpt_structure.py not found (skipping)."
  fi

  if [[ -f "$INSTALL_DIR/scripts/check_inter_program_connectivity.py" ]]; then
    log "Checking inter-program connectivity..."
    python "$INSTALL_DIR/scripts/check_inter_program_connectivity.py"
  else
    [[ "$VERBOSE" -eq 1 ]] && warn "scripts/check_inter_program_connectivity.py not found (skipping)."
  fi
}

record_install_metadata() {
  ENV_FILE="$INSTALL_DIR/.hueyos_install.env"
  BREW_DEPS_FILE="$INSTALL_DIR/.hueyos_brew_deps.installed"

  # Write a simple env file that update/uninstall can source.
  cat >"$ENV_FILE" <<EOF
# Generated by HueyOS install.sh on $(date -u '+%Y-%m-%dT%H:%M:%SZ')
INSTALL_DIR="$INSTALL_DIR"
VENV_DIR="$VENV_DIR"
MEMORY_PATH="$MEMORY_PATH"
REPO_URL="$REPO_URL"
PYTHON_BIN="$PYTHON_BIN"
EOF
}

prompt_license_cli() {
  # Minimal CLI fallback (non-legal advice): ask user to confirm acceptance.
  if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
    die "--non-interactive was set, but license acceptance was not provided. Use --accept-license or --skip-license."
  fi

  echo ""
  echo "License acceptance required."
  if [[ -f "$INSTALL_DIR/LICENSE" ]]; then
    echo "The license text is available at: $INSTALL_DIR/LICENSE"
  fi

  local answer
  read -r -p "Do you accept the project license terms? [y/N] " answer
  case "$answer" in
    y|Y|yes|YES)
      ACCEPT_LICENSE=1
      ;;
    *)
      die "License not accepted. Installation aborted."
      ;;
  esac
}

show_license() {
  if [[ "$SKIP_LICENSE" -eq 1 ]]; then
    warn "Skipping license step (--skip-license)."
    return 0
  fi

  if [[ "$ACCEPT_LICENSE" -eq 1 ]]; then
    [[ "$VERBOSE" -eq 1 ]] && log "License acceptance provided via --accept-license."
    return 0
  fi

  # Prefer the project's GUI license flow if available and we're not in an obvious headless environment.
  if [[ -f "$INSTALL_DIR/src/license_gui.py" && "$NON_INTERACTIVE" -eq 0 && -z "${SSH_CONNECTION:-}" ]]; then
    log "Displaying license agreement UI..."
    # Some environments may not be able to show UI; fall back to CLI.
    if ! python "$INSTALL_DIR/src/license_gui.py"; then
      warn "License dialog could not be displayed (or returned a non-zero exit code)."
      prompt_license_cli
    fi
  else
    prompt_license_cli
  fi
}

preload_data() {
  log "Preloading bundled data (best-effort)..."
  if python -c 'import importlib; importlib.import_module("hueyos")' >/dev/null 2>&1; then
    python -m hueyos.scripts.preload_data --summary || warn "Data preload failed (continuing)."
  else
    warn "HueyOS module not importable; skipping data preload."
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
    --user)
      INSTALL_DIR="$HOME/Applications/MonkeyHeadProject"
      shift
      ;;
    --memory-path)
      [[ $# -ge 2 ]] || die "--memory-path requires a value"
      MEMORY_PATH="$2"
      shift 2
      ;;
    --repo)
      [[ $# -ge 2 ]] || die "--repo requires a value"
      REPO_URL="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    --accept-license)
      ACCEPT_LICENSE=1
      shift
      ;;
    --skip-license)
      SKIP_LICENSE=1
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

# Resolve derived paths now that INSTALL_DIR is final.
VENV_DIR="$INSTALL_DIR/venv"
ENV_FILE="$INSTALL_DIR/.hueyos_install.env"
BREW_DEPS_FILE="$INSTALL_DIR/.hueyos_brew_deps.installed"

if [[ -z "$MEMORY_PATH" ]]; then
  MEMORY_PATH="$INSTALL_DIR/memory"
fi

if [[ "$NON_INTERACTIVE" -eq 1 && "$ACCEPT_LICENSE" -eq 0 && "$SKIP_LICENSE" -eq 0 ]]; then
  die "--non-interactive requires --accept-license or --skip-license."
fi

# ----------------------------
# Main
# ----------------------------

require_macos

ensure_admin_if_needed
ensure_install_dir

ensure_xcode_cli
ensure_homebrew

install_packages
select_python

sync_project_files

# Ensure ownership after syncing files (in case any privileged step touched content).
ensure_dir_owned_by_real_user "$INSTALL_DIR"

prepare_memory_dirs
update_submodules

create_or_update_venv
install_python_deps
post_install_checks
show_license
preload_data

record_install_metadata

echo ""
echo "Installation completed successfully."
echo ""
echo "Install directory: $INSTALL_DIR"
echo "Memory path:       $MEMORY_PATH"
echo "Virtualenv:        $VENV_DIR"
echo ""
echo "Next steps:"
echo "  1) Activate the environment:  source \"$VENV_DIR/bin/activate\""
echo "  2) Run the project entrypoint per the repository README."
echo ""
echo "***********************************************"
echo "  Thank you for supporting the Monkey Head Project!"
echo "***********************************************"
