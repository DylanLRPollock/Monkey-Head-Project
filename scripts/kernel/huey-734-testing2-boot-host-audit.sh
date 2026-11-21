#!/usr/bin/env bash
# Read-only inventory: running Debian boot/RAID state, current initramfs,
# and security mitigation context for HueyOS 7.3.4 testing2.
# NO generation/install of initramfs; no filesystem, mdadm, kernel or NVIDIA changes.
set -Eeuo pipefail
umask 077

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || fail 'Run as a normal user, without sudo.'

ROOT="$HOME/huey-kernel-734"
CONFIG="$ROOT/output/testing2-compile/.config"
REPORT="$ROOT/reports/testing2"
OUT="$REPORT/boot-host-readiness.txt"
[[ -d "$REPORT" && -r "$CONFIG" ]] || fail 'Missing previously built testing2 configuration or report directory.'
[[ ! -e "$OUT" ]] || fail "Existing report $OUT; preserve it rather than overwriting."
for command_name in cat grep awk sha256sum findmnt lsblk uname lsmod; do
  command -v "$command_name" >/dev/null 2>&1 || fail "Required read-only command missing: $command_name"
done
expected_config='db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3'
actual_config="$(sha256sum "$CONFIG" | awk '{print $1}')"
[[ "$actual_config" == "$expected_config" ]] || fail 'Testing2 Kconfig hash changed. Stop before inspection.'

TMP="$(mktemp -d "$REPORT/.boot-inventory.XXXXXXXX")"
trap 'rm -rf -- "$TMP"' EXIT

{
  printf 'HueyOS Linux 7.3.4-huey-testing2 — READ-ONLY host boot readiness\n'
  printf 'Recorded state: current Debian host only; no new initramfs generated\n\n'

  printf '=== Running kernel and boot mounts ===\n'
  printf 'Current kernel: %s\n' "$(uname -r)"
  findmnt -n -T / -o TARGET,SOURCE,FSTYPE,OPTIONS || true
  for mount_path in /boot /boot/efi; do
    printf 'Exact mountpoint %s: ' "$mount_path"
    findmnt -n -M "$mount_path" -o SOURCE,FSTYPE,TARGET || printf 'not a separate mount\n'
  done
  printf '\nKernel boot parameters relevant to root/resume:\n'
  tr ' ' '\n' </proc/cmdline | grep -E '^(root|resume|rootflags|rootfstype)=' || true
  printf '\nBlock devices (no disk serial numbers):\n'
  lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS || true

  printf '\n=== mdadm / RAID visibility (read only) ===\n'
  if [[ -r /proc/mdstat ]]; then cat /proc/mdstat; else printf '/proc/mdstat unreadable\n'; fi
  if command -v mdadm >/dev/null 2>&1; then
    printf '\nmdadm arrays (scan only):\n'
    mdadm --detail --scan 2>&1 || true
  elif [[ -x /usr/sbin/mdadm ]]; then
    printf '\nmdadm arrays (scan only):\n'
    /usr/sbin/mdadm --detail --scan 2>&1 || true
  else
    printf '\nWARN: mdadm executable not found on PATH or /usr/sbin.\n'
  fi

  printf '\n=== Currently installed boot artifacts ===\n'
  for file in /boot/vmlinuz-* /boot/initrd.img-*; do
    [[ -f "$file" ]] && stat -c '%n | %s bytes' "$file"
  done

  printf '\n=== Current initramfs audit (not HueyOS) ===\n'
  CURRENT="/boot/initrd.img-$(uname -r)"
  if [[ -r "$CURRENT" ]] && command -v lsinitramfs >/dev/null 2>&1; then
    if lsinitramfs "$CURRENT" > "$TMP/initrd-list" 2>"$TMP/list-errors"; then
      printf 'Current initramfs: %s\n' "$CURRENT"
      printf 'mdadm files in current initramfs:\n'
      grep -E '(^|/)(mdadm|mdadm.conf|mdadm.conf.d|local-top/mdadm)(/|$)' "$TMP/initrd-list" | head -n 15 || true
      for driver in vmd nvme nvme-core md-mod raid0 raid1 raid10 btrfs i915 amdgpu; do
        if grep -Eq "(^|/)$driver[.]ko([.](gz|xz|zst))?$" "$TMP/initrd-list"; then
          printf 'PRESENT current initramfs module: %s\n' "$driver"
        else
          printf 'NOT FOUND current initramfs module: %s (may be built-in or unused)\n' "$driver"
        fi
      done
    else
      printf 'WARN: Cannot list current initramfs contents.\n'
      cat "$TMP/list-errors"
    fi
  else
    printf 'WARN: current initramfs not readable or lsinitramfs unavailable: %s\n' "$CURRENT"
  fi

  printf '\n=== Security mitigation context (read only) ===\n'
  if command -v mokutil >/dev/null 2>&1; then mokutil --sb-state 2>&1 || true; fi
  grep -E '^CONFIG_(MITIGATION_RETHUNK|RETHUNK|OBJTOOL_WERROR|MODULE_SIG_FORCE|MODULE_SIG_ALL|DEBUG_INFO_BTF)=' "$CONFIG" || true
  for vulnerability in retbleed spec_rstack_overflow spectre_v2; do
    p="/sys/devices/system/cpu/vulnerabilities/$vulnerability"
    if [[ -r "$p" ]]; then printf '%s: ' "$vulnerability"; cat "$p"; fi
  done
  printf '\nLoaded display / compute modules (names only):\n'
  lsmod | awk 'NR==1 || $1 ~ /^(nvidia|nvidia_uvm|nvidia_modeset|nvidia_drm|i915|amdgpu)$/ {print $1}' || true

  printf '\n=== No actions taken ===\n'
  printf 'This is a running-system inventory, NOT approval for installation, boot, or new initramfs.\n'
  printf 'Review any missing mdadm or VMD/NVMe/RAID10/Btrfs hooks before attempting to boot testing2.\n'
} > "$OUT"

printf 'PASS: saved read-only boot-host inventory at %s\n' "$OUT"
printf 'No initramfs generated, no kernel/NVIDIA modules installed or loaded, no RAID changes or reboot.\n'
