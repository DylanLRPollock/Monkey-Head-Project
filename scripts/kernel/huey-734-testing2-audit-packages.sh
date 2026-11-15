#!/usr/bin/env bash
# Offline, read-only inspection of existing HueyOS testing2 Debian packages.
# No make, no install, no dpkg -i, no initramfs/GRUB, no reboot.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" != 0 ]] || fail 'Run without sudo.'
ROOT="$HOME/huey-kernel-734"
OUTPUT="$ROOT/output"
REPORT="$ROOT/reports/testing2"
KR=7.3.4-huey-testing2
VERSION=7.3.4-huey-testing2-1
SOURCE="$ROOT/downloads/linux-7.3.4.tar.xz"
TEST1="$OUTPUT/testing1/.config"
TEST2="$OUTPUT/testing2/.config"
OBJ="$OUTPUT/testing2-compile"
MANIFEST="$REPORT/debian-package-audit-manifest.txt"
HASHES="$REPORT/debian-package-audit-hashes.txt"

for cmd in sha256sum dpkg-deb grep awk find wc mktemp cp; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing $cmd"
done
[[ -d "$REPORT" ]] || fail "Missing report directory $REPORT"
[[ ! -e "$MANIFEST" && ! -e "$HASHES" ]] || \
  fail 'Previous package-audit reports exist. Preserve them; do not overwrite.'
check_sha() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$actual" == "$2" ]] || fail "SHA256 mismatch for $1 ($actual)"
}
check_sha "$SOURCE" b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f
check_sha "$TEST1" 1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762
check_sha "$TEST2" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3
check_sha "$OBJ/.config" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3
pass 'Pinned upstream archive and kernel configurations are unchanged.'

packages=(
  linux-image-7.3.4-huey-testing2
  linux-headers-7.3.4-huey-testing2
  linux-image-7.3.4-huey-testing2-dbg
  linux-libc-dev
)
all_count="$(find "$OUTPUT" -maxdepth 1 -type f -name '*.deb' | wc -l)"
[[ "$all_count" -eq 4 ]] || fail "Expected four .deb packages; found $all_count. Inspect manually."

# Use a private staging directory for audit outputs; publish results only
# if all package metadata, file lists and hashes pass inspection.
STAGE="$(mktemp -d "$REPORT/.package-audit.XXXXXXXX")"
trap 'rm -rf -- "$STAGE"' EXIT
: > "$STAGE/manifest"
: > "$STAGE/hashes"

for name in "${packages[@]}"; do
  pkg="$OUTPUT/${name}_${VERSION}_amd64.deb"
  [[ -s "$pkg" ]] || fail "Package missing or empty: $pkg"
  actual_name="$(dpkg-deb -f "$pkg" Package)"
  actual_version="$(dpkg-deb -f "$pkg" Version)"
  arch="$(dpkg-deb -f "$pkg" Architecture)"
  [[ "$actual_name" == "$name" ]] || fail "Wrong Package field in $pkg: $actual_name"
  [[ "$actual_version" == "$VERSION" ]] || fail "Wrong Version field in $pkg: $actual_version"
  [[ "$arch" == amd64 ]] || fail "Wrong Architecture field in $pkg: $arch"

  paths="$STAGE/$name.paths"
  dpkg-deb --contents "$pkg" | awk '{print $NF}' > "$paths"
  [[ -s "$paths" ]] || fail "Package file list empty: $pkg"
  # Fail closed on private keys, PKCS#12 bundles and PEM files. We check
  # the filename field, not permissions/owner strings in dpkg-deb -c.
  if grep -Eiq '(^|/)([^/]+\.(pem|key|p12|pfx)|id_rsa|id_ed25519|signing_key\.[^/]+)$' "$paths"; then
    fail "Suspicious key/certificate path in $pkg. Do not share it."
  fi
  printf '%s\n' "Package: $actual_name" "Version: $actual_version" \
    "Architecture: $arch" "Filename: $(basename "$pkg")" \
    "Entries: $(wc -l < "$paths")" '' >> "$STAGE/manifest"
  sha256sum "$pkg" >> "$STAGE/hashes"
  pass "Validated package: $name"
done

img_paths="$STAGE/linux-image-$KR.paths"
for path in \
  "./boot/vmlinuz-$KR" \
  "./lib/modules/$KR/kernel/drivers/pci/controller/vmd.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/nvme/host/nvme.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/nvme/host/nvme-core.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/md/md-mod.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/md/raid10.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/md/raid1.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/md/raid0.ko.xz" \
  "./lib/modules/$KR/kernel/fs/btrfs/btrfs.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/gpu/drm/i915/i915.ko.xz" \
  "./lib/modules/$KR/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko.xz"; do
  grep -Fqx "$path" "$img_paths" || fail "Boot-critical file absent in image package: $path"
done
hdr_paths="$STAGE/linux-headers-$KR.paths"
grep -Fqx "./usr/src/linux-headers-$KR/Module.symvers" "$hdr_paths" || \
  fail 'Kernel headers package lacks Module.symvers.'

# The second make pass can change a compiled artifact; report such drift
# for review, without claiming that the package itself is corrupt.
if sha256sum --status -c "$REPORT/kernel-compile-hashes.txt"; then
  printf 'Original compiled object hashes: unchanged\n' >> "$STAGE/manifest"
else
  printf 'WARNING: Original compiled object hashes changed during packaging; review before driver build.\n' >> "$STAGE/manifest"
fi
cp -- "$STAGE/manifest" "$MANIFEST"
cp -- "$STAGE/hashes" "$HASHES"
pass 'All four offline Debian packages, metadata and boot-critical paths verified.'
printf 'Manifest: %s\nHashes: %s\n' "$MANIFEST" "$HASHES"
printf '%s\n' 'No .deb was installed; no NVIDIA module or initramfs was built.'
