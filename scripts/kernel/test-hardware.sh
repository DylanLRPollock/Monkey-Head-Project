#!/bin/sh
# test-hardware.sh — read-only host smoke report for the HueyOS kernel builder.
#
# Read-only by default:
#   * runs 'python3.13 -m huey.kernel_build.cli inventory --json' (Step 21
#     -> Step 7), which is the same read-only host inventory used by 'doctor'
#     and 'plan --with-inventory';
#   * performs a local /boot/initrd.img-* presence check;
#   * performs a local /boot/config-* presence check;
#   * does not write to /boot, /lib/modules, /etc, or any live host path.
#
# Opt-in GPU smoke tests (default: skipped):
#   * --gpu-smoke enables CUDA / Ollama / ComfyUI probes;
#   * those probes may load the GPU and raise its temperature;
#   * non-interactive runs require --yes; interactive runs prompt on a TTY;
#   * without --gpu-smoke the probes stay skipped with a clear reason.
#
# No gaming or stress tests are run, ever. No vendor installer is invoked.
#
# Exit codes:
#   0   all checks passed (warns and skips do not fail)
#   2   bad argument
#   4   one or more checks failed
#   90  Python 3.13 not found on PATH
#   91  repository root or src/huey not found
set -eu

JSON_MODE=0
GPU_SMOKE=0
ASSUME_YES=0
LOG_FILE=""
BOOT_DIR="${HUEY_TEST_HARDWARE_BOOT_DIR:-/boot}"

usage() {
    cat <<'EOF'
Usage: test-hardware.sh [OPTIONS]

Read-only host smoke report for the HueyOS kernel builder.

Options:
  --json          Machine-readable JSON output
  --log FILE      Write a full log to FILE
  --gpu-smoke     Enable opt-in GPU smoke tests (CUDA / Ollama / ComfyUI).
                  Requires --yes for non-interactive runs, or interactive
                  confirmation on a TTY. These probes may load the GPU and
                  raise its temperature.
  --yes, -y       Skip the interactive confirmation prompt.
  --help, -h      Show this help and exit.

Environment overrides (intended for tests):
  HUEY_TEST_HARDWARE_INVENTORY_CMD  default: python3.13 -m huey.kernel_build.cli inventory --json
  HUEY_TEST_HARDWARE_CUDA_CMD       default: python3 -c 'import torch; print(torch.cuda.get_device_name(0))'
  HUEY_TEST_HARDWARE_OLLAMA_CMD     default: ollama ps
  HUEY_TEST_HARDWARE_COMFYUI_CMD    default: pgrep -af comfyui
  HUEY_TEST_HARDWARE_BOOT_DIR       default: /boot
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_MODE=1; shift ;;
        --log)
            if [ $# -lt 2 ]; then
                printf '%s: --log requires an argument\n' "$0" >&2
                exit 2
            fi
            LOG_FILE="$2"
            shift 2
            ;;
        --gpu-smoke) GPU_SMOKE=1; shift ;;
        --yes|-y) ASSUME_YES=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *)
            printf '%s: unknown argument: %s\n' "$0" "$1" >&2
            exit 2
            ;;
    esac
done

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
repo_root=$(CDPATH= cd -- "${script_dir}/../.." && pwd -P)

if [ ! -d "${repo_root}/src/huey" ]; then
    printf '%s: cannot locate repository root (looked for %s/src/huey)\n' "$0" "$repo_root" >&2
    exit 91
fi

if ! command -v python3.13 >/dev/null 2>&1; then
    printf '%s: python3.13 not found on PATH\n' "$0" >&2
    exit 90
fi

PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPATH

log() {
    if [ -n "$LOG_FILE" ]; then
        printf '%s\n' "$*" >> "$LOG_FILE"
    fi
}

FAILURES=0

tmp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t huey-hw)
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM

# ---------------------------------------------------------------------------
# Check 1: inventory (through the CLI; env-overridable for tests)
# ---------------------------------------------------------------------------
inventory_cmd="${HUEY_TEST_HARDWARE_INVENTORY_CMD:-python3.13 -m huey.kernel_build.cli inventory --json}"
# shellcheck disable=SC2086
if sh -c "$inventory_cmd" > "$tmp_dir/inventory.json" 2> "$tmp_dir/inventory.err"; then
    INVENTORY_STATUS=pass
    INVENTORY_DETAIL=captured
else
    INVENTORY_STATUS=fail
    INVENTORY_DETAIL="inventory command failed: $(tr '\n' ' ' < "$tmp_dir/inventory.err" 2>/dev/null | cut -c1-200)"
    FAILURES=$((FAILURES + 1))
    printf '{"subcommand":"inventory","status":"error","payload":{}}\n' > "$tmp_dir/inventory.json"
fi
log "inventory: $INVENTORY_STATUS -- $INVENTORY_DETAIL"

# ---------------------------------------------------------------------------
# Check 2: initramfs presence (read-only)
# ---------------------------------------------------------------------------
if [ -d "$BOOT_DIR" ] && ls "$BOOT_DIR"/initrd.img-* >/dev/null 2>&1; then
    INITRAMFS_STATUS=pass
    INITRAMFS_DETAIL=$(ls "$BOOT_DIR"/initrd.img-* 2>/dev/null | head -3 | tr '\n' ',' | sed 's/,$//')
else
    INITRAMFS_STATUS=warn
    INITRAMFS_DETAIL="no ${BOOT_DIR}/initrd.img-* found"
fi
log "boot_initramfs: $INITRAMFS_STATUS -- $INITRAMFS_DETAIL"

# ---------------------------------------------------------------------------
# Check 3: kernel config presence (read-only)
# ---------------------------------------------------------------------------
if [ -d "$BOOT_DIR" ] && ls "$BOOT_DIR"/config-* >/dev/null 2>&1; then
    CONFIG_STATUS=pass
    CONFIG_DETAIL=$(ls "$BOOT_DIR"/config-* 2>/dev/null | head -3 | tr '\n' ',' | sed 's/,$//')
else
    CONFIG_STATUS=warn
    CONFIG_DETAIL="no ${BOOT_DIR}/config-* found"
fi
log "boot_config: $CONFIG_STATUS -- $CONFIG_DETAIL"

# ---------------------------------------------------------------------------
# Checks 4-6: GPU smoke (opt-in)
# ---------------------------------------------------------------------------
CUDA_STATUS=skip
CUDA_DETAIL="not requested (pass --gpu-smoke with --yes, or interactively)"
OLLAMA_STATUS=skip
OLLAMA_DETAIL="not requested"
COMFYUI_STATUS=skip
COMFYUI_DETAIL="not requested"

if [ "$GPU_SMOKE" = 1 ]; then
    CONFIRMED=0
    if [ "$ASSUME_YES" = 1 ]; then
        CONFIRMED=1
    elif [ -t 0 ]; then
        printf '\n' >&2
        printf 'WARNING: --gpu-smoke will run GPU-loading commands.\n' >&2
        printf 'These may raise GPU temperature. Confirm cooling is adequate.\n' >&2
        printf 'Proceed? [y/N] ' >&2
        if read -r answer; then
            case "$answer" in
                y|Y|yes|YES) CONFIRMED=1 ;;
                *) CONFIRMED=0 ;;
            esac
        else
            CONFIRMED=0
        fi
    fi

    if [ "$CONFIRMED" = 0 ]; then
        CUDA_DETAIL="confirmation not given; pass --yes for non-interactive use"
        OLLAMA_DETAIL="$CUDA_DETAIL"
        COMFYUI_DETAIL="$CUDA_DETAIL"
    else
        cuda_cmd="${HUEY_TEST_HARDWARE_CUDA_CMD:-python3 -c 'import torch; print(torch.cuda.get_device_name(0))'}"
        if sh -c "$cuda_cmd" > "$tmp_dir/cuda.out" 2> "$tmp_dir/cuda.err"; then
            CUDA_STATUS=pass
            CUDA_DETAIL=$(head -1 "$tmp_dir/cuda.out" 2>/dev/null | cut -c1-200)
            [ -n "$CUDA_DETAIL" ] || CUDA_DETAIL="(no output)"
        else
            CUDA_STATUS=fail
            CUDA_DETAIL="$(tr '\n' ' ' < "$tmp_dir/cuda.err" 2>/dev/null | cut -c1-200)"
            FAILURES=$((FAILURES + 1))
        fi

        ollama_cmd="${HUEY_TEST_HARDWARE_OLLAMA_CMD:-ollama ps}"
        if sh -c "$ollama_cmd" > "$tmp_dir/ollama.out" 2> "$tmp_dir/ollama.err"; then
            OLLAMA_STATUS=pass
            OLLAMA_DETAIL=$(head -1 "$tmp_dir/ollama.out" 2>/dev/null | cut -c1-200)
            [ -n "$OLLAMA_DETAIL" ] || OLLAMA_DETAIL="(no output)"
        else
            OLLAMA_STATUS=fail
            OLLAMA_DETAIL="$(tr '\n' ' ' < "$tmp_dir/ollama.err" 2>/dev/null | cut -c1-200)"
            FAILURES=$((FAILURES + 1))
        fi

        comfyui_cmd="${HUEY_TEST_HARDWARE_COMFYUI_CMD:-pgrep -af comfyui}"
        if sh -c "$comfyui_cmd" > "$tmp_dir/comfyui.out" 2> "$tmp_dir/comfyui.err"; then
            if [ -s "$tmp_dir/comfyui.out" ]; then
                COMFYUI_STATUS=pass
                COMFYUI_DETAIL=$(head -1 "$tmp_dir/comfyui.out" | cut -c1-200)
            else
                COMFYUI_STATUS=warn
                COMFYUI_DETAIL="comfyui process not running"
            fi
        else
            COMFYUI_STATUS=fail
            COMFYUI_DETAIL="$(tr '\n' ' ' < "$tmp_dir/comfyui.err" 2>/dev/null | cut -c1-200)"
            FAILURES=$((FAILURES + 1))
        fi
    fi
fi

log "gpu_smoke:cuda: $CUDA_STATUS -- $CUDA_DETAIL"
log "gpu_smoke:ollama: $OLLAMA_STATUS -- $OLLAMA_DETAIL"
log "gpu_smoke:comfyui: $COMFYUI_STATUS -- $COMFYUI_DETAIL"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if [ "$JSON_MODE" = 1 ]; then
    CHK_INVENTORY_STATUS="$INVENTORY_STATUS" \
    CHK_INVENTORY_DETAIL="$INVENTORY_DETAIL" \
    CHK_INITRAMFS_STATUS="$INITRAMFS_STATUS" \
    CHK_INITRAMFS_DETAIL="$INITRAMFS_DETAIL" \
    CHK_CONFIG_STATUS="$CONFIG_STATUS" \
    CHK_CONFIG_DETAIL="$CONFIG_DETAIL" \
    CHK_CUDA_STATUS="$CUDA_STATUS" \
    CHK_CUDA_DETAIL="$CUDA_DETAIL" \
    CHK_OLLAMA_STATUS="$OLLAMA_STATUS" \
    CHK_OLLAMA_DETAIL="$OLLAMA_DETAIL" \
    CHK_COMFYUI_STATUS="$COMFYUI_STATUS" \
    CHK_COMFYUI_DETAIL="$COMFYUI_DETAIL" \
    python3.13 - "$tmp_dir/inventory.json" <<'PY'
import json
import os
import sys

inv = json.load(open(sys.argv[1]))
checks = []
for name, key in (
    ("inventory", "INVENTORY"),
    ("boot_initramfs", "INITRAMFS"),
    ("boot_config", "CONFIG"),
    ("gpu_smoke:cuda", "CUDA"),
    ("gpu_smoke:ollama", "OLLAMA"),
    ("gpu_smoke:comfyui", "COMFYUI"),
):
    checks.append({
        "name": name,
        "status": os.environ.get(f"CHK_{key}_STATUS", "skip"),
        "detail": os.environ.get(f"CHK_{key}_DETAIL", ""),
    })
summary = {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
for c in checks:
    summary[c["status"]] = summary.get(c["status"], 0) + 1
print(json.dumps(
    {
        "schema_version": 1,
        "inventory": inv,
        "checks": checks,
        "summary": summary,
    },
    indent=2,
    sort_keys=True,
))
PY
else
    printf 'HueyOS host smoke report\n'
    printf '========================\n'
    printf '%-22s %-6s %s\n' "CHECK" "STATUS" "DETAIL"
    printf '%-22s %-6s %s\n' "inventory" "$INVENTORY_STATUS" "$INVENTORY_DETAIL"
    printf '%-22s %-6s %s\n' "boot_initramfs" "$INITRAMFS_STATUS" "$INITRAMFS_DETAIL"
    printf '%-22s %-6s %s\n' "boot_config" "$CONFIG_STATUS" "$CONFIG_DETAIL"
    printf '%-22s %-6s %s\n' "gpu_smoke:cuda" "$CUDA_STATUS" "$CUDA_DETAIL"
    printf '%-22s %-6s %s\n' "gpu_smoke:ollama" "$OLLAMA_STATUS" "$OLLAMA_DETAIL"
    printf '%-22s %-6s %s\n' "gpu_smoke:comfyui" "$COMFYUI_STATUS" "$COMFYUI_DETAIL"
    printf '\n'
    if [ "$FAILURES" -gt 0 ]; then
        printf 'Result: FAIL (%d failing check(s))\n' "$FAILURES"
    else
        printf 'Result: OK\n'
    fi
fi

if [ "$FAILURES" -gt 0 ]; then
    exit 4
fi
exit 0
