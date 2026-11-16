#!/usr/bin/env bash
# Read-only companion ESP, stale mdadm entry, and GRUB fallback audit.
# No block writes, mount, file system repair, boot entry changes or reboot.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || fail 'Run as your normal user, not sudo.'
ROOT="$HOME/huey-kernel-734"
REPORT="$ROOT/reports/testing2/efi-recovery-readonly.txt"
[[ -d "$ROOT/reports/testing2" ]] || fail 'Missing reports/testing2 directory.'
[[ ! -e "$REPORT" ]] || fail "Report already exists; refusing to overwrite: $REPORT"
for cmd in lsblk findmnt grep sed tee sudo; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing command: $cmd"
done

# This escalates only the read-only inspection commands in the report.
sudo -v || fail 'sudo authentication required for the read-only audit.'

{
  printf '%s\n' 'HueyOS 7.3.4 testing2 — read-only EFI recovery / stale RAID audit'
  printf '%s\n\n' 'No writes to disk, mdadm configuration, EFI NVRAM or /boot.'

  printf '%s\n' '=== PARTUUID, filesystem signature and EFI partition type mapping ==='
  lsblk -o NAME,SIZE,TYPE,FSTYPE,PARTTYPE,PARTUUID,PARTLABEL,MOUNTPOINTS
  printf '\nCurrent ESP mount:\n'
  findmnt -n -M /boot/efi -o SOURCE,FSTYPE,TARGET || true
  printf '\nKnown SSD partition signature probes (read-only):\n'
  sudo blkid -p /dev/sdc1 /dev/sdd1 2>&1 || true
  printf '\nSecond SSD EFI candidate signatures (wipefs -n; no change):\n'
  sudo wipefs -n /dev/sdd1 2>&1 || true

  printf '\n=== Firmware entries and current firmware selection ===\n'
  if command -v efibootmgr >/dev/null 2>&1; then
    sudo efibootmgr -v || true
  else
    printf 'efibootmgr not installed\n'
  fi

  printf '\n=== GRUB loader bridge in existing mounted ESP ===\n'
  if [[ -f /boot/efi/EFI/debian/grub.cfg ]]; then
    sudo sed -n '1,60p' /boot/efi/EFI/debian/grub.cfg
  else
    printf 'No /boot/efi/EFI/debian/grub.cfg on mounted ESP\n'
  fi
  printf '\nExisting GRUB kernel menu entries (maximum 30 lines):\n'
  if [[ -f /boot/grub/grub.cfg ]]; then
    sudo grep -E '^[[:space:]]*(menuentry|submenu)[[:space:]]' /boot/grub/grub.cfg | \
      sed -n '1,30p' || true
  else
    printf 'No /boot/grub/grub.cfg; investigate bootloader layout\n'
  fi
  printf '\nCurrent GRUB default and timeout policy:\n'
  if [[ -f /etc/default/grub ]]; then
    sudo grep -E '^GRUB_(DEFAULT|TIMEOUT|TIMEOUT_STYLE|DISABLE_SUBMENU)=' \
      /etc/default/grub || true
  fi

  printf '\n=== RAID metadata and native 10TB Btrfs identifiers ===\n'
  sudo mdadm --detail --scan || true
  printf '\nmdadm.conf array identifiers (comparison only):\n'
  sudo grep -E '^[[:space:]]*ARRAY[[:space:]]' /etc/mdadm/mdadm.conf || true
  printf '\n10TB physical disk partition signatures (wipefs -n only):\n'
  for partition in /dev/sda1 /dev/sdb1; do
    if [[ -b "$partition" ]]; then
      sudo wipefs -n "$partition" || true
    fi
  done
  if command -v btrfs >/dev/null 2>&1 && [[ -d /10TB ]]; then
    printf '\nNative Btrfs filesystem devices for /10TB:\n'
    sudo btrfs filesystem show /10TB || true
  fi

  printf '\n=== Final reminder ===\n'
  printf '%s\n' 'This inventory is not proof Boot0005 is functional and is not authorization to install or reboot.'
} 2>&1 | tee "$REPORT"

printf 'Read-only report: %s\n' "$REPORT"
