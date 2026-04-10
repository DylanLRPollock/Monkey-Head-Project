#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <role: core|pulse|lab> <output-config> [kernel-config-dir]" >&2
  exit 1
fi

ROLE="$1"
OUTPUT_CONFIG="$2"
KERNEL_CONFIG_DIR="${3:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
BASE_CONFIG="${KERNEL_CONFIG_DIR}/base.config"

if [[ ! -f "${BASE_CONFIG}" ]]; then
  echo "Missing base config: ${BASE_CONFIG}" >&2
  exit 1
fi

case "${ROLE}" in
  core)
    ROLE_CONFIG="${KERNEL_CONFIG_DIR}/core.config"
    ;;
  pulse)
    ROLE_CONFIG="${KERNEL_CONFIG_DIR}/pulse.config"
    ;;
  lab)
    ROLE_CONFIG="${KERNEL_CONFIG_DIR}/lab.config"
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

  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" =~ ^#[[:space:]]*include[[:space:]]+(.+)$ ]]; then
      local include_rel="${BASH_REMATCH[1]}"
      local include_file="${root_dir}/${include_rel}"
      if [[ ! -f "${include_file}" ]]; then
        echo "Missing included fragment: ${include_file}" >&2
        exit 1
      fi
      expand_config "${include_file}" "${root_dir}"
    else
      printf '%s\n' "${line}"
    fi
  done < "${input}"
}

tmp_role="$(mktemp)"
trap 'rm -f "${tmp_role}"' EXIT
expand_config "${ROLE_CONFIG}" "${KERNEL_CONFIG_DIR}" > "${tmp_role}"

cat "${BASE_CONFIG}" "${tmp_role}" > "${OUTPUT_CONFIG}"
echo "Assembled kernel config for role '${ROLE}' -> ${OUTPUT_CONFIG}" >&2
