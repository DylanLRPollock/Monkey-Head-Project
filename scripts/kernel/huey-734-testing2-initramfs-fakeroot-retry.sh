#!/usr/bin/env bash
# Retry ONLY failed initramfs generation using original private staging.
# fakeroot emulates chown() in a restricted user namespace; no host install.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" != 0 ]] || fail "Run without sudo."
KR='7.3.4-huey-testing2'
ROOT="$HOME/huey-kernel-734"
REPORT="$ROOT/reports/testing2"
STAGE="$ROOT/output/testing2-initramfs-isolated"
MODTREE="$STAGE/unpacked-image/lib/modules/$KR"
CONF="$STAGE/config"
RETRY="$STAGE/work/fakeroot-retry1"
ARCHIVE="$RETRY/initrd.img-$KR"
PROBELOG="$REPORT/testing2-fakeroot-probe.log"
LOG="$REPORT/testing2-fakeroot-initramfs-build.log"
LIST="$REPORT/testing2-fakeroot-initramfs-files.txt"
AUDIT="$REPORT/testing2-fakeroot-initramfs-audit.txt"
HASHES="$REPORT/testing2-fakeroot-initramfs-hashes.txt"
PRIOR="$REPORT/testing2-isolated-initramfs-build.log"
for cmd in bwrap fakeroot sha256sum awk grep lsinitramfs install cp; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Required executable missing: $cmd"
done
[[ -x /usr/sbin/mkinitramfs ]] || fail 'Missing /usr/sbin/mkinitramfs.'
[[ -s "$PRIOR" ]] || fail 'Original failure log absent; do not bypass first attempt.'
[[ -d "$CONF" && -s "$CONF/modules" && -s "$CONF/initramfs.conf" ]] || \
  fail 'Missing original private initramfs configuration.'
[[ -d "$MODTREE/kernel" && -s "$MODTREE/modules.dep" ]] || \
  fail 'Missing original private depmod output; refusing to rebuild or modify it.'
[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]] || \
  fail 'Target testing2 kernel appears on the host; aborting.'
for f in "$RETRY" "$PROBELOG" "$LOG" "$LIST" "$AUDIT" "$HASHES"; do
  [[ ! -e "$f" ]] || fail "Existing retry artifact, refusing overwrite: $f"
done

hash_is() {
  local got
  got="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$got" == "$2" ]] || fail "Unexpected SHA-256: $1"
}
hash_is "$ROOT/output/linux-image-7.3.4-huey-testing2_7.3.4-huey-testing2-1_amd64.deb" 25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0
hash_is "$ROOT/output/testing2-compile/.config" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3
hash_is "$MODTREE/updates/nvidia.ko" 31113cef510d54e51b593c8a84780342bf8bfadb346dd09d93f2baa893c24c60
hash_is "$MODTREE/updates/nvidia-uvm.ko" 49e7714072c73035db08736f2848bf180938614a3c5aee3dd56740bf4e3c7995
hash_is "$MODTREE/updates/nvidia-modeset.ko" 076c6b14554a929ced396323574ef6b23edfc79142de0128f5f439ca359ae72a
hash_is "$MODTREE/updates/nvidia-drm.ko" bcd7b35e78231d36bee6a95c9a40adfd0ca8ca0bc0db52b9f4b02da18fba00e7
pass 'Original module staging and NVIDIA module identities verified.'

# The previously successful rootless Bubblewrap mount policy is retained.
# Root binds are read-only. Only the new retry directory can be written.
install -d -m 0700 "$RETRY/tmp"
sandbox() {
  bwrap --unshare-user --uid 0 --gid 0 --unshare-pid --unshare-net \
    --die-with-parent --ro-bind / / --proc /proc --dev /dev \
    --tmpfs /tmp --tmpfs /lib/modules --dir "/lib/modules/$KR" \
    --ro-bind "$MODTREE" "/lib/modules/$KR" \
    --bind "$RETRY" "$RETRY" \
    --setenv PATH /usr/sbin:/usr/bin:/sbin:/bin \
    --setenv TMPDIR "$RETRY/tmp" \
    --setenv SOURCE_DATE_EPOCH 0 \
    --setenv FAKEROOTDONTTRYCHOWN 1 \
    -- "$@"
}
printf '%s\n' 'STEP 1 — Probe fakeroot ownership preservation in a private namespace.'
if sandbox fakeroot -- /bin/sh -c \
  'test -s "/lib/modules/$1/modules.dep" && \
   test ! -e "/lib/modules/$(uname -r)" && \
   cp --reflink=auto --preserve=xattr -fLp /usr/bin/btrfs "$2/probe-btrfs" && \
   test -s "$2/probe-btrfs"' sh "$KR" "$RETRY" \
  >"$PROBELOG" 2>&1; then
  pass 'fakeroot ownership-copy probe passed.'
else
  tail -n 35 "$PROBELOG" >&2
  fail 'fakeroot copy probe failed. Do not regenerate initramfs.'
fi

printf '%s\n' 'STEP 2 — Retry only mkinitramfs under FAKEROOTDONTTRYCHOWN=1.'
if sandbox fakeroot -- /usr/sbin/mkinitramfs \
  -d "$CONF" -o "$ARCHIVE" "$KR" >"$LOG" 2>&1; then
  pass 'Isolated fakeroot mkinitramfs completed.'
else
  code=$?
  printf 'mkinitramfs exit code: %s\n' "$code" >&2
  tail -n 70 "$LOG" >&2
  fail 'Initramfs retry failed; existing evidence and worktree preserved.'
fi
[[ -s "$ARCHIVE" ]] || fail 'Archive is absent or empty.'
lsinitramfs "$ARCHIVE" >"$LIST" || fail 'Cannot read generated archive file list.'
printf '%s\n' 'STEP 3 — Validate critical modules and MD RAID assembly hooks.'
for mod in vmd nvme nvme-core md-mod raid10 raid1 raid0 btrfs amdgpu \
           nvidia nvidia-uvm; do
  grep -Eq "(^|/)$mod[.]ko([.](xz|gz|zst))?$" "$LIST" || \
    fail "Missing early module: $mod"
done
for entry in usr/sbin/mdadm etc/mdadm/mdadm.conf scripts/local-block/mdadm; do
  grep -Eq "(^|/)$entry$" "$LIST" || \
    fail "Missing mdadm executable/config/assembly script: $entry"
done
grep -Eq "(^|/)(usr/)?lib/modules/$KR/" "$LIST" || \
  fail "Archive lacks expected kernel release $KR."
if grep -Eq '(^|/)nouveau[.]ko([.](xz|gz|zst))?$' "$LIST"; then
  fail 'Archive unexpectedly includes Nouveau.'
fi
sha256sum "$ARCHIVE" >"$HASHES"
{
  printf 'Target release: %s\n' "$KR"
  printf 'Artifact: %s\n' "$ARCHIVE"
  cat "$HASHES"
  printf 'PASS: requested early modules, RAID metadata/hooks and versioned modules present.\n'
  printf 'NOTE: fakeroot uses simulated ownership; inspect actual cpio metadata before boot.\n'
  printf 'NOTE: archive listing does not prove bootability or NVIDIA runtime behavior.\n'
  printf 'No host driver/kernel installation, EFI/GRUB/RAID changes or reboot occurred.\n'
} >"$AUDIT"
cat "$AUDIT"
printf 'Audit: %s\nBuild log: %s\n' "$AUDIT" "$LOG"
