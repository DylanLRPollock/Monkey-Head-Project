#!/usr/bin/env bash
# Build offline Debian packages from the verified testing2 bzImage/modules.
# No dpkg install, root commands, initramfs/GRUB update or reboot.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || fail 'Do not use sudo.'

ROOT="$HOME/huey-kernel-734"
SRC="$ROOT/sources/linux-7.3.4"
OBJ="$ROOT/output/testing2-compile"
CAND="$ROOT/output/testing2/.config"
TEST1="$ROOT/output/testing1/.config"
ARCHIVE="$ROOT/downloads/linux-7.3.4.tar.xz"
OUTPUT="$ROOT/output"
REPORT="$ROOT/reports/testing2"
LOG="$REPORT/debian-package.log"
MANIFEST="$REPORT/debian-package-manifest.txt"
HASHES="$REPORT/debian-package-hashes.txt"
KR='7.3.4-huey-testing2'
PKG_VERSION='7.3.4-huey-testing2-1'
SOURCE_SHA='b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f'
TEST1_SHA='1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762'
CAND_SHA='db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3'

for cmd in sha256sum awk df find dpkg-buildpackage dpkg-deb \
           dpkg-query dpkg-checkbuilddeps dh gcc-16 \
           make rustc bindgen fakeroot rsync tar; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing tool $cmd"
done
# The upstream mkdebian-generated control file requires
# debhelper-compat (= 12) and libdw-dev:native on Debian Forky.
# debhelper's virtual Provides satisfies compat 12; do not modify
# generated metadata or bypass dpkg-checkbuilddeps.
for pkg in debhelper libdw-dev; do
  installed="$(dpkg-query -W -f='\${Status}' "$pkg" 2>/dev/null || true)"
  [[ "$installed" == 'install ok installed' ]] || \
    fail "Missing Debian packaging dependency $pkg (sudo apt install debhelper libdw-dev)"
done
for file in "$SRC/Makefile" "$OBJ/.config" "$CAND" "$TEST1" \
            "$ARCHIVE" "$OBJ/vmlinux" "$OBJ/Module.symvers" \
            "$OBJ/arch/x86/boot/bzImage" "$REPORT/kernel-compile-hashes.txt"; do
  [[ -s "$file" ]] || fail "Required artifact missing: $file"
done

hash_is() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$actual" == "$2" ]] || fail "SHA-256 mismatch for $1 ($actual)"
}
hash_is "$ARCHIVE" "$SOURCE_SHA"
hash_is "$TEST1" "$TEST1_SHA"
hash_is "$CAND" "$CAND_SHA"
hash_is "$OBJ/.config" "$CAND_SHA"
sha256sum --status -c "$REPORT/kernel-compile-hashes.txt" || \
  fail 'Compiled artifacts differ from their original recorded hashes.'
[[ -f "$OBJ/certs/signing_key.pem" ]] || \
  fail 'Private signing key unexpectedly absent from isolated build; stop.'

[[ ! -e "$LOG" && ! -e "$HASHES" && ! -e "$MANIFEST" ]] || \
  fail 'A previous packaging report exists; preserve it before retrying.'
if find "$OUTPUT" -maxdepth 1 -type f \
    \( -name '*.deb' -o -name '*.changes' -o -name '*.buildinfo' \) | grep -q .; then
  fail 'Existing package artifacts in output directory; do not overwrite.'
fi

free_kb="$(df -Pk "$OUTPUT" | awk 'NR==2 {print $4}')"
[[ "$free_kb" =~ ^[0-9]+$ ]] || fail 'Could not determine free space.'
(( free_kb >= 50 * 1024 * 1024 )) || \
  fail 'Less than 50 GiB free: resolve workspace capacity first.'
export ARCH=x86_64
release="$(make -s -C "$SRC" O="$OBJ" CC=gcc-16 HOSTCC=gcc-16 \
  LOCALVERSION=-huey-testing2 kernelrelease)"
[[ "$release" == "$KR" ]] || fail "Unexpected kernelrelease $release"
current_kernel="$(uname -r)"

printf 'STEP 1 — Package offline: %s\n' "$KR"
if make -C "$SRC" O="$OBJ" -j4 CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing2 KDEB_PKGVERSION="$PKG_VERSION" \
      bindeb-pkg >"$LOG" 2>&1; then
  printf '%s\n' 'Debian packaging command completed.'
else
  rc=$?
  printf 'Packaging exited %s; last 40 log lines:\n' "$rc" >&2
  tail -n 40 "$LOG" >&2
  fail "Package generation failed. Preserve the worktree and inspect $LOG"
fi

printf '%s\n' 'STEP 2 — Verify package names and screen for private-key paths'
: >"$MANIFEST"
: >"$HASHES"
image=0
headers=0
count=0
for pkg in "$OUTPUT"/*.deb; do
  [[ -f "$pkg" ]] || continue
  count=$((count+1))
  package_name="$(dpkg-deb -f "$pkg" Package)"
  case "$package_name" in
    "linux-image-$KR") image=$((image+1)) ;;
    "linux-headers-$KR") headers=$((headers+1)) ;;
    linux-libc-dev) : ;;
    *) fail "Unexpected binary package $package_name at $pkg" ;;
  esac
  printf '%s\n' "--- $pkg ---" >>"$MANIFEST"
  dpkg-deb -f "$pkg" Package Version Architecture >>"$MANIFEST"
  contents="$REPORT/package-contents-$(basename "$pkg").txt"
  dpkg-deb --contents "$pkg" >"$contents"
  if grep -Ei '(^|/)(signing_key\.pem|[^/]+\.key|private[^/]*\.pem|id_rsa|[^/]+\.p12|[^/]+\.pfx)([[:space:]]|$)' \
      "$contents" >/dev/null; then
    fail "Possible private key in $pkg. Do not share it."
  fi
  sha256sum "$pkg" >>"$HASHES"
done
[[ "$count" -gt 0 && "$image" -eq 1 && "$headers" -eq 1 ]] || \
  fail "Missing or duplicate expected image/headers packages (image=$image, headers=$headers)."
hash_is "$OBJ/.config" "$CAND_SHA"
if ! sha256sum --status -c "$REPORT/kernel-compile-hashes.txt"; then
  printf '%s\n' 'WARN: Compiled artifact hashes changed during packaging; re-review required.'
fi
[[ "$(uname -r)" == "$current_kernel" ]] || \
  fail 'Running kernel changed unexpectedly.'
printf 'PASS: offline Debian image/headers packages identified (%s total).\n' "$count"
printf 'Manifest: %s\nHashes: %s\n' "$MANIFEST" "$HASHES"
printf '%s\n' 'No package installed. Do not upload .deb files before independent review.'
