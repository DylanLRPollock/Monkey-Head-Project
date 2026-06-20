#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: scripts/kernel/assemble_config.sh <role: core|pulse|lab> <output-config> [kernel-config-dir]

Build a kernel .config by layering src/huey/core/base.config with a role profile.
Supports role fragments via lines like: # include fragments/<name>.config
Uses merge_config.sh when available, otherwise uses a deterministic fallback.
USAGE
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 1
fi

ROLE="$1"
OUTPUT_CONFIG="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
KERNEL_CONFIG_DIR="${3:-${REPO_ROOT}/src/huey/core}"
BASE_CONFIG="${KERNEL_CONFIG_DIR}/base.config"

if [[ ! -f "${BASE_CONFIG}" ]]; then
  echo "Missing base config: ${BASE_CONFIG}" >&2
  exit 1
fi

case "${ROLE}" in
  core|pulse|lab)
    ROLE_CONFIG="${KERNEL_CONFIG_DIR}/${ROLE}.config"
    ;;
  *)
    echo "Unsupported role '${ROLE}'. Expected one of: core, pulse, lab." >&2
    exit 1
    ;;
esac

if [[ ! -f "${ROLE_CONFIG}" ]]; then
  echo "Missing role config: ${ROLE_CONFIG}" >&2
  exit 1
fi

expand_config() {
  local input="$1"
  local root_dir="$2"
  local stack="${3:-}"

  local abs_input
  abs_input="$(cd "$(dirname "${input}")" && pwd)/$(basename "${input}")"

  if [[ ":${stack}:" == *":${abs_input}:"* ]]; then
    echo "Detected recursive include while expanding ${abs_input}" >&2
    exit 1
  fi

  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" =~ ^#[[:space:]]*include[[:space:]]+(.+)$ ]]; then
      local include_rel="${BASH_REMATCH[1]}"
      local include_file="${root_dir}/${include_rel}"
      if [[ ! -f "${include_file}" ]]; then
        echo "Missing included fragment: ${include_file}" >&2
        exit 1
      fi
      expand_config "${include_file}" "${root_dir}" "${stack}:${abs_input}"
    else
      printf '%s\n' "${line}"
    fi
  done < "${input}"
}

find_merge_config() {
  local candidates=()

  if [[ -n "${MERGE_CONFIG_SH:-}" ]]; then
    candidates+=("${MERGE_CONFIG_SH}")
  fi

  candidates+=(
    "${SCRIPT_DIR}/merge_config.sh"
    "${REPO_ROOT}/scripts/kconfig/merge_config.sh"
    "${REPO_ROOT}/linux/scripts/kconfig/merge_config.sh"
  )

  if command -v merge_config.sh >/dev/null 2>&1; then
    candidates+=("$(command -v merge_config.sh)")
  fi

  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -n "${candidate}" && -f "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done

  return 1
}

deterministic_merge() {
  local base="$1"
  local role="$2"
  local output="$3"

  awk '
    function emit_ordered(  i, key) {
      for (i = 1; i <= count; i++) {
        key = order[i]
        print final[key]
      }
    }

    function parse_key(line, key) {
      key = ""
      if (match(line, /^CONFIG_[A-Za-z0-9_]+=.*/)) {
        key = substr(line, 1, index(line, "=") - 1)
      } else if (match(line, /^# CONFIG_[A-Za-z0-9_]+ is not set$/)) {
        key = line
        sub(/^# /, "", key)
        sub(/ is not set$/, "", key)
      }
      return key
    }

    {
      key = parse_key($0)

      if (key == "") {
        key = sprintf("__LINE__%09d", NR)
      }

      if (!(key in seen)) {
        seen[key] = 1
        count += 1
        order[count] = key
      }

      final[key] = $0
    }

    END {
      emit_ordered()
    }
  ' "${base}" "${role}" > "${output}"
}

mkdir -p "$(dirname "${OUTPUT_CONFIG}")"

temp_dir="$(mktemp -d)"
trap 'rm -rf "${temp_dir}"' EXIT

EXPANDED_ROLE_CONFIG="${temp_dir}/role.expanded.config"
expand_config "${ROLE_CONFIG}" "${KERNEL_CONFIG_DIR}" > "${EXPANDED_ROLE_CONFIG}"

if MERGE_CONFIG_PATH="$(find_merge_config)"; then
  cp "${BASE_CONFIG}" "${temp_dir}/.config"
  (cd "${temp_dir}" && bash "${MERGE_CONFIG_PATH}" -m .config "${EXPANDED_ROLE_CONFIG}" >/dev/null)
  cp "${temp_dir}/.config" "${OUTPUT_CONFIG}"
  echo "Assembled kernel config for role '${ROLE}' using merge_config.sh -> ${OUTPUT_CONFIG}" >&2
else
  deterministic_merge "${BASE_CONFIG}" "${EXPANDED_ROLE_CONFIG}" "${OUTPUT_CONFIG}"
  echo "Assembled kernel config for role '${ROLE}' using deterministic fallback -> ${OUTPUT_CONFIG}" >&2
fi
