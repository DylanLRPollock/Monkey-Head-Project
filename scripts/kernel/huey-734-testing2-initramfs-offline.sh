#!/usr/bin/env bash
# HueyOS 7.3.4 testing2: generate a test initramfs in a private user namespace.
# Never install kernel/modules, change the live /lib/modules or /boot,
# update initramfs/GRUB/EFI/RAID, load a module or reboot.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" -ne 0 ]] || fail 'Run without sudo.'

KR=7.3.4-huey-testing2
BASE="$HOME/huey-kernel-734"
REPORT="$BASE/reports/testing2"
STAGE="$BASE/output/testing2-initramfs-isolated"
EXTRACT="$STAGE/unpacked-image"
MODTREE="$EXTRACT/lib/modules/$KR"
CONF="$STAGE/config"
WORK="$STAGE/work"
PKG="$BASE/output/linux-image-7.3.4-huey-testing2_7.3.4-huey-testing2-1_amd64.deb"
VENDOR="$BASE/output/testing2-nvidia-r580/NVIDIA-Linux-x86_64-580.196.07/kernel"
ARCHIVE="$WORK/initrd.img-$KR"
LOG="$REPORT/testing2-isolated-initramfs-build.log"
DEPLOG="$REPORT/testing2-isolated-initramfs-depmod.log"
LIST="$REPORT/testing2-isolated-initramfs-files.txt"
RESULT="$REPORT/testing2-isolated-initramfs-report.txt"
SUMS="$REPORT/testing2-isolated-initramfs-sha256.txt"

for cmd in bwrap dpkg-deb lsinitramfs sha256sum awk grep install df find; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Required tool missing: $cmd"
done
DEPMOD="$(command -v depmod 2>/dev/null || true)"
[[ -n "$DEPMOD" ]] || DEPMOD=/usr/sbin/depmod
[[ -x "$DEPMOD" && -x /usr/sbin/mkinitramfs ]] || \
  fail 'Missing depmod or /usr/sbin/mkinitramfs.'
[[ -d "$REPORT" ]] || fail "Missing reporting directory: $REPORT"
for p in "$STAGE" "$LOG" "$DEPLOG" "$LIST" "$RESULT" "$SUMS"; do
  [[ ! -e "$p" ]] || fail "Refusing to overwrite existing output: $p"
done
[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]] || \
  fail 'Testing2 appears installed on the host; this script requires uninstalled testing2.'
[[ -s "$PKG" ]] || fail "Missing kernel package: $PKG"
check_sha() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$actual" == "$2" ]] || fail "SHA-256 mismatch for $1"
}
check_sha "$PKG" 25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0
for mod in nvidia nvidia-uvm nvidia-modeset nvidia-drm; do
  [[ -s "$VENDOR/$mod.ko" ]] || fail "NVIDIA module missing: $mod.ko"
done
check_sha "$VENDOR/nvidia.ko" 31113cef510d54e51b593c8a84780342bf8bfadb346dd09d93f2baa893c24c60
check_sha "$VENDOR/nvidia-uvm.ko" 49e7714072c73035db08736f2848bf180938614a3c5aee3dd56740bf4e3c7995
check_sha "$VENDOR/nvidia-modeset.ko" 076c6b14554a929ced396323574ef6b23edfc79142de0128f5f439ca359ae72a
check_sha "$VENDOR/nvidia-drm.ko" bcd7b35e78231d36bee6a95c9a40adfd0ca8ca0bc0db52b9f4b02da18fba00e7

free_kib="$(df -Pk "$BASE/output" | awk 'NR==2 {print $4}')"
[[ "$free_kib" =~ ^[0-9]+$ ]] && (( free_kib > 8 * 1024 * 1024 )) || \
  fail 'Require over 8 GiB free in the output filesystem.'
printf '%s\n' 'STEP 1 — Extract already-audited image into private staging.'
install -d -m 0700 "$EXTRACT" "$CONF/conf.d" "$CONF/hooks" "$WORK/tmp"
dpkg-deb --extract "$PKG" "$EXTRACT"
[[ -d "$MODTREE/kernel" && -s "$MODTREE/modules.builtin" ]] || \
  fail 'Extracted package lacks full kernel module tree.'
install -d -m 0700 "$MODTREE/updates"
for mod in nvidia nvidia-uvm nvidia-modeset nvidia-drm; do
  install -m 0644 "$VENDOR/$mod.ko" "$MODTREE/updates/$mod.ko"
done
if "$DEPMOD" -a -b "$EXTRACT" "$KR" >"$DEPLOG" 2>&1; then
  pass 'Private depmod succeeded.'
else
  tail -n 40 "$DEPLOG" >&2
  fail 'Private depmod failed; nothing installed on host.'
fi
[[ -s "$MODTREE/modules.dep" ]] || fail 'Private modules.dep missing.'

# Deliberately minimal: Debian's regular /usr/share/initramfs-tools hooks
# still run in the sandbox, including the installed mdadm hooks.
printf '%s\n' 'MODULES=list' 'BUSYBOX=auto' 'COMPRESS=gzip' \
  >"$CONF/initramfs.conf"
printf '%s\n' vmd nvme nvme_core md_mod raid10 raid1 raid0 btrfs \
  amdgpu nvidia nvidia_uvm >"$CONF/modules"

sandbox() {
  bwrap --unshare-user --uid 0 --gid 0 --unshare-pid --unshare-net \
    --die-with-parent --ro-bind / / --proc /proc --dev /dev \
    --tmpfs /tmp --tmpfs /lib/modules --dir "/lib/modules/$KR" \
    --ro-bind "$MODTREE" "/lib/modules/$KR" \
    --bind "$WORK" "$WORK" \
    --setenv PATH /usr/sbin:/usr/bin:/sbin:/bin \
    --setenv TMPDIR "$WORK/tmp" --setenv SOURCE_DATE_EPOCH 0 \
    -- "$@"
}
printf '%s\n' 'STEP 2 — Confirm private kernel module tree before generation.'
sandbox /bin/sh -c \
  'test -s "/lib/modules/$1/modules.dep" && test -s "/lib/modules/$1/updates/nvidia.ko" && test ! -e "/lib/modules/$(uname -r)"' \
  sh "$KR" || fail 'Private module tree bind mount was not usable.'
pass 'Target modules visible only within Bubblewrap.'

printf '%s\n' 'STEP 3 — Run mkinitramfs for testing2 inside isolated namespace.'
if sandbox /usr/sbin/mkinitramfs -d "$CONF" -o "$ARCHIVE" "$KR" \
  >"$LOG" 2>&1; then
  pass 'Isolated mkinitramfs returned success.'
else
  tail -n 70 "$LOG" >&2
  fail 'mkinitramfs failed. Preserve output and logs for diagnosis.'
fi
[[ -s "$ARCHIVE" ]] || fail 'No nonempty initramfs output.'
lsinitramfs "$ARCHIVE" >"$LIST" || fail 'Cannot inspect generated initramfs.'

printf '%s\n' 'STEP 4 — Verify boot-critical hooks, modules and target identity.'
for mod in vmd nvme nvme-core md-mod raid10 btrfs amdgpu nvidia nvidia-uvm; do
  grep -Eq "(^|/)$mod[.]ko([.](xz|zst|gz))?$" "$LIST" || \
    fail "Missing expected kernel module: $mod"
done
for p in usr/sbin/mdadm etc/mdadm/mdadm.conf scripts/local-block/mdadm; do
  grep -Eq "(^|/)$p$" "$LIST" || fail "Missing RAID assembly file: $p"
done
grep -Eq "(^|/)(usr/)?lib/modules/$KR/" "$LIST" || fail 'Wrong or missing kernel module release.'
if grep -Eq '(^|/)nouveau[.]ko([.](xz|zst|gz))?$' "$LIST"; then
  fail 'Nouveau unexpectedly included in initramfs.'
fi
sha256sum "$ARCHIVE" >"$SUMS"
{
  printf 'PASS: isolated test initramfs generated for %s\n' "$KR"
  printf 'Archive: %s\n' "$ARCHIVE"
  cat "$SUMS"
  printf 'Contents: VMD/NVMe/RAID10/Btrfs, AMDGPU, NVIDIA, mdadm early hooks\n'
  printf 'Read-only host boot files: untouched\n'
  printf 'WARNING: archive content checks do not establish bootability\n'
  printf 'WARNING: proprietary NVIDIA rethunk warnings remain unresolved\n'
} >"$RESULT"
cat "$RESULT"
printf 'Build log: %s\nAudit: %s\nContents: %s\n' "$LOG" "$RESULT" "$LIST"
