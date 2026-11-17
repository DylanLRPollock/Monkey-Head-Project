#!/usr/bin/env bash
# Build second PRIVATE testing2 initrd using existing staged modules and exact policy overlay.
# Prune stale md3 and disable resume only inside this namespace. No host changes.
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
ORIGCONF="$STAGE/config"
RETRY="$STAGE/work/fakeroot-policy2"
CONF="$RETRY/config"
PRIVATEMD="$RETRY/mdadm.conf"
ORIGMD="$ROOT/output/testing2-initramfs-content-audit/etc/mdadm/mdadm.conf"
if [[ ! -f "$ORIGMD" ]]; then ORIGMD="$ROOT/output/testing2-initramfs-content-audit/main/etc/mdadm/mdadm.conf"; fi
EXTRACT="$RETRY/unpacked"
VERBOSE="$REPORT/testing2-policy2-verbose.txt"
UNPACKLOG="$REPORT/testing2-policy2-unpack.log"
ARCHIVE="$RETRY/initrd.img-$KR"
PROBELOG="$REPORT/testing2-policy2-probe.log"
LOG="$REPORT/testing2-policy2-build.log"
LIST="$REPORT/testing2-policy2-files.txt"
AUDIT="$REPORT/testing2-policy2-audit.txt"
HASHES="$REPORT/testing2-policy2-hashes.txt"
PRIOR="$REPORT/testing2-fakeroot-initramfs-audit.txt"
OLDIMG="$STAGE/work/fakeroot-retry1/initrd.img-$KR"
MD0=f3c8b907:d3b5a85f:a2578548:157bf1d2
MD1=a3068941:490dcc7f:ce9dedcc:6ef270e0
MD2=646adf0e:63c18bd3:053728a3:66c836b5
MD3=38a8dd4b:f15c5eca:fafe213a:2962ac03
for cmd in bwrap fakeroot sha256sum awk grep lsinitramfs install cp; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Required executable missing: $cmd"
done
[[ -x /usr/sbin/mkinitramfs ]] || fail 'Missing /usr/sbin/mkinitramfs.'
[[ -s "$PRIOR" && -s "$OLDIMG" && -s "$ORIGMD" ]] || fail 'Original successful artifact/config extraction missing.'
[[ "$(sha256sum "$OLDIMG" | awk '{print $1}')" == ddcc9e6c238a3c744adca38903c5d4ffcf8c4393ee1517576860a85812cb5bdd ]] || fail 'Previous validated initramfs changed.'
[[ -d "$ORIGCONF" && -s "$ORIGCONF/modules" && -s "$ORIGCONF/initramfs.conf" ]] || \
  fail 'Missing original private initramfs configuration.'
[[ -d "$MODTREE/kernel" && -s "$MODTREE/modules.dep" ]] || \
  fail 'Missing original private depmod output; refusing to rebuild or modify it.'
[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]] || \
  fail 'Target testing2 kernel appears on the host; aborting.'
for f in "$RETRY" "$PROBELOG" "$LOG" "$LIST" "$VERBOSE" "$UNPACKLOG" "$AUDIT" "$HASHES"; do
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
pass 'Existing tested modules and NVIDIA identity hashes verified.'

# The source file was extracted from the pinned previous archive.
for id in "$MD0" "$MD1" "$MD2" "$MD3"; do
  grep -Fq "$id" "$ORIGMD" || fail "Source mdadm.conf lacks expected UUID: $id"
done
printf '%s\n' 'STEP 1 — Create a second private configuration (never edit live /etc).'
install -d -m 0700 "$RETRY/tmp" "$CONF"
cp -a "$ORIGCONF/." "$CONF/"
install -d -m 0700 "$CONF/conf.d"
printf 'RESUME=none\n' >"$CONF/conf.d/resume"
awk -v md3="$MD3" '
  $1=="ARRAY" && $2=="/dev/md/3" && index($0, md3) {removed++; next}
  {print}
  END {if (removed != 1) exit 19}
' "$ORIGMD" >"$PRIVATEMD" || fail 'Expected exactly one obsolete md3 ARRAY record.'
chmod 0644 "$PRIVATEMD"
for id in "$MD0" "$MD1" "$MD2"; do
  grep -Fq "$id" "$PRIVATEMD" || fail "Lost an active mdadm ARRAY UUID: $id"
done
if grep -Fq "$MD3" "$PRIVATEMD"; then fail 'Obsolete md3 entry remains in staged config.'; fi
[[ "$(grep -Ec '^[[:space:]]*ARRAY[[:space:]]' "$PRIVATEMD")" == 3 ]] || fail 'Expected precisely 3 active ARRAY entries.'
pass 'Private mdadm.conf has md0/md1/md2 only; private resume policy is none.'

# The previously successful rootless Bubblewrap mount policy is retained.
# Root binds are read-only. Only the new retry directory can be written.
sandbox() {
  bwrap --unshare-user --uid 0 --gid 0 --unshare-pid --unshare-net \
    --die-with-parent --ro-bind / / --proc /proc --dev /dev \
    --tmpfs /tmp --tmpfs /lib/modules --dir "/lib/modules/$KR" \
    --ro-bind "$MODTREE" "/lib/modules/$KR" \
    --bind "$RETRY" "$RETRY" \
    --ro-bind "$PRIVATEMD" /etc/mdadm/mdadm.conf \
    --setenv PATH /usr/sbin:/usr/bin:/sbin:/bin \
    --setenv TMPDIR "$RETRY/tmp" \
    --setenv SOURCE_DATE_EPOCH 0 \
    --setenv FAKEROOTDONTTRYCHOWN 1 \
    -- "$@"
}
printf '%s\n' 'STEP 2 — Verify namespace policy and fakeroot copying.'
if sandbox fakeroot -- /bin/sh -c \
  'test -s "/lib/modules/$1/modules.dep" && \
   test ! -e "/lib/modules/$(uname -r)" && \
   cp --reflink=auto --preserve=xattr -fLp /usr/bin/btrfs "$2/probe-btrfs" && \
   test -s "$2/probe-btrfs" && \
   grep -Fq "$3" /etc/mdadm/mdadm.conf && \
   ! grep -Fq "$4" /etc/mdadm/mdadm.conf' sh "$KR" "$RETRY" "$MD0" "$MD3" \
  >"$PROBELOG" 2>&1; then
  pass 'fakeroot ownership-copy probe passed.'
else
  tail -n 35 "$PROBELOG" >&2
  fail 'fakeroot copy probe failed. Do not regenerate initramfs.'
fi

printf '%s\n' 'STEP 3 — Generate second isolated initrd under fakeroot.'
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
printf '%s\n' 'STEP 4 — Verify early boot files and cpio metadata.'
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
lsinitramfs -l "$ARCHIVE" >"$VERBOSE" || fail 'Cannot inspect cpio ownership metadata.'
awk '$NF=="init" && $1=="-rwxr-xr-x" && $3=="root" && $4=="root" {found=1} END {exit !found}' \
  "$VERBOSE" || fail 'New image has unexpected /init ownership/mode.'

printf '%s\n' 'STEP 5 — Inspect actual embedded mdadm and resume policy in private extraction.'
UNPACK="$(command -v unmkinitramfs || true)"
[[ -n "$UNPACK" ]] || UNPACK=/usr/bin/unmkinitramfs
[[ -x "$UNPACK" ]] || fail 'Missing unmkinitramfs.'
install -d -m 0700 "$EXTRACT"
if bwrap --unshare-net --die-with-parent \
  --ro-bind / / --proc /proc --dev /dev --tmpfs /tmp \
  --bind "$RETRY" "$RETRY" --setenv TMPDIR /tmp \
  -- "$UNPACK" "$ARCHIVE" "$EXTRACT" >"$UNPACKLOG" 2>&1; then
  pass 'Extracted new image only to a private directory.'
else
  tail -n 40 "$UNPACKLOG" >&2
  fail 'Cannot extract new image for policy validation.'
fi
if [[ -f "$EXTRACT/init" ]]; then
  MAIN="$EXTRACT"
elif [[ -f "$EXTRACT/main/init" ]]; then
  MAIN="$EXTRACT/main"
else
  fail 'No /init in extracted new image.'
fi
EMD="$MAIN/etc/mdadm/mdadm.conf"
RESUME="$MAIN/conf/conf.d/resume"
[[ -s "$EMD" && -f "$RESUME" ]] || fail 'New image is missing embedded mdadm.conf or resume policy.'
for id in "$MD0" "$MD1" "$MD2"; do
  grep -Fq "$id" "$EMD" || fail "New image is missing active mdadm ARRAY UUID: $id"
done
if grep -Fq "$MD3" "$EMD"; then fail 'New image still contains stale md3 ARRAY UUID.'; fi
[[ "$(grep -Ec '^[[:space:]]*ARRAY[[:space:]]' "$EMD")" == 3 ]] || fail 'Unexpected embedded ARRAY count.'
grep -Exq 'RESUME=none' "$RESUME" || fail 'RESUME=none not embedded.'
if grep -REq '^RESUME=(/dev/|UUID=|auto)' "$MAIN/conf"; then
  fail 'A conflicting resume configuration remains embedded.'
fi

sha256sum "$ARCHIVE" >"$HASHES"
{
  printf 'Target release: %s\n' "$KR"
  printf 'Artifact: %s\n' "$ARCHIVE"
  cat "$HASHES"
  printf 'PASS: requested early modules, RAID metadata/hooks and versioned modules present.\n'
  printf 'PASS: /init ownership=root:root mode=0755.\n'\n  printf 'PASS: embedded md0/md1/md2, md3 absent, RESUME=none.\n'
  printf 'NOTE: archive listing does not prove bootability or NVIDIA runtime behavior.\n'
  printf 'No host driver/kernel installation, EFI/GRUB/RAID changes or reboot occurred.\n'
} >"$AUDIT"
cat "$AUDIT"
printf 'Audit: %s\nBuild log: %s\n' "$AUDIT" "$LOG"
