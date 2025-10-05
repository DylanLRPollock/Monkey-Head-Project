#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=${PYTHON:-python3}
DEFAULT_VERSION="6.16.12"

print_help() {
  cat <<USAGE
Usage: $(basename "$0") [version] [-- [extra args]]

version      Optional kernel version (defaults to ${DEFAULT_VERSION}).
extra args   Arguments passed verbatim to build_kernel.py after a "--" separator.

Environment variables:
  PYTHON     Python interpreter to use (default: python3).

Examples:
  $(basename "$0")
  $(basename "$0") 6.16.11 -- -j16
USAGE
}

if [[ ${1-} == "--help" || ${1-} == "-h" ]]; then
  print_help
  exit 0
fi

VERSION="$DEFAULT_VERSION"
if [[ $# -gt 0 && $1 != "--" ]]; then
  VERSION="$1"
  shift
fi

exec "$PYTHON" "$SCRIPT_DIR/build_kernel.py" --version "$VERSION" "$@"
