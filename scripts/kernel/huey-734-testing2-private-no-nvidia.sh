#!/usr/bin/env bash
# Build only a THIRD PRIVATE testing2 initrd for storage/AMDGPU boot testing.
# Keep the original policy2 and host kernel, drivers, EFI, GRUB and RAID unchanged.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" != 0 ]] || fail "Run as normal user WITHOUT sudo."

KR=7.3.4-huey-testing2
ROOT="$HOME/huey-kernel-734"
STAGE="$ROOT/output/testing2-initramfs-isolated"
REPORT="$ROOT/reports/testing2"
MODTREE="$STAGE/unpacked-image/lib/modules/$KR"
POLICY2="$STAGE/work/fakeroot-policy2"
WORK="$STAGE/work/no-nvidia-test1"
CONF="$WORK/config"
ARCHIVE="$WORK/initrd.img-$KR"
EXTRACT="$WORK/unpacked"
LOG="$REPORT/testing2-no-nvidia-build.log"
UNPACKLOG="$REPORT/testing2-no-nvidia-unpack.log"
PROBELOG="$REPORT/testing2-no-nvidia-probe.log"
LIST="$REPORT/testing2-no-nvidia-list.txt"
VERBOSE="$REPORT/testing2-no-nvidia-verbose.txt"
AUDIT="$REPORT/testing2-no-nvidia-audit.txt"
HASHES="$REPORT/testing2-no-nvidia-sha256.txt"
POLICY2_SHA=8bce591f673c74d3eeadfc53f8563aa7d20c6f22af2ac7adff4744bcfc6a05b7
MD0=f3c8b907:d3b5a85f:a2578548:157bf1d2
MD1=a3068941:490dcc7f:ce9dedcc:6ef270e0
MD2=646adf0e:63c18bd3:053728a3:66c836b5
MD3=38a8dd4b:f15c5eca:fafe213a:2962ac03

for cmd in bwrap fakeroot sha256sum awk grep lsinitramfs install cp df; do
  command -v "$cmd" >/dev/null || fail "Required executable missing: $cmd"
done
UNPACK="$(command -v unmkinitramfs || true)"
[[ -n "$UNPACK" ]] || UNPACK=/usr/bin/unmkinitramfs
[[ -x "$UNPACK" && -x /usr/sbin/mkinitramfs ]] ||
  fail "Debian initramfs-tools extraction or build utility missing."
[[ -d "$REPORT" && -s "$POLICY2/initrd.img-$KR" ]] ||
  fail "Policy2 must be built and audited before attempting this test."
[[ -s "$POLICY2/mdadm.conf" && -s "$POLICY2/config/modules" &&
   -s "$POLICY2/config/initramfs.conf" ]] ||
  fail "Missing source policy2 configuration."
[[ -s "$MODTREE/modules.dep" && -d "$MODTREE/kernel" ]] ||
  fail "Original private module staging is missing."
[[ ! -e "/boot/vmlinuz-$KR" && ! -e "/lib/modules/$KR" ]] ||
  fail "Testing2 appears installed on the host; stop for review."
for p in "$WORK" "$LOG" "$UNPACKLOG" "$PROBELOG" "$LIST" "$VERBOSE" "$AUDIT" "$HASHES"; do
  [[ ! -e "$p" ]] || fail "Existing artifact would be overwritten: $p"
done
actual="$(sha256sum "$POLICY2/initrd.img-$KR" | awk '{print $1}')"
[[ "$actual" == "$POLICY2_SHA" ]] || fail "Verified policy2 SHA-256 mismatch: $actual"
# Preserve provenance of the exact audited Linux image and Kconfig.
[[ "$(sha256sum "$ROOT/output/linux-image-7.3.4-huey-testing2_7.3.4-huey-testing2-1_amd64.deb" | awk '{print $1}')" == 25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0 ]] ||
  fail "Original testing2 kernel package checksum mismatch."
[[ "$(sha256sum "$ROOT/output/testing2-compile/.config" | awk '{print $1}')" == db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3 ]] ||
  fail "Original testing2 kernel configuration checksum mismatch."
space="$(df -Pk "$ROOT/output" | awk 'NR==2 {print $4}')"
[[ "$space" =~ ^[0-9]+$ ]] && (( space >= 3 * 1024 * 1024 )) ||
  fail "At least 3 GiB free required in output filesystem."
for uuid in "$MD0" "$MD1" "$MD2"; do
  grep -Fq "$uuid" "$POLICY2/mdadm.conf" ||
    fail "Policy2 mdadm.conf missing active array UUID $uuid"
done
if grep -Fq "$MD3" "$POLICY2/mdadm.conf"; then
  fail "Policy2 mdadm.conf unexpectedly includes inactive md3."
fi
[[ "$(grep -Ec '^[[:space:]]*ARRAY[[:space:]]' "$POLICY2/mdadm.conf")" == 3 ]] ||
  fail "Expected exactly three active MD arrays in policy2."
grep -Exq 'RESUME=none' "$POLICY2/config/conf.d/resume" ||
  fail "Policy2 does not disable resume."
pass "Verified exact policy2 source image, RAID UUIDs and staged modules."

printf '%s\n' "STEP 1 — Create private no-NVIDIA initramfs configuration."
install -d -m 0700 "$WORK/tmp" "$CONF"
cp -a "$POLICY2/config/." "$CONF/"
# Do not modify original module staging or private policy2 files.
# Use precisely the known boot-essential storage/display modules.
printf '%s\n' \
  vmd nvme nvme_core md_mod raid10 raid1 raid0 btrfs amdgpu \
  >"$CONF/modules"
printf 'RESUME=none\n' >"$CONF/conf.d/resume"
if grep -Ei '^[[:space:]]*nvidia([_-]|[[:space:]]|$)' "$CONF/modules"; then
  fail "NVIDIA remains in private module preload configuration."
fi

# The kernel module tree remains READ-ONLY in the namespace.
# Hooks may still add NVIDIA: inspect the FINISHED image and fail closed.
sandbox() {
  bwrap --unshare-user --uid 0 --gid 0 --unshare-pid --unshare-net \
    --die-with-parent --ro-bind / / --proc /proc --dev /dev \
    --tmpfs /tmp --tmpfs /lib/modules --dir "/lib/modules/$KR" \
    --ro-bind "$MODTREE" "/lib/modules/$KR" \
    --bind "$WORK" "$WORK" \
    --ro-bind "$POLICY2/mdadm.conf" /etc/mdadm/mdadm.conf \
    --setenv PATH /usr/sbin:/usr/bin:/sbin:/bin \
    --setenv TMPDIR "$WORK/tmp" \
    --setenv SOURCE_DATE_EPOCH 0 \
    --setenv FAKEROOTDONTTRYCHOWN 1 \
    -- "$@"
}
printf '%s\n' "STEP 2 — Verify restricted namespace and fakeroot copy behavior."
if sandbox fakeroot -- /bin/sh -c '
  test -s "/lib/modules/$1/modules.dep" &&
  test ! -e "/lib/modules/$(uname -r)" &&
  grep -Fq "$3" /etc/mdadm/mdadm.conf &&
  cp --reflink=auto --preserve=xattr -fLp /usr/bin/btrfs "$2/probe-btrfs" &&
  test -s "$2/probe-btrfs"
' sh "$KR" "$WORK" "$MD0" >"$PROBELOG" 2>&1; then
  pass "Rootless fakeroot and read-only module bindings verified."
else
  tail -n 35 "$PROBELOG" >&2
  fail "Namespace probe failed; preserve output."
fi

printf '%s\n' "STEP 3 — Build a third private archive, without installing."
if sandbox fakeroot -- /usr/sbin/mkinitramfs \
   -d "$CONF" -o "$ARCHIVE" "$KR" >"$LOG" 2>&1; then
  pass "Private mkinitramfs completed."
else
  tail -n 60 "$LOG" >&2
  fail "Private initramfs build failed; keep logs."
fi
[[ -s "$ARCHIVE" ]] || fail "New image missing or empty."
lsinitramfs "$ARCHIVE" >"$LIST" || fail "Cannot list initramfs."
lsinitramfs -l "$ARCHIVE" >"$VERBOSE" || fail "Cannot inspect initramfs metadata."

printf '%s\n' "STEP 4 — Require storage/display modules and reject any NVIDIA modules."
for module in vmd nvme nvme-core md-mod raid10 raid1 raid0 btrfs amdgpu; do
  grep -Eq "(^|/)$module[.]ko([.](xz|gz|zst))?$" "$LIST" ||
    fail "Missing boot-essential module: $module"
done
for file in init usr/sbin/mdadm usr/bin/btrfs etc/mdadm/mdadm.conf \
            scripts/local-block/mdadm scripts/local-bottom/mdadm \
            scripts/local-premount/btrfs; do
  grep -Eq "(^|/)$file$" "$LIST" || fail "Missing boot file: $file"
done
# Includes nvidia.ko, nvidia-uvm.ko, nvidia-modeset.ko, nvidia-drm.ko,
# and any other nvidia*.ko kernel module, including compressed variants.
if grep -Ei '(^|/)(nvidia([-_][^/]*)?)[.]ko([.](xz|gz|zst))?$' "$LIST"; then
  fail "NVIDIA module is present in the supposed no-NVIDIA initramfs."
fi
if grep -Eq '(^|/)nouveau[.]ko([.](xz|gz|zst))?$' "$LIST"; then
  fail "Nouveau unexpectedly present; V100 must remain unused during test."
fi
awk '$NF=="init" && $1=="-rwxr-xr-x" && $3=="root" && $4=="root" {ok=1}
     END {exit !ok}' "$VERBOSE" ||
  fail "Root init cpio permissions or ownership are incorrect."

printf '%s\n' "STEP 5 — Extract private archive for embedded config inspection."
install -d -m 0700 "$EXTRACT"
if bwrap --unshare-net --die-with-parent \
    --ro-bind / / --proc /proc --dev /dev --tmpfs /tmp \
    --bind "$WORK" "$WORK" --setenv TMPDIR /tmp \
    -- "$UNPACK" "$ARCHIVE" "$EXTRACT" >"$UNPACKLOG" 2>&1; then
  pass "Image extracted to isolated private directory."
else
  tail -n 40 "$UNPACKLOG" >&2
  fail "Unable to inspect extracted image."
fi
if [[ -f "$EXTRACT/init" ]]; then
  MAIN="$EXTRACT"
elif [[ -f "$EXTRACT/main/init" ]]; then
  MAIN="$EXTRACT/main"
else
  fail "No init executable found in extracted image."
fi
EMD="$MAIN/etc/mdadm/mdadm.conf"
RESUME="$MAIN/conf/conf.d/resume"
PRELOAD="$MAIN/conf/modules"
[[ -s "$EMD" && -f "$RESUME" && -s "$PRELOAD" ]] ||
  fail "Embedded RAID, resume or preload configuration is missing."
for uuid in "$MD0" "$MD1" "$MD2"; do
  grep -Fq "$uuid" "$EMD" || fail "Embedded mdadm lost array UUID: $uuid"
done
if grep -Fq "$MD3" "$EMD"; then
  fail "Embedded initrd contains stale md3."
fi
[[ "$(grep -Ec '^[[:space:]]*ARRAY[[:space:]]' "$EMD")" == 3 ]] ||
  fail "Embedded initrd has wrong MD array count."
grep -Exq 'RESUME=none' "$RESUME" ||
  fail "New image does not embed RESUME=none."
if grep -REq '^RESUME=(/dev/|UUID=|auto)' "$MAIN/conf"; then
  fail "Conflicting embedded resume setting."
fi
if grep -Ei '^[[:space:]]*nvidia([_-]|[[:space:]]|$)' "$PRELOAD"; then
  fail "NVIDIA early preload still configured."
fi
# modules.order is a kernel-build ordering index, not an archive file list.
# The Linux tree contains unrelated names like typec_nvidia.ko and
# nvidia-wmi-ec-backlight.ko. Reject only proprietary R580 module
# filenames; first-boot post-root isolation requires module_blacklist.
if grep -Ei '(^|/)(nvidia|nvidia-uvm|nvidia-modeset|nvidia-drm)[.]ko([.](xz|gz|zst))?([:[:space:]]|$)' \
   "$MAIN/usr/lib/modules/$KR/modules.dep" \
   "$MAIN/usr/lib/modules/$KR/modules.order"; then
  fail "Proprietary NVIDIA kernel module referenced in archived metadata."
fi

sha256sum "$ARCHIVE" >"$HASHES"
{
  printf 'HueyOS %s: private no-NVIDIA initramfs audit\n' "$KR"
  printf 'Source policy2 SHA-256: %s\n' "$POLICY2_SHA"
  printf 'New artifact: %s\n' "$ARCHIVE"
  cat "$HASHES"
  printf 'PASS: VMD/NVMe/MD RAID10/1/0/Btrfs/AMDGPU modules present.\n'
  printf 'PASS: no nvidia*.ko or nouveau.ko in initramfs list.\n'
  printf 'PASS: md0/md1/md2 UUIDs embedded; old md3 absent; RESUME=none.\n'
  printf 'PASS: root-owned executable /init found.\n'
  printf 'HOLD: no proof of post-root NVIDIA isolation from this artifact.\n'
  printf 'HOLD: any future one-time test entry MUST carry kernel parameter:\n'
  printf '  module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm\n'
  printf 'HOLD: only boot via a reviewed and separately approved procedure.\n'
  printf 'Nothing installed; live RAID, EFI, GRUB, NVIDIA and swap unchanged.\n'
} >"$AUDIT"
cat "$AUDIT"
printf 'Build log: %s\nAudit: %s\n' "$LOG" "$AUDIT"
