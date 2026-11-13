#!/bin/sh
# Thin wrapper for the HueyOS kernel builder CLI: build-nvidia subcommand.
#
# This script contains no build logic and performs no installation. It
# locates the repository root from its own path, ensures Python 3.13 is
# on PATH, prepends the checkout's src/ to PYTHONPATH, and execs the CLI.
# All argv, --help, --dry-run, and exit codes pass through unchanged.
#
# This wrapper never runs the vendor .run installer, never calls
# 'dkms install', never runs 'dpkg -i', and never writes to /boot or
# /lib/modules. Module staging is entirely a CLI responsibility (Step 21
# -> Step 14).
#
# Exit codes:
#   0..N  forwarded from the CLI (see huey.kernel_build.cli.ExitCode)
#   90    Python 3.13 not found on PATH
#   91    repository root or src/huey not found from this script's location
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
repo_root=$(CDPATH= cd -- "${script_dir}/../.." && pwd -P)

if [ ! -d "${repo_root}/src/huey" ]; then
    printf '%s: cannot locate repository root (looked for %s/src/huey)\n' \
        "$0" "${repo_root}" >&2
    exit 91
fi

if ! command -v python3.13 >/dev/null 2>&1; then
    printf '%s: python3.13 not found on PATH\n' "$0" >&2
    exit 90
fi

PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPATH

exec python3.13 -m huey.kernel_build.cli build-nvidia "$@"
