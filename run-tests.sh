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
# This script is used to run the tests using the virtual environment
usage() {
    cat <<EOF
Usage: $0 [options]

Options:
  -h, --help            Show this help message and exit
  -l, --log FILE        Write test results to FILE
  -m, --module MODULE   Run tests only for the given module or file
      --no-cov          Run tests without coverage reporting
EOF
}

parse_args() {
    MODULE=""
    COV_ARGS=(--cov=monkey_head --cov-report=term)
    LOG_FILE="logs/test_results.log"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -l|--log)
                LOG_FILE="$2"
                shift 2
                ;;
            -m|--module)
                MODULE="$2"
                shift 2
                ;;
            --no-cov)
                COV_ARGS=()
                shift
                ;;
            *)
                echo "Unknown option: $1" >&2
                usage >&2
                exit 1
                ;;
        esac
    done
}

check_venv() {
    if [ ! -f "venv/bin/activate" ]; then
      echo "Virtual environment not found. Please run install.sh first." >&2
      exit 1
    fi
}

run_tests() {
    LOG_DIR="$(dirname "$LOG_FILE")"
    mkdir -p "$LOG_DIR"
    echo "Test run started at $(date)" | tee "$LOG_FILE"

    source ./venv/bin/activate
    local args=(pytest -vv)
    if [ -n "$MODULE" ]; then
        args+=("$MODULE")
    fi
    args+=("${COV_ARGS[@]}")
    "${args[@]}" | tee -a "$LOG_FILE"
}

parse_args "$@"
check_venv
run_tests
