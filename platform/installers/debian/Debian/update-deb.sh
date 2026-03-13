#!/usr/bin/env bash
# HueyOS Debian Forky Updater Script
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
#   Updates HueyOS components on Debian Forky.
#   - Updates Python dependencies using the same requirements layout as install.sh
#   - Reinstalls the project in editable mode
#   - Optionally updates system packages and/or pulls latest git changes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_INSTALL_DIR="/opt/hueyos"

# Target codename for optional system updates (override via env var)
DEBIAN_CODENAME="${DEBIAN_CODENAME:-forky}"

# Options
DO_SYSTEM_UPDATE=0
DO_GIT_PULL=0
FORCE_GIT=0
EXTRA_GROUPS=()

function usage() {
    cat <<USAGE
Usage: $0 [options]

Options:
  --system              Align apt sources to DEBIAN_CODENAME and run apt update + dist-upgrade.
  --pull                If this is a git checkout, fetch + fast-forward pull updates.
  --force-git           Pull even if the working tree is dirty (not recommended).
  --extras LIST         Comma separated Python extras to update (ml,data,cloud).
  -h, --help            Show this help and exit.

Environment:
  DEBIAN_CODENAME       Target apt codename (default: forky). Used only with --system.
                        Example: DEBIAN_CODENAME=testing sudo ./update.sh --system
USAGE
}

function error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

function parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --system)
                DO_SYSTEM_UPDATE=1
                shift
                ;;
            --pull)
                DO_GIT_PULL=1
                shift
                ;;
            --force-git)
                FORCE_GIT=1
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

function find_project_root() {
    # Prefer installed location, then script location, then parent, then CWD.
    local candidates=(
        "$DEFAULT_INSTALL_DIR"
        "$SCRIPT_DIR"
        "$SCRIPT_DIR/.."
        "$(pwd)"
    )

    for c in "${candidates[@]}"; do
        if [[ -d "$c" ]]; then
            if [[ -f "$c/requirements/requirements-core.txt" || -f "$c/requirements.txt" || -f "$c/pyproject.toml" ]]; then
                echo "$(cd "$c" && pwd)"
                return 0
            fi
        fi
    done

    error_exit "Unable to locate project root. Expected requirements/requirements-core.txt, requirements.txt, or pyproject.toml."
}

function find_venv_dir() {
    local project_root="$1"

    # Respect pre-set VENV_DIR if provided as env var.
    if [[ -n "${VENV_DIR:-}" && -d "${VENV_DIR:-}" ]]; then
        echo "$VENV_DIR"
        return 0
    fi

    local candidates=(
        "$project_root/venv"
        "$DEFAULT_INSTALL_DIR/venv"
        "$SCRIPT_DIR/venv"
        "$(pwd)/venv"
    )

    for v in "${candidates[@]}"; do
        if [[ -d "$v" && -x "$v/bin/python" ]]; then
            echo "$v"
            return 0
        fi
    done

    error_exit "Virtual environment not found. Please run the installation script first (expected venv at $project_root/venv or $DEFAULT_INSTALL_DIR/venv)."
}

function run_as_root() {
    # Usage: run_as_root <cmd...>
    if [[ $EUID -eq 0 ]]; then
        "$@"
    else
        if command -v sudo >/dev/null 2>&1; then
            sudo "$@"
        else
            error_exit "This operation requires root, but sudo is not available. Re-run as root."
        fi
    fi
}

function update_system_packages() {
    export DEBIAN_FRONTEND=noninteractive

    local project_root="$1"
    local updater=""
    local audio_packages=(
        ffmpeg
        libasound2-dev
        libportaudio2
        libportaudiocpp0
        portaudio19-dev
        libsndfile1
    )

    echo "System update requested. Target apt codename: ${DEBIAN_CODENAME}"

    # Locate an apt-sources updater helper (same detection logic style as install.sh)
    local candidates=(
        "$project_root/huey/memory/PY/update_sources_to_forky.py"
        "$project_root/huey/memory/PY/update_sources_to_testing.py"
        "$project_root/huey/memory/PY/update_sources_to_codename.py"
        "$project_root/huey/memory/PY/update_sources_to_debian.py"
        "$project_root/huey/memory/PY/update_sources_to_trixie.py"
    )

    for c in "${candidates[@]}"; do
        if [[ -f "$c" ]]; then
            updater="$c"
            break
        fi
    done

    if [[ -z "$updater" ]]; then
        echo "WARNING: No apt-sources updater helper found under $project_root/huey/memory/PY. Skipping sources alignment." >&2
    else
        echo "Aligning apt sources via: $updater"
        run_as_root python3 "$updater" "$DEBIAN_CODENAME"
    fi

    echo "Running apt update + dist-upgrade ..."
    run_as_root apt-get update -y
    run_as_root apt-get dist-upgrade -y

    echo "Ensuring audio runtime packages for PyGPT/PyGPT-net are installed ..."
    run_as_root apt-get install -y --no-install-recommends "${audio_packages[@]}"
}

function git_pull_updates() {
    local project_root="$1"

    if ! command -v git >/dev/null 2>&1; then
        echo "WARNING: git is not installed; skipping --pull." >&2
        return 0
    fi

    if [[ ! -d "$project_root/.git" ]]; then
        echo "INFO: No .git directory found at $project_root; skipping --pull."
        return 0
    fi

    pushd "$project_root" >/dev/null

    if [[ $FORCE_GIT -eq 0 ]]; then
        if [[ -n "$(git status --porcelain 2>/dev/null || true)" ]]; then
            echo "WARNING: Working tree has local changes; skipping pull. Use --force-git to override." >&2
            popd >/dev/null
            return 0
        fi
    fi

    echo "Fetching git updates ..."
    git fetch --all --prune

    echo "Pulling fast-forward updates (if available) ..."
    # --ff-only avoids accidental merge commits in automation
    git pull --ff-only || {
        echo "WARNING: git pull --ff-only failed (non-FF or other issue). Resolve manually if needed." >&2
    }

    popd >/dev/null
}

function ensure_python_runtime_in_venv() {
    local venv_dir="$1"
    local py_bin="$venv_dir/bin/python"
    local ver
    ver=$("$py_bin" -V 2>&1 | awk '{print $2}' || true)

    if [[ -z "$ver" ]]; then
        error_exit "Unable to determine Python version from venv: $py_bin"
    fi

    if [[ "$ver" != 3.14.* ]]; then
        cat <<PYWARN >&2
Python 3.14.x is required for the Monkey Head Project runtime.
Detected venv Python: ${ver}

If this environment was created with the wrong interpreter, re-run install.sh after
Python 3.14 is available and rebuild the virtual environment.
PYWARN
        exit 1
    fi
}

function update_python_deps() {
    local project_root="$1"
    local venv_dir="$2"
    local pip_bin="$venv_dir/bin/pip"

    [[ -x "$pip_bin" ]] || error_exit "pip not found in venv: $pip_bin"

    echo "Upgrading pip/setuptools/wheel ..."
    "$pip_bin" install --upgrade pip setuptools wheel

    # Base dependencies
    if [[ -f "$project_root/requirements/requirements-core.txt" ]]; then
        echo "Updating core Python dependencies (requirements/requirements-core.txt) ..."
        "$pip_bin" install --upgrade -r "$project_root/requirements/requirements-core.txt"
    elif [[ -f "$project_root/requirements.txt" ]]; then
        echo "Updating Python dependencies (requirements.txt) ..."
        "$pip_bin" install --upgrade -r "$project_root/requirements.txt"
    else
        echo "WARNING: No requirements file found; skipping base dependency update." >&2
    fi

    echo "Reinstalling project in editable mode ..."
    "$pip_bin" install -e "$project_root"

    echo "Updating PyGPT-net and audio Python dependencies ..."
    "$pip_bin" install --upgrade "pygpt-net>=2.6.67" pydub sounddevice soundfile

    local submodule_path="$project_root/repo/pygpt-MHP"
    if [[ -d "$submodule_path" ]]; then
        echo "Reinstalling local pygpt-MHP integration in editable mode ..."
        "$pip_bin" install -e "$submodule_path"
    fi

    # Optional extras
    declare -A extras_map=(
        [ml]="requirements/requirements-ml.txt"
        [data]="requirements/requirements-data.txt"
        [cloud]="requirements/requirements-cloud.txt"
    )

    if [[ ${#EXTRA_GROUPS[@]} -gt 0 ]]; then
        for extra in "${EXTRA_GROUPS[@]}"; do
            extra=${extra,,}
            if [[ -n "${extras_map[$extra]:-}" ]]; then
                local req_file="$project_root/${extras_map[$extra]}"
                if [[ -f "$req_file" ]]; then
                    echo "Updating optional '${extra}' dependencies ..."
                    "$pip_bin" install --upgrade -r "$req_file"
                else
                    echo "Skipping missing requirements file: $req_file" >&2
                fi
            else
                echo "Unknown extras group '$extra' (supported: ml,data,cloud)" >&2
            fi
        done
    fi
}

function run_post_update_checks() {
    local project_root="$1"
    local venv_dir="$2"
    local py_bin="$venv_dir/bin/python"

    if [[ -f "$project_root/huey/memory/PY/sync_pygpt_structure.py" ]]; then
        echo "Synchronising pygpt structure ..."
        "$py_bin" "$project_root/huey/memory/PY/sync_pygpt_structure.py" || \
            echo "Warning: sync_pygpt_structure.py failed" >&2
    fi

    if [[ -f "$project_root/huey/memory/PY/check_inter_program_connectivity.py" ]]; then
        echo "Checking inter-program connectivity ..."
        "$py_bin" "$project_root/huey/memory/PY/check_inter_program_connectivity.py" || \
            echo "Warning: connectivity check failed" >&2
    fi

    echo "Preloading bundled data ..."
    "$py_bin" -m huey.memory.PY.preload_data --summary || \
        echo "Warning: preload_data reported an issue" >&2
}

function main() {
    parse_args "$@"

    local project_root
    project_root="$(find_project_root)"
    local venv_dir
    venv_dir="$(find_venv_dir "$project_root")"

    echo "Project root: $project_root"
    echo "Virtualenv:    $venv_dir"

    if [[ $DO_SYSTEM_UPDATE -eq 1 ]]; then
        update_system_packages "$project_root"
    fi

    if [[ $DO_GIT_PULL -eq 1 ]]; then
        git_pull_updates "$project_root"
    fi

    ensure_python_runtime_in_venv "$venv_dir"
    update_python_deps "$project_root" "$venv_dir"
    run_post_update_checks "$project_root" "$venv_dir"

    echo "Update completed successfully."
}

main "$@"

