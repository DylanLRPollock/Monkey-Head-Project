#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_dispatch.sh"
huey_exec_memory_sh "rst_to_md.sh" "$@"
