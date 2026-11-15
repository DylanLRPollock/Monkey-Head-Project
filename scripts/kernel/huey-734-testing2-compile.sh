#!/usr/bin/env bash
# First offline compilation of HueyOS Linux 7.3.4 testing2.
# Builds bzImage + in-tree .ko modules in a private, fresh object directory.
# No package installation, dpkg, kernel/module installation, initramfs, GRUB,
# hardware state changes, or reboot. Does NOT build proprietary NVIDIA R580.
set -Eeuo pipefail
umask 077

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || fail 'Run as a regular user, NEVER with sudo.'

ROOT="$HOME/huey-kernel-734"
SRC="$ROOT/sources/linux-7.3.4"
ARCHIVE="$ROOT/downloads/linux-7.3.4.tar.xz"
CAND="$ROOT/output/testing2/.config"
TEST1="$ROOT/output/testing1/.config"
RELEASE_FILE="$ROOT/reports/testing2/kernelrelease.txt"
OBJ="$ROOT/output/testing2-compile"
REPORT="$ROOT/reports/testing2"
BUILD_LOG="$REPORT/kernel-compile.log"
CONFIG_LOG="$REPORT/kernel-compile-config.log"
HASH_LOG="$REPORT/kernel-compile-hashes.txt"

SOURCE_SHA='b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f'
TEST1_SHA='1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762'
TEST2_SHA='db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3'
KR='7.3.4-huey-testing2'
JOBS=4

for cmd in make gcc-16 rustc bindgen sha256sum awk df find wc modinfo; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing tool $cmd"
done
for f in "$SRC/Makefile" "$ARCHIVE" "$CAND" "$TEST1" "$RELEASE_FILE"; do
  [[ -f "$f" ]] || fail "Missing preverified input $f"
done
check_hash() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$actual" == "$2" ]] || fail "SHA256 mismatch for $1; actual=$actual"
}
check_hash "$ARCHIVE" "$SOURCE_SHA"
check_hash "$TEST1" "$TEST1_SHA"
check_hash "$CAND" "$TEST2_SHA"
[[ "$(tr -d '\r\n' < "$RELEASE_FILE")" == "$KR" ]] || fail 'Candidate release record mismatch.'
[[ ! -e "$OBJ" ]] || fail "Build object directory exists: $OBJ. Preserve it and diagnose before retrying."
[[ ! -e "$BUILD_LOG" ]] || fail "Build log exists: $BUILD_LOG. Preserve it before retrying."

# Directly inspect the frozen candidate, not a mutable build default.
for line in 'CONFIG_RUST=y' 'CONFIG_BTRFS_FS=m' 'CONFIG_VMD=m' \
            'CONFIG_MD_RAID10=m' 'CONFIG_DRM_AMDGPU=m' \
            '# CONFIG_DRM_NOUVEAU is not set' \
            '# CONFIG_MODVERSIONS is not set'; do
  grep -Fqx "$line" "$CAND" || fail "Missing verified configuration requirement: $line"
done

free_kb="$(df -Pk "$ROOT/output" | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] || fail 'Unable to measure free workspace space.'
(( free_kb >= 60 * 1024 * 1024 )) || fail 'Less than 60 GiB free; do not start.'
[[ -d "$REPORT" ]] || fail "Missing report directory: $REPORT"

install -d -m 700 "$OBJ"
cp -- "$CAND" "$OBJ/.config"
check_hash "$OBJ/.config" "$TEST2_SHA"
export ARCH=x86_64

printf '%s\n' 'STEP 1 — Check copied Kconfig using gcc-16 (no source changes)'
if ! make -C "$SRC" O="$OBJ" CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing2 olddefconfig >"$CONFIG_LOG" 2>&1; then
  tail -n 35 "$CONFIG_LOG" >&2
  fail "Configuration validation failed; inspect $CONFIG_LOG"
fi
check_hash "$OBJ/.config" "$TEST2_SHA"
release="$(make -s -C "$SRC" O="$OBJ" CC=gcc-16 HOSTCC=gcc-16 \
           LOCALVERSION=-huey-testing2 kernelrelease)"
[[ "$release" == "$KR" ]] || fail "Unexpected kernelrelease: $release"

printf '%s\n' 'STEP 2 — Compile bzImage and in-tree modules, with four jobs'
printf 'Build log: %s\n' "$BUILD_LOG"
printf '%s\n' 'Do not upload the build object directory: it may contain a private signing key.'
if make -C "$SRC" O="$OBJ" -j"$JOBS" CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing2 bzImage modules >"$BUILD_LOG" 2>&1; then
  printf '%s\n' 'Build process returned success.'
else
  rc=$?
  printf 'Build process exited %s. Last 45 log lines:\n' "$rc" >&2
  tail -n 45 "$BUILD_LOG" >&2
  fail "Offline compilation failed; inspect $BUILD_LOG (keep the object tree)."
fi

printf '%s\n' 'STEP 3 — Verify compiled outputs (NO installation)'
check_hash "$OBJ/.config" "$TEST2_SHA"
[[ -s "$OBJ/arch/x86/boot/bzImage" ]] || fail 'No built bzImage found.'
[[ -s "$OBJ/vmlinux" ]] || fail 'No built vmlinux found.'
[[ -s "$OBJ/Module.symvers" ]] || fail 'Missing Module.symvers (external NVIDIA build cannot proceed).'

for name in vmd nvme raid10 btrfs amdgpu i915; do
  result="$(find "$OBJ" -type f -name "$name.ko" -print -quit)"
  [[ -n "$result" ]] || fail "Boot/display module missing: $name.ko"
  vermagic="$(modinfo -F vermagic "$result")"
  [[ "$vermagic" == "$KR "* ]] || fail "Unexpected $name.ko vermagic: $vermagic"
done
modules="$(find "$OBJ" -type f -name '*.ko' | wc -l)"
printf 'Built kernel release: %s\n' "$KR"
printf 'Built in-tree modules (.ko): %s\n' "$modules"
sha256sum "$OBJ/.config" "$OBJ/arch/x86/boot/bzImage" \
  "$OBJ/vmlinux" "$OBJ/Module.symvers" >"$HASH_LOG"
printf 'Hashes: %s\n' "$HASH_LOG"
printf '%s\n' 'SUCCESS: offline Linux bzImage and in-tree modules built.'
printf '%s\n' 'No headers .deb, NVIDIA proprietary driver, initramfs or boot installation was performed.'
