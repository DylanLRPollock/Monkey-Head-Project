#!/usr/bin/env bash
# HueyOS Debian Forky Installer Script
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
#   Installs HueyOS components on Debian Forky.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

INSTALL_DIR="/opt/hueyos"
VENV_DIR="$INSTALL_DIR/venv"
MEMORY_PATH="${MEMORY_PATH:-$INSTALL_DIR/memory}"
CONFIG_DIR="$INSTALL_DIR/config/pygpt_net"
CONFIG_FILE="$CONFIG_DIR/config.json"
ENV_TEMPLATE="$PROJECT_ROOT/.env.example"
ENV_FILE="$INSTALL_DIR/.env"

# Target codename (override by exporting DEBIAN_CODENAME before running).
DEBIAN_CODENAME="${DEBIAN_CODENAME:-}"

# Host detection metadata (informational)
HOST_OS_ID=""
HOST_DEBIAN_CODENAME=""

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
    ca-certificates
)
AUDIO_SYSTEM_PACKAGES=(
    ffmpeg
    libasound2-dev
    libportaudio2
    libportaudiocpp0
    portaudio19-dev
    libsndfile1
)
GUI_PACKAGES=(
    mate-desktop-environment-core
)

function usage() {
    cat <<USAGE
Usage: $0 [options]

Options:
  --with-gui            Install optional desktop packages (Mate desktop).
  --install-edge        Install Microsoft Edge (beta channel) after base setup.
  --extras LIST         Comma separated Python extras to install (ml,data,cloud).
  --force-os            Continue even if the host is not Debian Forky/Testing.
  -h, --help            Show this help and exit.

Environment:
  DEBIAN_CODENAME        Target apt codename to align sources to (default: forky)
                         Example: DEBIAN_CODENAME=testing sudo ./install.sh
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
    local os_id="" os_codename="" os_pretty=""

    if [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        os_id=${ID:-}
        os_codename=${VERSION_CODENAME:-}
        os_pretty=${PRETTY_NAME:-}
    fi

    if [[ -z $os_codename ]] && command -v lsb_release >/dev/null 2>&1; then
        os_codename=$(lsb_release -cs 2>/dev/null || true)
    fi

    HOST_OS_ID="$os_id"
    HOST_DEBIAN_CODENAME="$os_codename"

    # Default target codename is Forky unless overridden by env var.
    DEBIAN_CODENAME="${DEBIAN_CODENAME:-forky}"

    local host_id_lc="${HOST_OS_ID,,}"
    local host_codename_lc="${HOST_DEBIAN_CODENAME,,}"
    local target_codename_lc="${DEBIAN_CODENAME,,}"

    echo "Host: ID=${HOST_OS_ID:-unknown}, CODENAME=${HOST_DEBIAN_CODENAME:-unknown}, PRETTY_NAME=${os_pretty:-unknown}"
    echo "Target apt codename: ${DEBIAN_CODENAME}"

    if [[ $host_id_lc != "debian" ]]; then
        echo "WARNING: Host is not Debian. Proceeding will still attempt to target '${DEBIAN_CODENAME}' apt sources." >&2
        if [[ $FORCE_OS -eq 0 ]]; then
            echo "Use --force-os to suppress this warning or abort now (Ctrl+C) if this is unexpected." >&2
            sleep 5
        fi
        return
    fi

    # Acceptable hosts when targeting forky/testing: forky, testing, sid/unstable.
    local ok=0
    case "$target_codename_lc" in
        forky|testing)
            if [[ $host_codename_lc == "forky" || $host_codename_lc == "testing" || $host_codename_lc == "sid" || $host_codename_lc == "unstable" ]]; then
                ok=1
            fi
            ;;
        *)
            if [[ -n $host_codename_lc && $host_codename_lc == "$target_codename_lc" ]]; then
                ok=1
            fi
            ;;
    esac

    if [[ $ok -eq 0 ]]; then
        echo "WARNING: Debian Forky/Testing not detected (HOST_CODENAME=${HOST_DEBIAN_CODENAME:-unknown})." >&2
        echo "         Apt sources will be aligned to '${DEBIAN_CODENAME}'." >&2
        if [[ $FORCE_OS -eq 0 ]]; then
            echo "Use --force-os to suppress this warning or abort now (Ctrl+C) if this is unexpected." >&2
            sleep 5
        fi
    else
        echo "Detected Debian ${HOST_DEBIAN_CODENAME:-unknown}; continuing."
    fi
}

function ensure_bootstrap_tools() {
    # Ensure we can run the apt-sources update helper (python3) and basic HTTPS tooling.
    local pkgs=()
    command -v python3 >/dev/null 2>&1 || pkgs+=(python3)
    command -v curl >/dev/null 2>&1 || pkgs+=(curl)
    command -v gpg >/dev/null 2>&1 || pkgs+=(gnupg)
    command -v rsync >/dev/null 2>&1 || pkgs+=(rsync)
    command -v update-ca-certificates >/dev/null 2>&1 || pkgs+=(ca-certificates)

    if [[ ${#pkgs[@]} -gt 0 ]]; then
        echo "Installing bootstrap packages: ${pkgs[*]} ..."
        apt-get update -y
        apt-get install -y --no-install-recommends "${pkgs[@]}"
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

    local updater=""
    local candidates=(
        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_forky.py"
        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_testing.py"
        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_codename.py"
        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_debian.py"
        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_trixie.py"  # migration-only fallback for legacy nodes
    )

    for candidate in "${candidates[@]}"; do
        if [[ -f "$candidate" ]]; then
            updater="$candidate"
            break
        fi
    done

    [[ -z $updater ]] && error_exit "Failed to locate an apt-sources update helper under $PROJECT_ROOT/huey/memory/PY"

    python3 "$updater" "$DEBIAN_CODENAME" || error_exit "Failed to update apt sources."
    echo "Updating system packages ..."
    apt-get update -y
    apt-get dist-upgrade -y
}

function install_packages() {
    echo "Installing required packages ..."
    apt-get install -y --no-install-recommends "${BASE_PACKAGES[@]}"
    echo "Installing audio runtime packages for PyGPT/PyGPT-net ..."
    apt-get install -y --no-install-recommends "${AUDIO_SYSTEM_PACKAGES[@]}"
    if [[ $INSTALL_GUI -eq 1 ]]; then
        echo "Installing optional GUI packages ..."
        apt-get install -y --no-install-recommends "${GUI_PACKAGES[@]}"
    fi
}

function install_edge() {
    echo "Installing Microsoft Edge Beta ..."
    apt-get purge -y firefox || true
    apt-get autoremove -y || true
    install -d -m 755 /usr/share/keyrings
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" \
        > /etc/apt/sources.list.d/microsoft-edge-beta.list
    apt-get update -y
    apt-get install -y microsoft-edge-beta
    if command -v update-alternatives >/dev/null 2>&1 && [[ -x /usr/bin/microsoft-edge-beta ]]; then
        update-alternatives --set x-www-browser /usr/bin/microsoft-edge-beta || true
        update-alternatives --set gnome-www-browser /usr/bin/microsoft-edge-beta || true
    fi
}

function ensure_python_runtime() {
    # If python3.14 isn't present yet, try to install it from apt (Forky/testing may provide it).
    if ! command -v python3.14 >/dev/null 2>&1; then
        echo "python3.14 not found; attempting to install python3.14 + python3.14-venv from apt (if available) ..."
        apt-get install -y --no-install-recommends python3.14 python3.14-venv >/dev/null 2>&1 || true
    fi

    local python_bin=""
    for candidate in python3.14 python3.13 python3.12 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            python_bin=$(command -v "$candidate")
            break
        fi
    done

    [[ -z $python_bin ]] && error_exit "python3 is not installed."

    local version
    version=$("$python_bin" -V 2>&1 | awk '{print $2}')

    if [[ $version != 3.14.* ]]; then
        cat <<PYWARN >&2
Python 3.14.x is required for the Monkey Head Project runtime but was not detected.
Detected: Python ${version}

Install Python 3.14 from your distribution (preferred) or build CPython 3.14.x from source.
Example build steps (mirror the Dockerfile build stage if applicable):

  apt-get install -y --no-install-recommends \
      build-essential ca-certificates curl wget xz-utils \
      libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
      libffi-dev liblzma-dev tk-dev uuid-dev

  PYTHON_FALLBACK=\${PYTHON_FALLBACK:-3.14.0}
  curl -fsSLO https://www.python.org/ftp/python/\$PYTHON_FALLBACK/Python-\$PYTHON_FALLBACK.tgz
  tar -xzf Python-\$PYTHON_FALLBACK.tgz
  cd Python-\$PYTHON_FALLBACK
  ./configure --prefix=/usr/local --enable-optimizations --with-lto --enable-shared
  make -j"\$(nproc)"
  make altinstall
  ldconfig

Re-run this installer after Python 3.14 is available (python3.14).
PYWARN
        exit 1
    fi

    echo "$python_bin"
}

function create_virtualenv() {
    local python_bin
    python_bin=$(ensure_python_runtime)

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

    echo "Installing PyGPT-net and audio Python dependencies ..."
    "$pip_bin" install --upgrade "pygpt-net>=2.6.67" pydub sounddevice soundfile

    local submodule_path="$PROJECT_ROOT/repo/pygpt-MHP"
    if [[ -d $submodule_path ]]; then
        echo "Installing local pygpt-MHP integration in editable mode ..."
        "$pip_bin" install -e "$submodule_path"
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
PDF_DIR=/opt/hueyos/memory/PDF
# Uncomment to override default log directory
# LOG_DIR=/opt/hueyos/memory/LOGS
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
    PYTHONPATH="$PROJECT_ROOT" \
    HUEYOS_CONFIG_FILE="$CONFIG_FILE" \
    HUEYOS_VENV_PYTHON="$python_bin" \
    "$python_bin" - <<'PY'
import os
from pathlib import Path
from huey.memory.PY.license_gui import show_license_gui, ConfigManager

config_path = Path(os.environ.get("HUEYOS_CONFIG_FILE", "/opt/hueyos/config/pygpt_net/config.json"))
venv_python = os.environ.get("HUEYOS_VENV_PYTHON", "/opt/hueyos/venv/bin/python")

manager = ConfigManager(str(config_path))
if manager.get_setting("license.accepted"):
    raise SystemExit(0)

try:
    show_license_gui(config_path)
except Exception as exc:  # pragma: no cover - depends on desktop availability
    print(f"License GUI could not be displayed: {exc}")
    print(f"Run '{venv_python} -m huey.memory.PY.license_cli' to accept via CLI.")
    manager.set_setting("license.accepted", False)
PY
}

function main() {
    parse_args "$@"
    ensure_root
    detect_codename
    ensure_bootstrap_tools
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
