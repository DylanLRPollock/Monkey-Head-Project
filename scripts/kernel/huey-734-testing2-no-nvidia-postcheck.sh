#!/usr/bin/env bash
# Read-only audit of EXISTING no-NVIDIA test1 archive after a false-positive
# modules.order check. Never rebuild or modify the archive, kernel, or host.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" -ne 0 ]] || fail 'Do not run as root or with sudo.'

KR=7.3.4-huey-testing2
ROOT="$HOME/huey-kernel-734"
STAGE="$ROOT/output/testing2-initramfs-isolated"
WORK="$STAGE/work/no-nvidia-test1"
POLICY2="$STAGE/work/fakeroot-policy2"
REPORT="$ROOT/reports/testing2"
ARCHIVE="$WORK/initrd.img-$KR"
LIST="$REPORT/testing2-no-nvidia-list.txt"
VERBOSE="$REPORT/testing2-no-nvidia-verbose.txt"
BUILDL="$REPORT/testing2-no-nvidia-build.log"
EXTRACT="$WORK/unpacked"
AUDIT="$REPORT/testing2-no-nvidia-postcheck.txt"
POLICY2_SHA=8bce591f673c74d3eeadfc53f8563aa7d20c6f22af2ac7adff4744bcfc6a05b7
MD0=f3c8b907:d3b5a85f:a2578548:157bf1d2
MD1=a3068941:490dcc7f:ce9dedcc:6ef270e0
MD2=646adf0e:63c18bd3:053728a3:66c836b5
MD3=38a8dd4b:f15c5eca:fafe213a:2962ac03

for cmd in sha256sum lsinitramfs awk grep cmp find; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing $cmd"
done
[[ -s "$ARCHIVE" && -s "$LIST" && -s "$VERBOSE" && -s "$BUILDL" ]] ||
  fail 'Missing archive, original listings or build log.'
[[ -s "$POLICY2/initrd.img-$KR" ]] || fail 'Missing source policy2 archive.'
[[ ! -e "$AUDIT" ]] || fail "Report exists; refusing overwrite: $AUDIT"
[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]] ||
  fail 'Testing2 appears installed; halt read-only qualification.'
[[ "$(sha256sum "$POLICY2/initrd.img-$KR" | awk '{print $1}')" == "$POLICY2_SHA" ]] ||
  fail 'Source policy2 SHA-256 does not match the pinned version.'

# Cross-check that the original successful listing came from this actual archive.
cmp -s "$LIST" <(lsinitramfs "$ARCHIVE") ||
  fail 'Archive content differs from the saved original module inventory.'
if [[ -f "$EXTRACT/init" ]]; then
  MAIN="$EXTRACT"
elif [[ -f "$EXTRACT/main/init" ]]; then
  MAIN="$EXTRACT/main"
else
  fail 'Previously extracted image does not contain /init.'
fi
for file in "$MAIN/etc/mdadm/mdadm.conf" "$MAIN/conf/conf.d/resume" \
            "$MAIN/conf/modules" "$MAIN/usr/lib/modules/$KR/modules.dep" \
            "$MAIN/usr/lib/modules/$KR/modules.order"; do
  [[ -f "$file" ]] || fail "Required extracted artifact missing: $file"
done
EMD="$MAIN/etc/mdadm/mdadm.conf"
RESUME="$MAIN/conf/conf.d/resume"
PRELOAD="$MAIN/conf/modules"
MODDIR="$MAIN/usr/lib/modules/$KR"

printf '%s\n' 'STEP 1 — Verify boot-critical module files within the archived inventory.'
for module in vmd nvme nvme-core md-mod raid10 raid1 raid0 btrfs amdgpu; do
  grep -Eq "(^|/)$module[.]ko([.](gz|xz|zst))?$" "$LIST" ||
    fail "Missing boot-critical module $module."
done
for file in init usr/sbin/mdadm usr/bin/btrfs etc/mdadm/mdadm.conf \
            scripts/local-block/mdadm scripts/local-bottom/mdadm \
            scripts/local-premount/btrfs; do
  grep -Eq "(^|/)$file$" "$LIST" || fail "Missing early boot file $file."
done

printf '%s\n' 'STEP 2 — Check ACTUAL archived modules, not unrelated modules.order entries.'
# These are the proprietary R580 module basenames we must never load
# during the first kernel-only test. Kernel's typec_nvidia and
# nvidia-wmi-ec-backlight are unrelated and are NOT proprietary R580.
PROPRIETARY='(^|/)(nvidia|nvidia-uvm|nvidia-modeset|nvidia-drm)[.]ko([.](gz|xz|zst))?$'
if grep -Eiq "$PROPRIETARY" "$LIST"; then
  fail 'Proprietary NVIDIA kernel module found in actual archive inventory.'
fi
if grep -Eq '(^|/)nouveau[.]ko([.](gz|xz|zst))?$' "$LIST"; then
  fail 'Nouveau module unexpectedly included.'
fi
# Includes stray files even if their names somehow escaped the archive listing.
if find "$MAIN" -type f \( -name 'nvidia.ko*' -o -name 'nvidia-uvm.ko*' \
    -o -name 'nvidia-modeset.ko*' -o -name 'nvidia-drm.ko*' \
    -o -name 'nouveau.ko*' \) -print -quit | grep -q .; then
  fail 'Proprietary/Nouveau binary found inside extracted initramfs.'
fi
# A full kernel build's modules.order references many modules that do
# not exist in this initrd. Only a reference to the R580 modules is
# disqualifying; an in-tree NVIDIA-named driver is not.
if grep -Ei '(^|/)(updates/)?(nvidia|nvidia-uvm|nvidia-modeset|nvidia-drm)[.]ko([.](gz|xz|zst))?([:[:space:]]|$)' \
    "$MODDIR/modules.dep" "$MODDIR/modules.order"; then
  fail 'Proprietary R580 module reference found in dependency metadata.'
fi
for f in "$MODDIR/modules.alias" "$MODDIR/modules.softdep"; do
  if [[ -f "$f" ]] && grep -Ei '(^|[[:space:]/])(nvidia|nvidia-uvm|nvidia-modeset|nvidia-drm)([[:space:]/:]|$)' "$f"; then
    fail "Proprietary module alias/softdep reference found in $f."
  fi
done
if grep -Ei '^[[:space:]]*(nvidia|nvidia[-_]uvm|nvidia[-_]modeset|nvidia[-_]drm)([[:space:]]|$)' "$PRELOAD"; then
  fail 'Proprietary NVIDIA module still in initramfs preload policy.'
fi
pass 'No proprietary NVIDIA or Nouveau module is included in initramfs.'

printf '%s\n' 'STEP 3 — Recheck embedded RAID/resume configuration and cpio /init metadata.'
for uuid in "$MD0" "$MD1" "$MD2"; do
  grep -Fq "$uuid" "$EMD" || fail "Embedded mdadm.conf is missing $uuid."
done
if grep -Fq "$MD3" "$EMD"; then
  fail 'Stale inactive md3 UUID present.'
fi
[[ "$(grep -Ec '^[[:space:]]*ARRAY[[:space:]]' "$EMD")" == 3 ]] ||
  fail 'Embedded mdadm.conf does not contain exactly three ARRAY entries.'
grep -Exq 'RESUME=none' "$RESUME" || fail 'Embedded resume is not disabled.'
if grep -REq '^RESUME=(/dev/|UUID=|auto)' "$MAIN/conf"; then
  fail 'Conflicting automatic resume setting found.'
fi
awk '$NF=="init" && $1=="-rwxr-xr-x" && $3=="root" && $4=="root" {ok=1}
     END {exit !ok}' "$VERBOSE" ||
  fail 'Archived /init is not root-owned and executable.'
pass 'RAID identifiers, no md3, RESUME=none, and /init cpio mode verified.'

DIGEST="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
{
  printf 'HueyOS %s: post-build no-NVIDIA archive inspection\n' "$KR"
  printf 'Existing archive: %s\n' "$ARCHIVE"
  printf 'SHA-256: %s\n' "$DIGEST"
  printf 'PASS: required VMD, NVMe, RAID10/1/0, Btrfs, AMDGPU, early hooks.\n'
  printf 'PASS: no proprietary R580 or Nouveau module in archive.\n'
  printf 'PASS: md0/md1/md2 configured, stale md3 absent, RESUME=none.\n'
  printf 'PASS: /init metadata root:root 0755.\n'
  printf 'NOTE: in-tree typec_nvidia and nvidia-wmi-ec-backlight entries in modules.order are unrelated to proprietary R580.\n'
  printf 'HOLD: post-root autoload requires kernel-level module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm.\n'
  printf 'HOLD: recovery RAID assembly and NVIDIA compatibility remain outside this check.\n'
  printf 'No archive rebuild, sudo, kernel install, EFI/GRUB/RAID changes or reboot.\n'
} >"$AUDIT"
cat "$AUDIT"
printf 'Report: %s\n' "$AUDIT"
