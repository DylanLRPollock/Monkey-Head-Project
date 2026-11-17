#!/usr/bin/env bash
# Inspect the EXACT verified testing2 initramfs content inside private staging.
# Never install, execute extracted files, modify GRUB/RAID/EFI, or reboot.
set -Eeuo pipefail
umask 077
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || die 'Run as normal user without sudo.'

KR=7.3.4-huey-testing2
ROOT="$HOME/huey-kernel-734"
REPORT="$ROOT/reports/testing2"
IMAGE="$ROOT/output/testing2-initramfs-isolated/work/fakeroot-retry1/initrd.img-$KR"
EXTRACT="$ROOT/output/testing2-initramfs-content-audit"
LOG="$REPORT/testing2-initramfs-content-extract.log"
AUDIT="$REPORT/testing2-initramfs-content-audit.txt"
EXPECTED_IMAGE_SHA='ddcc9e6c238a3c744adca38903c5d4ffcf8c4393ee1517576860a85812cb5bdd'
EXPECTED_ROOT_MD='f3c8b907:d3b5a85f:a2578548:157bf1d2'
EXPECTED_ROOT_FS='dddebb01-4f58-4782-82b3-0e77209afc8c'
STALE_MD3='38a8dd4b:f15c5eca:fafe213a:2962ac03'

for cmd in bwrap sha256sum awk grep stat df findmnt sed install; do
  command -v "$cmd" >/dev/null 2>&1 || die "Missing executable $cmd"
done
UNPACK="$(command -v unmkinitramfs || true)"
if [[ -z "$UNPACK" && -x /usr/bin/unmkinitramfs ]]; then
  UNPACK=/usr/bin/unmkinitramfs
elif [[ -z "$UNPACK" && -x /usr/sbin/unmkinitramfs ]]; then
  UNPACK=/usr/sbin/unmkinitramfs
fi
[[ -n "$UNPACK" && -x "$UNPACK" ]] || die 'unmkinitramfs not installed.'
[[ -s "$IMAGE" && -d "$REPORT" ]] || die 'Missing archive or report directory.'
for p in "$EXTRACT" "$LOG" "$AUDIT"; do
  [[ ! -e "$p" ]] || die "Previous audit output exists; refusing overwrite $p"
done
actual="$(sha256sum "$IMAGE" | awk '{print $1}')"
[[ "$actual" == "$EXPECTED_IMAGE_SHA" ]] || die "Archive SHA-256 has changed: $actual"
[[ ! -e "/boot/vmlinuz-$KR" ]] || die 'Testing2 appears installed; stop for review.'
available="$(df -Pk "$ROOT/output" | awk 'NR==2 {print $4}')"
[[ "$available" =~ ^[0-9]+$ ]] && (( available >= 4 * 1024 * 1024 )) || \
  die 'At least 4 GiB free required for private extraction.'
printf 'PASS: exact initramfs SHA-256 verified (%s)\n' "$actual"

install -d -m 0700 "$EXTRACT"
printf '%s\n' 'STEP 1 — Extract private initramfs content without root or host writes.'
# Only the new extraction directory is writable within the sandbox.
# Archive is trusted only after its pinned digest passes. Do not execute
# extracted programs/scripts; inspect files as data.
if bwrap --unshare-net --die-with-parent \
    --ro-bind / / --proc /proc --dev /dev --tmpfs /tmp \
    --bind "$EXTRACT" "$EXTRACT" --setenv TMPDIR /tmp \
    -- "$UNPACK" "$IMAGE" "$EXTRACT" >"$LOG" 2>&1; then
  printf '%s\n' 'PASS: private extraction completed.'
else
  tail -n 45 "$LOG" >&2
  die 'unmkinitramfs failed; preserve partial extraction and log.'
fi

# initramfs-tools 0.151 can extract directly, while older versions
# may separate "early" and "main" archive parts.
if [[ -f "$EXTRACT/init" ]]; then
  MAIN="$EXTRACT"
elif [[ -f "$EXTRACT/main/init" ]]; then
  MAIN="$EXTRACT/main"
else
  die 'Cannot find /init in extracted archive, do not proceed.'
fi
[[ -f "$MAIN/etc/mdadm/mdadm.conf" ]] || die 'Embedded mdadm.conf not found.'
[[ -f "$MAIN/conf/initramfs.conf" ]] || die 'Embedded initramfs.conf not found.'
[[ -f "$MAIN/scripts/local-block/mdadm" ]] || die 'Embedded early mdadm hook not found.'
[[ -f "$MAIN/scripts/local-premount/btrfs" ]] || die 'Embedded early Btrfs hook not found.'

{
  printf 'HueyOS %s — private initramfs content inspection\n' "$KR"
  printf 'Source archive SHA-256: %s\n' "$actual"
  printf 'Source archive: %s\n' "$IMAGE"
  printf 'Private extraction destination: %s\n' "$MAIN"

  printf '\n=== MD RAID assembly configuration embedded inside initramfs ===\n'
  grep -E '^[[:space:]]*(ARRAY|HOMEHOST|DEVICE|AUTO)[[:space:]]' \
    "$MAIN/etc/mdadm/mdadm.conf" || true
  if grep -Fq "$EXPECTED_ROOT_MD" "$MAIN/etc/mdadm/mdadm.conf"; then
    printf 'PASS: embedded mdadm.conf includes the exact Optane md0 RAID10 UUID\n'
  else
    printf 'BLOCKER: embedded mdadm.conf missing Optane md0 RAID10 UUID\n'
  fi
  if grep -Fq "$STALE_MD3" "$MAIN/etc/mdadm/mdadm.conf"; then
    printf 'REVIEW: embedded mdadm.conf carries old inactive md3 entry\n'
  else
    printf 'INFO: inactive md3 UUID not found in embedded mdadm.conf\n'
  fi

  printf '\n=== Boot configuration and root subvolume (read-only host comparison) ===\n'
  printf 'Expected Btrfs root UUID: %s\n' "$EXPECTED_ROOT_FS"
  printf 'Expected rootflags: subvol=@rootfs\n'
  printf 'Running kernel root options:\n'
  tr ' ' '\n' < /proc/cmdline | grep -E '^(root|rootflags|rootfstype)=' || true
  if [[ -r /boot/grub/grub.cfg ]]; then
    if grep -Fq "$EXPECTED_ROOT_FS" /boot/grub/grub.cfg; then
      printf 'PASS: existing GRUB config references current Btrfs root UUID\n'
    else
      printf 'REVIEW: expected Btrfs root UUID not found in GRUB config\n'
    fi
    if grep -Fq 'rootflags=subvol=@rootfs' /boot/grub/grub.cfg; then
      printf 'PASS: existing GRUB config specifies @rootfs subvolume\n'
    else
      printf 'REVIEW: expected rootflags are not present in GRUB config\n'
    fi
  else
    printf 'REVIEW: existing GRUB config cannot be read by this user\n'
  fi

  printf '\n=== Embedded resume and initramfs module policy ===\n'
  if [[ -f "$MAIN/conf/conf.d/zz-resume-auto" ]]; then
    sed -n '1,30p' "$MAIN/conf/conf.d/zz-resume-auto"
  else
    printf 'No auto-resume fragment present\n'
  fi
  if [[ -f "$MAIN/conf/conf.d/resume" ]]; then
    sed -n '1,30p' "$MAIN/conf/conf.d/resume"
  fi
  grep -E '^(MODULES|COMPRESS|BUSYBOX)=' "$MAIN/conf/initramfs.conf" || true
  printf 'Configured early module names:\n'
  grep -Ev '^[[:space:]]*(#|$)' "$MAIN/conf/modules" || true

  printf '\n=== Key early scripts retained ===\n'
  for p in init usr/bin/btrfs usr/sbin/mdadm \
           scripts/local-block/mdadm scripts/local-bottom/mdadm \
           scripts/local-premount/btrfs; do
    if [[ -s "$MAIN/$p" ]]; then
      printf 'PRESENT: %s\n' "$p"
    else
      printf 'BLOCKER: missing or empty %s\n' "$p"
    fi
  done
  printf '\n=== Limitations ===\n'
  printf 'Extracted filesystem ownership is not authoritative; use prior cpio metadata audit.\n'
  printf 'No actual md0 assembly, Btrfs root mount, or NVIDIA runtime test is performed.\n'
  printf 'No boot, kernel installation, RAID/EFI/GRUB edit, or module insertion occurred.\n'
} > "$AUDIT"
cat "$AUDIT"
printf '\nAudit: %s\nExtraction log: %s\n' "$AUDIT" "$LOG"
