#!/usr/bin/env bash
# Read-only verification of the already-built, isolated testing2 initramfs.
# No extraction, image regeneration, sudo, module insertion or boot changes.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" -ne 0 ]] || fail "Run as normal user, without sudo."

KR='7.3.4-huey-testing2'
BASE="$HOME/huey-kernel-734"
DIR="$BASE/reports/testing2"
ARCHIVE="$BASE/output/testing2-initramfs-isolated/work/fakeroot-retry1/initrd.img-$KR"
SUMMARY="$DIR/testing2-fakeroot-archive-metadata-audit.txt"
VERBOSE="$DIR/testing2-fakeroot-archive-verbose-list.txt"
BUILD_LOG="$DIR/testing2-fakeroot-initramfs-build.log"
EXPECTED='ddcc9e6c238a3c744adca38903c5d4ffcf8c4393ee1517576860a85812cb5bdd'

for tool in lsinitramfs sha256sum awk grep wc stat; do
  command -v "$tool" >/dev/null 2>&1 || fail "Required tool missing: $tool"
done
[[ -s "$ARCHIVE" && -r "$BUILD_LOG" ]] || fail "Missing initramfs or fakeroot build log."
[[ ! -e "$SUMMARY" && ! -e "$VERBOSE" ]] || fail "Existing audit output; preserve it."
GOT="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[[ "$GOT" == "$EXPECTED" ]] || fail "Initramfs SHA-256 mismatch ($GOT)."
printf 'PASS: pinned testing2 initramfs SHA-256 verified.\n'

# Use Debian's native parser for the concatenated early microcode + main cpio.
# -l reports cpio ownership/mode metadata without unpacking files.
if ! lsinitramfs -l "$ARCHIVE" > "$VERBOSE"; then
  fail 'lsinitramfs verbose metadata listing failed.'
fi
{
  printf 'HueyOS %s — read-only initramfs ownership/mode audit\n' "$KR"
  printf 'SHA-256: %s\n' "$GOT"
  printf 'Archive: %s\n' "$ARCHIVE"
  stat -c 'Size: %s bytes' "$ARCHIVE"
  printf 'Verbose-list entries: %s\n' "$(wc -l < "$VERBOSE")"
  printf '\n=== Metadata for boot-critical entries ===\n'
  for p in init \
           etc/mdadm/mdadm.conf scripts/local-block/mdadm \
           scripts/local-bottom/mdadm scripts/local-premount/btrfs \
           usr/bin/btrfs usr/sbin/mdadm \
           "usr/lib/modules/$KR/updates/nvidia.ko" \
           "usr/lib/modules/$KR/updates/nvidia-uvm.ko"; do
    # Debian's long format ends in the filename.
    if ! awk -v p="$p" '$NF==p || $NF=="./"p {found=1; print}' "$VERBOSE" | \
      grep -q .; then
      printf 'MISSING metadata row for: %s\n' "$p"
    else
      awk -v p="$p" '$NF==p || $NF=="./"p {print}' "$VERBOSE"
    fi
  done
  printf '\n=== Fakeroot and boot-hook diagnostics (original build log) ===\n'
  grep -E 'libfakeroot|root file system|resume from|mdadm:|plymouth:' "$BUILD_LOG" || true
  printf '\n=== Qualification policy ===\n'
  printf 'This report records cpio metadata, not bootability or initramfs correctness.\n'
  printf 'Confirm root ownership and executable permissions of /init and mdadm hooks.\n'
  printf 'Inspect actual embedded mdadm.conf UUIDs and resume policy separately.\n'
  printf 'Do not install, load modules or reboot on this result alone.\n'
} > "$SUMMARY"
cat "$SUMMARY"
printf '\nFull verbose listing: %s\nSummary: %s\n' "$VERBOSE" "$SUMMARY"
