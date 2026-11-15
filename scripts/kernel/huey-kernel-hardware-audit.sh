#!/usr/bin/env bash
# HueyOS Linux 7.3.4 pre-build hardware audit.
# READ ONLY: no sudo, apt, installation, driver reload, disk changes or reboot.
# Save output locally and redact boot UUIDs / paths before sharing.
set -u
export LC_ALL=C

section() { printf '\n===== %s =====\n' "$1"; }
run() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'
  "$@" 2>&1 || printf '(unavailable, inaccessible or nonzero exit)\n'
}
read_optional() {
  if [[ -r "$1" ]]; then
    printf '%s: ' "$1"
    cat -- "$1"
    printf '\n'
  fi
}

section "Host, kernel, boot chain and Secure Boot"
run uname -a
run cat /etc/os-release
run cat /proc/cmdline
run findmnt -no SOURCE,FSTYPE,OPTIONS /
run findmnt -R -o SOURCE,TARGET,FSTYPE,OPTIONS
run ls -l /boot
command -v mokutil >/dev/null && run mokutil --sb-state || true
for dmi in board_vendor board_name board_version bios_version bios_date; do
  read_optional "/sys/class/dmi/id/$dmi"
done

section "i9 P/E topology, RAM and build toolchain"
run lscpu
run free -h
for cc in gcc gcc-14 g++-14 make ld; do
  if command -v "$cc" >/dev/null; then run "$cc" --version; fi
done
for p in /sys/devices/system/cpu/intel_pstate/status \
         /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver; do
  read_optional "$p"
done
run grep -m1 -E '^microcode[[:space:]]*:' /proc/cpuinfo

section "PCI controllers, GPUs and bound drivers"
run lspci -nnk
run lspci -tv
for status in /sys/class/drm/card*/status /sys/class/drm/card*-*/status; do
  [[ -r "$status" ]] && read_optional "$status"
done

section "Storage device topology (serial numbers omitted)"
run lsblk -e7 -o NAME,TYPE,SIZE,TRAN,MODEL,FSTYPE,MOUNTPOINTS
read_optional /proc/mdstat
if command -v mdadm >/dev/null; then run mdadm --detail --scan; fi
if command -v dmsetup >/dev/null; then run dmsetup ls --tree; fi
if command -v btrfs >/dev/null; then run btrfs filesystem show; fi
run swapon --show

section "NVIDIA V100, CUDA 12.9 and temperature"
if command -v nvidia-smi >/dev/null; then
  run nvidia-smi --query-gpu=name,pci.bus_id,driver_version,memory.total,temperature.gpu,temperature.memory,utilization.gpu,power.draw --format=csv
fi
if command -v nvcc >/dev/null; then
  run nvcc --version
  printf '%s\n' '+ nvcc --list-gpu-arch (Volta detection)'
  if nvcc --list-gpu-arch 2>/dev/null | grep -qx 'compute_70'; then
    printf 'sm_70 compilation target: available\n'
  else
    printf 'sm_70 compilation target: NOT reported; do not compile V100 kernels\n'
  fi
else
  printf 'nvcc unavailable (this does not mean NVIDIA driver is missing)\n'
fi
if command -v sensors >/dev/null; then run sensors; fi

section "Current kernel config: critical boot and GPU symbols"
config="/boot/config-$(uname -r)"
if [[ -r "$config" ]]; then
  grep -E '^(CONFIG_(LOCALVERSION|LOCALVERSION_AUTO|MODULES|MODVERSIONS|MODULE_SIG|DRM_I915|DRM_AMDGPU|DRM_NOUVEAU|VMD|BLK_DEV_NVME|NVME_CORE|SATA_AHCI|BLK_DEV_MD|MD_RAID1|DM_RAID|BLK_DEV_DM|BTRFS_FS|EXT4_FS|INTEL_IOMMU|X86_INTEL_PSTATE|INTEL_IDLE|MICROCODE_INTEL|IGC|IWLWIFI)=|# CONFIG_(LOCALVERSION_AUTO|DRM_I915|DRM_AMDGPU|VMD|BLK_DEV_NVME|SATA_AHCI|BTRFS_FS) is not set$)' "$config" || true
  printf 'Full kernel config: %s\n' "$config"
else
  printf 'Missing /boot/config for running kernel; investigate /proc/config.gz\n'
fi

section "PCIe GPU link widths and maximum capability"
for dev in /sys/bus/pci/devices/*; do
  [[ -r "$dev/class" ]] || continue
  class=$(cat "$dev/class" 2>/dev/null || true)
  case "$class" in
    0x0300*|0x0302*)
      printf "PCI device: %s\n" "${dev##*/}"
      for info in current_link_speed current_link_width max_link_speed max_link_width; do
        read_optional "$dev/$info"
      done
    ;;
  esac
done

section "Summary"
printf 'This script has not changed any host state.\n'
printf 'For optional privileged READ-ONLY checks, run manually:\n'
printf '  sudo dkms status\n'
printf '  sudo modinfo -F version nvidia\n'
printf '  sudo modinfo -F vermagic nvidia\n'
printf '  sudo mdadm --detail --scan\n'
