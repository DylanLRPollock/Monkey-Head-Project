#!/usr/bin/env bash
# HueyOS 7.3.4 testing2 initramfs isolation/readiness preflight.
# Read-only. Never generates an initramfs or writes to /lib/modules, /boot,
# mdadm config, EFI NVRAM, or running kernel.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || fail 'Run as the normal user, without sudo.'

ROOT="$HOME/huey-kernel-734"
REPORT_DIR="$ROOT/reports/testing2"
REPORT="$REPORT_DIR/initramfs-isolation-preflight.txt"
KR="7.3.4-huey-testing2"
OBJ="$ROOT/output/testing2-compile"
IMAGE="$ROOT/output/linux-image-${KR}_${KR}-1_amd64.deb"
[[ -d "$REPORT_DIR" ]] || fail "Missing report directory $REPORT_DIR"
[[ ! -e "$REPORT" ]] || fail "Report already exists, refusing overwrite: $REPORT"
for tool in dpkg-query sha256sum awk lsblk stat findmnt; do
  command -v "$tool" >/dev/null 2>&1 || fail "Missing inspection tool: $tool"
done

{
  printf 'HueyOS %s — initramfs isolation preflight (read-only)\n' "$KR"
  printf 'Running kernel: %s\n' "$(uname -r)"
  printf 'Target module tree must NOT be installed on the host for this preflight.\n\n'

  printf '=== Target package and configured object tree ===\n'
  if [[ -f "$IMAGE" ]]; then
    sha256sum "$IMAGE"
  else
    printf 'MISSING expected image package: %s\n' "$IMAGE"
  fi
  for artifact in "$OBJ/.config" "$OBJ/Module.symvers" "$OBJ/arch/x86/boot/bzImage"; do
    if [[ -s "$artifact" ]]; then
      sha256sum "$artifact"
    else
      printf 'MISSING expected compiled artifact: %s\n' "$artifact"
    fi
  done
  printf '\nHost module tree for testing2: '
  if [[ -e "/lib/modules/$KR" ]]; then
    printf 'EXISTS (investigate before any boot preparation)\n'
  else
    printf 'ABSENT (as expected for an uninstalled kernel)\n'
  fi

  printf '\n=== Installed initramfs / sandbox tools ===\n'
  for pkg in initramfs-tools initramfs-tools-core kmod bubblewrap uidmap \
             mdadm btrfs-progs; do
    dpkg-query -W -f='${Package} ${Status} ${Version}\n' "$pkg" 2>/dev/null || \
      printf '%s: not installed/unknown\n' "$pkg"
  done
  for cmd in mkinitramfs lsinitramfs depmod bwrap unshare fakeroot; do
    if command -v "$cmd" >/dev/null 2>&1; then
      printf '%s: %s\n' "$cmd" "$(command -v "$cmd")"
    elif [[ "$cmd" == depmod && -x /usr/sbin/depmod ]]; then
      printf 'depmod: /usr/sbin/depmod\n'
    else
      printf '%s: NOT FOUND\n' "$cmd"
    fi
  done
  if command -v mkinitramfs >/dev/null 2>&1; then
    printf '\nTarget-version support reported by mkinitramfs:\n'
    mkinitramfs --supported-target-version="$KR" 2>&1 || true
  fi

  printf '\n=== Unprivileged mount-namespace support ===\n'
  for sysctl in /proc/sys/kernel/unprivileged_userns_clone \
                /proc/sys/user/max_user_namespaces; do
    if [[ -r "$sysctl" ]]; then
      printf '%s: ' "$sysctl"
      cat "$sysctl"
    fi
  done
  if command -v unshare >/dev/null 2>&1; then
    if unshare --user --map-root-user -- true >/dev/null 2>&1; then
      printf 'Unprivileged user namespace: PASS (creation only)\n'
    else
      printf 'Unprivileged user namespace: BLOCKED\n'
    fi
  else
    printf 'Unprivileged user namespace: unshare unavailable\n'
  fi
  if command -v bwrap >/dev/null 2>&1; then
    if bwrap --ro-bind / / --proc /proc --dev-bind /dev /dev -- \
        /usr/bin/true >/dev/null 2>&1; then
      printf 'Minimal bubblewrap read-only sandbox: PASS\n'
    else
      printf 'Minimal bubblewrap read-only sandbox: BLOCKED\n'
    fi
  else
    printf 'Minimal bubblewrap read-only sandbox: bubblewrap unavailable\n'
  fi

  printf '\n=== Existing boot artifacts and GRUB bridge ===\n'
  findmnt -n -M /boot/efi -o SOURCE,FSTYPE,TARGET || true
  for path in /boot/efi/EFI/debian/grub.cfg \
              /boot/efi/EFI/debian/grubx64.efi \
              /boot/efi/EFI/debian/shimx64.efi \
              /boot/grub/grub.cfg \
              /boot/vmlinuz-7.2.15+deb14-amd64 \
              /boot/initrd.img-7.2.15+deb14-amd64 \
              /boot/vmlinuz-7.2.12+deb14-amd64 \
              /boot/initrd.img-7.2.12+deb14-amd64; do
    if [[ -e "$path" ]]; then
      stat -c 'PRESENT %n (%s bytes) %y' "$path"
    else
      printf 'MISSING %s\n' "$path"
    fi
  done

  printf '\n=== Explicit non-actions ===\n'
  printf 'No kernel installed, no modules loaded, no mdadm config changed, no initramfs generated.\n'
  printf 'This only selects a safe staging strategy for further review.\n'
} >"$REPORT" 2>&1
printf 'Read-only preflight recorded: %s\n' "$REPORT"
