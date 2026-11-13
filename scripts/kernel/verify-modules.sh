#!/bin/sh
# Thin wrapper for the HueyOS kernel builder CLI: verify subcommand.
#
# Purpose
# -------
# Offline verification of a release directory (Step 19's
# ReleaseVerifier). No network, no host inspection. Reads only the
# release tree and invokes the read-only tools dpkg-deb, modinfo, and
# lsinitramfs through the CLI's audited Runner -- never directly from
# this script.
#
# Host read-only check
# --------------------
# If the first argument is '--host-read-only', this wrapper routes to
# the CLI's 'inventory' subcommand instead, which performs a read-only
# snapshot of the running host (uname, mokutil --sb-state, lspci,
# nvidia-smi --query, modinfo of the *loaded* nvidia module, dkms
# status). This is the explicit, separate host check the handoff calls
# for, and it must never be conflated with staged-module verification:
#   * verify  -> reads staged .ko files under --release-dir
#   * inventory -> reads the currently running host
# Passing '--host-read-only' anywhere other than first is forwarded
# verbatim to the CLI and will be rejected by argparse; call it as the
# first argument to invoke the host check.
#
# This wrapper never invokes modinfo, dpkg-deb, lsinitramfs, nvidia-smi,
# dkms, nvidia-installer, or any network tool (curl/wget/apt/pip)
# directly, and never references /boot, /lib/modules, /etc/modprobe.d,
# or /etc/initramfs-tools in executable code.
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

# Explicit host-read-only dispatch: only as the first argument so that
# every other argument is preserved exactly and unambiguously.
if [ "${1:-}" = "--host-read-only" ]; then
    shift
    exec python3.13 -m huey.kernel_build.cli inventory "$@"
fi

exec python3.13 -m huey.kernel_build.cli verify "$@"
