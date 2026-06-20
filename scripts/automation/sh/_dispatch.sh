#!/usr/bin/env bash
set -euo pipefail

huey_find_repo_root() {
  local start_path="$1"
  while [[ -n "$start_path" ]]; do
    if [[ -f "$start_path/pyproject.toml" && -f "$start_path/run.py" ]]; then
      printf '%s\n' "$start_path"
      return 0
    fi

    local parent
    parent="$(dirname "$start_path")"
    if [[ "$parent" == "$start_path" ]]; then
      break
    fi
    start_path="$parent"
  done

  return 1
}

huey_exec_memory_sh() {
  local script_name="$1"
  shift || true

  local script_dir repo_root target
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(huey_find_repo_root "$script_dir")" || {
    echo "Could not locate the Huey repository root from '$script_dir'." >&2
    exit 1
  }

  target="$repo_root/src/huey/memory/SH/$script_name"
  if [[ ! -f "$target" ]]; then
    echo "Remembered shell script not found: $target" >&2
    exit 1
  fi

  exec bash "$target" "$@"
}
