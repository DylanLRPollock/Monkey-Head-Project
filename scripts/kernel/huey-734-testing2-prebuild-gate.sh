#!/usr/bin/env bash
# Read-only HueyOS 7.3.4 testing2 build readiness audit. No compile/install/reboot.
set -Eeuo pipefail
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
warn() { printf 'WARN: %s\n' "$*" >&2; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" != 0 ]] || fail 'Run as your normal user, not sudo.'
ROOT="$HOME/huey-kernel-734"
OUT="$ROOT/output/testing2"
CONFIG="$OUT/.config"
SOURCE="$ROOT/downloads/linux-7.3.4.tar.xz"
TEST1="$ROOT/output/testing1/.config"
RELEASE="$ROOT/reports/testing2/kernelrelease.txt"

for p in "$CONFIG" "$SOURCE" "$TEST1" "$RELEASE"; do
  [[ -f "$p" ]] || fail "Missing expected file: $p"
done

check_hash() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$actual" == "$2" ]] || fail "Unexpected SHA-256 for $1 ($actual)"
}
check_hash "$SOURCE" b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f
check_hash "$TEST1" 1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762
check_hash "$CONFIG" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3
[[ "$(tr -d '\n\r' < "$RELEASE")" == "7.3.4-huey-testing2" ]] || fail 'Wrong kernel release'
pass 'Signed-source digest and immutable testing1/testing2 configuration digests match.'

require() { grep -Fqx "$1" "$CONFIG" || fail "Required Kconfig line missing: $1"; }
for symbol in VMD NVME_CORE BLK_DEV_NVME BLK_DEV_MD MD_RAID10 \
              MD_RAID0 MD_RAID1 BTRFS_FS SATA_AHCI DRM_I915 DRM_AMDGPU; do
  require "CONFIG_$symbol=m"
done
for symbol in MODULES RUST RUST_IS_AVAILABLE DEBUG_INFO_BTF EFI EFI_STUB MODULE_SIG; do
  require "CONFIG_$symbol=y"
done
for symbol in LOCALVERSION_AUTO MODVERSIONS DRM_NOUVEAU MODULE_SIG_FORCE; do
  require "# CONFIG_$symbol is not set"
done
require 'CONFIG_LOCALVERSION=""'
pass 'Intel VMD/Optane root, SATA, i915, AMDGPU, V100 and Rust options preserved.'

require 'CONFIG_MODULE_SIG_ALL=y'
require 'CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"'
warn 'Automatic module signing configured. Keep generated private key outside any shared artifact.'
require '# CONFIG_ANDROID_BINDER_IPC is not set'
warn 'Android Binder is absent for upstream testing2 (Waydroid not qualified).'
warn 'Actual initramfs mdadm hooks and V100 R580 module compatibility are not yet verified.'

missing=()
for cmd in gcc-16 make flex bison bc openssl pahole cpio rsync fakeroot \
           dpkg-deb dpkg-buildpackage dpkg-checkbuilddeps dh \
           rustc bindgen pkg-config; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
# Debian places modinfo in /usr/sbin; allow normal-user shells to omit it
# from PATH while still requiring the kmod binary to be installed.
if ! command -v modinfo >/dev/null 2>&1 &&
   [[ ! -x /usr/sbin/modinfo && ! -x /sbin/modinfo ]]; then
  missing+=("kmod (provides modinfo)")
fi
for pkg in libssl-dev libelf-dev libdw-dev debhelper; do
  status="$(dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null || true)"
  [[ "$status" == 'install ok installed' ]] || missing+=("$pkg")
done
if ((${#missing[@]})); then
  printf 'Missing build prerequisites: %s\n' "${missing[*]}"
  fail 'Required build prerequisites are missing. Review and install them before approving compilation.'
else
  pass 'Common kernel/headers/packaging prerequisites found.'
fi

free_kb="$(df -Pk "$OUT" | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] || fail 'Unable to measure workspace free space.'
printf 'Workspace free: %s GiB\n' "$((free_kb / 1024 / 1024))"
(( free_kb >= 30 * 1024 * 1024 )) || warn 'Less than 30 GiB free: do not start a build.'
mode="$(stat -c '%a' "$OUT")"
if (( (8#$mode & 0077) != 0 )); then
  warn 'Output directory is not private; do not create a signing key here.'
else
  pass 'Build output permissions restrict access to the current user.'
fi
printf '%s\n' 'END: Configuration and package-readiness checks only. No compile/install/reboot.'
