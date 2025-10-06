#!/usr/bin/env bash
set -euo pipefail
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   2025-01-13
# ==================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INSTALL_DIR="/opt/monkey_head"
VENV_DIR="$INSTALL_DIR/venv"
MEMORY_PATH="${MEMORY_PATH:-$INSTALL_DIR/memory}"
CONFIG_DIR="$INSTALL_DIR/config/pygpt_net"
CONFIG_FILE="$CONFIG_DIR/config.json"
ENV_TEMPLATE="$PROJECT_ROOT/.env.example"
ENV_FILE="$INSTALL_DIR/.env"
DEBIAN_CODENAME=""
FORCE_OS=0
INSTALL_GUI=0
INSTALL_EDGE=0
EXTRA_GROUPS=()

export DEBIAN_FRONTEND=noninteractive

BASE_PACKAGES=(
    git
    docker.io
    docker-compose-plugin
    python3
    python3-venv
    qemu-kvm
    libvirt-daemon-system
    libvirt-clients
    curl
    ufw
    rsync
    gnupg
)
GUI_PACKAGES=(
    mate-desktop-environment-core
)

function usage() {
    cat <<USAGE
Usage: $0 [options]

Options:
  --with-gui            Install optional desktop packages (Mate desktop).
  --install-edge        Install Microsoft Edge (dev channel) after base setup.
  --extras LIST         Comma separated Python extras to install (ml,data,cloud).
  --force-os            Continue even if the host is not Debian Trixie.
  -h, --help            Show this help and exit.
USAGE
}

function error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

function parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --with-gui)
                INSTALL_GUI=1
                shift
                ;;
            --install-edge)
                INSTALL_EDGE=1
                shift
                ;;
            --extras)
                [[ $# -lt 2 ]] && error_exit "--extras requires a value"
                IFS=',' read -r -a EXTRA_GROUPS <<<"$2"
                shift 2
                ;;
            --extras=*)
                IFS=',' read -r -a EXTRA_GROUPS <<<"${1#*=}"
                shift
                ;;
            --force-os)
                FORCE_OS=1
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

function ensure_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "Please run this script with sudo or as root."
    fi
}

function detect_codename() {
    local os_id="" os_codename=""
    if [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        os_id=${ID:-}
        os_codename=${VERSION_CODENAME:-${DEBIAN_CODENAME:-}}
    fi

    DEBIAN_CODENAME=${DEBIAN_CODENAME:-${os_codename:-trixie}}

    if [[ ${os_id,,} != "debian" || ( ${DEBIAN_CODENAME,,} != "trixie" && ${DEBIAN_CODENAME,,} != "testing" ) ]]; then
        echo "WARNING: Debian Trixie/Testing not detected (ID=${os_id:-unknown}, CODENAME=${os_codename:-unknown})." >&2
        echo "         Apt sources will still be updated to '${DEBIAN_CODENAME}'." >&2
        if [[ $FORCE_OS -eq 0 ]]; then
            echo "Use --force-os to suppress this warning or abort now (Ctrl+C) if this is unexpected." >&2
            sleep 5
        fi
    else
        echo "Detected Debian ${DEBIAN_CODENAME}."
    fi
}

function copy_project_files() {
    if [[ "$PROJECT_ROOT" != "$INSTALL_DIR" ]]; then
        echo "Copying project files to $INSTALL_DIR ..."
        mkdir -p "$INSTALL_DIR"
        if command -v rsync >/dev/null 2>&1; then
            rsync -a --delete --exclude 'venv' "$PROJECT_ROOT/" "$INSTALL_DIR/"
        else
            echo "rsync not found; falling back to cp -a (venv directories will be skipped if present)."
            find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 ! -name 'venv' -exec rm -rf {} +
            cp -a "$PROJECT_ROOT"/. "$INSTALL_DIR"/
            rm -rf "$INSTALL_DIR/venv"
        fi
        PROJECT_ROOT="$INSTALL_DIR"
        ENV_TEMPLATE="$PROJECT_ROOT/.env.example"
        ENV_FILE="$PROJECT_ROOT/.env"
    fi
    cd "$PROJECT_ROOT"
}

function prepare_memory_dirs() {
    echo "Preparing memory directories at $MEMORY_PATH ..."
    mkdir -p "$MEMORY_PATH/LOGS" "$MEMORY_PATH/RAW"
}

function update_sources() {
    echo "Aligning apt sources to Debian ${DEBIAN_CODENAME} ..."
    python3 "$PROJECT_ROOT/huey/memory/PY/update_sources_to_trixie.py" "$DEBIAN_CODENAME" || \
        error_exit "Failed to update apt sources."
    echo "Updating system packages ..."
    apt-get update -y
    apt-get dist-upgrade -y
}

function install_packages() {
    echo "Installing required packages ..."
    apt-get install -y --no-install-recommends "${BASE_PACKAGES[@]}"
    if [[ $INSTALL_GUI -eq 1 ]]; then
        echo "Installing optional GUI packages ..."
        apt-get install -y --no-install-recommends "${GUI_PACKAGES[@]}"
    fi
}

function install_edge() {
    echo "Installing Microsoft Edge Dev ..."
    apt-get purge -y firefox || true
    apt-get autoremove -y || true
    install -d -m 755 /usr/share/keyrings
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" \
        > /etc/apt/sources.list.d/microsoft-edge-dev.list
    apt-get update -y
    apt-get install -y microsoft-edge-dev
}

function ensure_python_313() {
    local python_bin=""
    for candidate in python3.13 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            python_bin=$(command -v "$candidate")
            break
        fi
    done

    [[ -z $python_bin ]] && error_exit "python3 is not installed."

    local version
    version=$("$python_bin" -V 2>&1 | awk '{print $2}')
    if [[ $version != 3.13.* ]]; then
        cat <<'PYWARN' >&2
Python 3.13 is required for the Monkey Head Project runtime but was not detected.
Debian Trixie currently ships Python 3.12. Please build CPython 3.13 from source,
mirroring the Dockerfile build stage:

  apt-get install -y --no-install-recommends \
      build-essential ca-certificates curl wget xz-utils \
      libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
      libffi-dev liblzma-dev tk-dev uuid-dev
  curl -fsSLO https://www.python.org/ftp/python/3.13.5/Python-3.13.5.tgz
  tar -xzf Python-3.13.5.tgz
  cd Python-3.13.5
  ./configure --prefix=/usr/local --enable-optimizations --with-lto --enable-shared
  make -j"$(nproc)"
  make altinstall
  ldconfig

Re-run this installer after Python 3.13 is available (python3.13 or python3).
PYWARN
        exit 1
    fi

    echo "$python_bin"
}

function create_virtualenv() {
    local python_bin
    python_bin=$(ensure_python_313)

    if [[ -d $VENV_DIR ]]; then
        echo "Virtual environment already exists at $VENV_DIR"
    else
        echo "Creating virtual environment at $VENV_DIR ..."
        "$python_bin" -m venv "$VENV_DIR"
    fi

    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
}

function install_python_requirements() {
    local pip_bin="$VENV_DIR/bin/pip"
    echo "Installing core Python requirements ..."
    "$pip_bin" install -r "$PROJECT_ROOT/requirements/requirements-core.txt"
    echo "Installing project package in editable mode ..."
    "$pip_bin" install -e "$PROJECT_ROOT"

    declare -A extras_map=(
        [ml]="requirements/requirements-ml.txt"
        [data]="requirements/requirements-data.txt"
        [cloud]="requirements/requirements-cloud.txt"
    )

    if [[ ${#EXTRA_GROUPS[@]} -gt 0 ]]; then
        for extra in "${EXTRA_GROUPS[@]}"; do
            extra=${extra,,}
            if [[ -n ${extras_map[$extra]:-} ]]; then
                local req_file="$PROJECT_ROOT/${extras_map[$extra]}"
                if [[ -f $req_file ]]; then
                    echo "Installing optional '$extra' dependencies ..."
                    "$pip_bin" install -r "$req_file"
                else
                    echo "Skipping missing requirements file: $req_file"
                fi
            else
                echo "Unknown extras group '$extra' (supported: ml,data,cloud)" >&2
            fi
        done
    fi
}

function run_post_setup_checks() {
    local python_bin="$VENV_DIR/bin/python"
    echo "Synchronising pygpt structure ..."
    "$python_bin" "$PROJECT_ROOT/huey/memory/PY/sync_pygpt_structure.py" || \
        echo "Warning: sync_pygpt_structure.py failed"
    echo "Checking inter-program connectivity ..."
    "$python_bin" "$PROJECT_ROOT/huey/memory/PY/check_inter_program_connectivity.py" || \
        echo "Warning: connectivity check failed"
}

function run_preload() {
    local python_bin="$VENV_DIR/bin/python"
    echo "Preloading bundled data ..."
    "$python_bin" -m huey.memory.PY.preload_data --summary || \
        echo "Warning: preload_data reported an issue"
}

function ensure_env_file() {
    if [[ -f $ENV_FILE ]]; then
        echo "Existing .env detected at $ENV_FILE"
        return
    fi

    if [[ ! -f $ENV_TEMPLATE ]]; then
        cat <<'ENV' > "$ENV_TEMPLATE"
APP_ENV=production
TZ=Etc/UTC
PDF_DIR=/opt/monkey_head/memory/PDF
# Uncomment to override default log directory
# LOG_DIR=/opt/monkey_head/memory/LOGS
ENV
    fi

    echo "Copying environment template to $ENV_FILE"
    mkdir -p "$(dirname "$ENV_FILE")"
    cp "$ENV_TEMPLATE" "$ENV_FILE"
}

function show_license_gui() {
    local python_bin="$VENV_DIR/bin/python"
    mkdir -p "$CONFIG_DIR"
    if [[ ! -f $CONFIG_FILE ]]; then
        cat <<'JSON' > "$CONFIG_FILE"
{
    "license": {
        "accepted": false
    }
}
JSON
    fi

    echo "Ensuring license agreement is accepted ..."
    PYTHONPATH="$PROJECT_ROOT" "$python_bin" - <<'PY'
from pathlib import Path
from huey.memory.PY.license_gui import show_license_gui, ConfigManager

config_path = Path("/opt/monkey_head/config/pygpt_net/config.json")
manager = ConfigManager(str(config_path))
if manager.get_setting("license.accepted"):
    raise SystemExit(0)

try:
    show_license_gui(config_path)
except Exception as exc:  # pragma: no cover - depends on desktop availability
    print(f"License GUI could not be displayed: {exc}")
    print("Run '/opt/monkey_head/venv/bin/python -m huey.memory.PY.license_cli' to accept via CLI.")
    manager.set_setting("license.accepted", False)
PY
}

function main() {
    parse_args "$@"
    ensure_root
    detect_codename
    copy_project_files
    prepare_memory_dirs
    update_sources
    install_packages
    if [[ $INSTALL_EDGE -eq 1 ]]; then
        install_edge
    fi
    create_virtualenv
    install_python_requirements
    run_post_setup_checks
    ensure_env_file
    show_license_gui
    run_preload

    echo "Installation completed successfully."
    echo
    echo "***********************************************"
    echo "  Thank you for supporting the Monkey Head Project!"
    echo "  We hope you enjoy using it."
    echo "***********************************************"
}

main "$@"
