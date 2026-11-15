# Full Debian 7.2.15 Kconfig review for HueyOS Linux 7.3.4

**Status:** full source configuration parsed on 2026-11-14/15; **not**
a completed Linux 7.3.4 Kconfig migration or a qualified build.

**Source:** user-provided `/boot/config-7.2.15+deb14-amd64` exported
as `current-kernel.config`. Never commit the whole machine-derived
configuration to the public repository.

- Lines: **11,982**
- Distinct Kconfig symbols: **9,884**, no duplicate assignments
- Enabled `=y`: **2,784**; modules `=m`: **4,036**;
  explicitly disabled `=n`: **2,849**
- SHA-256 of decompressed configuration:
  `1d9e4bc522860e2a358bb40f03c56fa4f17d4b0f7f3d6e24cac62fb543a843ed`
- Linux configuration banner: `Linux/x86 7.2.15`
- Build compiler recorded in the config:
  `x86_64-linux-gnu-gcc-16 (Debian 16.2.0-4) 16.2.0`
- Assembler/linker version metadata: binutils **2.47.50**
- Rust recorded: `rustc 1.97.1`, `CONFIG_RUST=y`.
- `CONFIG_DEBUG_INFO_BTF=y`, `CONFIG_DEBUG_INFO_BTF_MODULES=y`,
  `CONFIG_PAHOLE_VERSION=132`.
- Kernel module compression: `CONFIG_MODULE_COMPRESS_XZ=y`.
- `CONFIG_LOCALVERSION=""` and `CONFIG_LOCALVERSION_AUTO=n`;
  Debian's `+deb14-amd64` suffix is external to those two settings.
  This proves the need for the HueyOS pre-compile exact release gate.

## Critical root and data devices — PRESERVE

| Component | Observed Kconfig | Why |
| --- | --- | --- |
| Intel VMD | `CONFIG_VMD=m` | Exposes four Optane modules behind VMD domain |
| NVMe | `CONFIG_NVME_CORE=m`, `CONFIG_BLK_DEV_NVME=m` | Optane devices |
| Linux software MD | `CONFIG_BLK_DEV_MD=m` | All three MD arrays |
| Optane RAID10 | `CONFIG_MD_RAID10=m` | Root `/dev/md0` |
| SATA SSD RAID0 | `CONFIG_MD_RAID0=m` | Non-redundant `/home` |
| SATA SSD RAID1 | `CONFIG_MD_RAID1=m` | Swap |
| Btrfs | `CONFIG_BTRFS_FS=m` | Root, home and archival disks |
| SATA AHCI | `CONFIG_SATA_AHCI=m` | Kingston + WD drives |
| EFI/GPT | `CONFIG_EFI=y`, `CONFIG_EFI_STUB=y`, `CONFIG_EFI_PARTITION=y` | UEFI/GRUB |
| FAT/VFAT | `CONFIG_FAT_FS=m`, `CONFIG_VFAT_FS=m` | EFI system partition |
| Ext4 | `CONFIG_EXT4_FS=m` | Optional recovery/other devices |

These are modular on Debian's working baseline. The **complete
initramfs and mdadm userspace hooks** are therefore a release-blocking
dependency. Do not use `localmodconfig` or eliminate the root's VMD/NVMe/
RAID10/Btrfs chain. A Kconfig-only test is insufficient: verify the
resulting `lsinitramfs` contents, correct `rootflags=subvol=@rootfs`,
MD RAID assembly and actual cold boots.

The pure offline guard `scripts/kernel/validate_i9_kconfig.py` checks
the critical symbols in `baseline`, `testing1` or `intel-only`
stages; it never modifies the host and does not prove bootability.

## GPU and media baseline

- Intel UHD 770: `CONFIG_DRM_I915=m`; `CONFIG_DRM_XE=m` is also
  configured but neither currently has an enumerated iGPU device.
  The actual handover requires UEFI display enablement, motherboard
  HDMI/DP, driver binding, Wayland and rollback checks.
- RX 570: `CONFIG_DRM_AMDGPU=m`, currently bound and driving display.
  Retain in `testing1` until Intel-only graphics qualification.
- Tesla V100: Nouveau is `CONFIG_DRM_NOUVEAU=m` in Debian's generic
  config, while the actual device is successfully bound to NVIDIA
  proprietary 580.196.07. For the specialized HueyOS V100 profile,
  **disable Nouveau** to remove an unnecessary driver collision.
- `CONFIG_MODULES=y` and **`CONFIG_MODVERSIONS=n`**.
  The working NVIDIA `vermagic` lacks `modversions`: preserve `n`
  for testing1, and build matching modules for the exact `KERNELRELEASE`.
- `CONFIG_MODULE_SIG=y`, `CONFIG_MODULE_SIG_FORCE=n`;
  Secure Boot currently disabled. Preserve signing capability; do not
  pretend signing is mandatory in the current boot state.
- Generic console fallback:
  `CONFIG_FB_EFI=y`, `CONFIG_FB_VESA=y`,
  `CONFIG_FRAMEBUFFER_CONSOLE=y`, `CONFIG_VT_CONSOLE=y`.
  `CONFIG_DRM_SIMPLEDRM=n` on baseline; do not unilaterally switch
  console/DRM behavior before first-boot tests.

## i9 CPU, latency and diagnostics — PRESERVE initially

- `CONFIG_PREEMPT_DYNAMIC=y`, `CONFIG_PREEMPT_LAZY=y`;
  `CONFIG_HZ=250`, `CONFIG_HZ_250=y`, high-resolution timers enabled.
- `CONFIG_NO_HZ_FULL=y` means the feature is available, not proof
  that particular CPUs are currently isolated by boot parameters.
- `CONFIG_X86_INTEL_PSTATE=y`, `CONFIG_INTEL_IDLE=y`,
  `CONFIG_INTEL_HFI_THERMAL=y`, `CONFIG_ENERGY_MODEL=y`.
- `CONFIG_CPU_MITIGATIONS=y` and modern Intel vulnerability mitigations.
  No `mitigations=off` or unreviewed CPU-frequency changes.
- `CONFIG_BPF=y`, `CONFIG_BPF_SYSCALL=y`,
  `CONFIG_DEBUG_INFO_BTF=y`, ftrace and kprobes enabled.
  These support observability and should not be trimmed from testing1.
- `CONFIG_RUST=y`: before `olddefconfig`, verify the source-supported
  Rust compiler and bindgen/LLVM toolchain; the saved `.config` is
  **not** proof that the toolchain is installed today. If rebuilding
  Rust-enabled drivers cannot be supported, decide an explicit config
  change and record its delta rather than silently dropping `CONFIG_RUST`.
- Preserve Intel I226-V `CONFIG_IGC=m`, Intel CNVi Wi-Fi
  `CONFIG_IWLWIFI=m`, USB xHCI as modules, HD Audio support,
  IOMMU, TPM and watchdog dependencies.

## Compiler policy

Forky currently uses GCC 16.2 for the running kernel, and GCC/G++14 are
installed for CUDA 12.9. **Do not confuse the CUDA host compiler with
the kernel compiler.**

Prefer testing upstream 7.3.4 with a pinned GCC 16 toolchain matching
this working kernel; independently verify the proprietary R580 DKMS
build with the **same kernel compiler**. CUDA 12.9 `nvcc` should select
GCC/G++ 14 as its host compiler for V100 `sm_70` workloads. The
7.3.4 upstream Kconfig will regenerate compiler/version feature
metadata; it must never retain stale derived GCC 16 settings blindly
if we choose a different compiler.

## Before first build

1. Download/verify signed upstream 7.3.4 source, pin the SHA-256 in
   `source.lock.json` and record signature provenance.
2. Run source-specific `olddefconfig` using the pinned build toolchain,
   resolve deprecated/new Kconfig symbols, and produce a complete delta.
3. Run `validate_i9_kconfig.py --stage testing1` on the effective
   7.3.4 `.config`; errors block build. Test output must separately
   verify modules available within initramfs and all `mdadm` scripts.
4. Verify exact `7.3.4-huey-testing1` from `make -s kernelrelease`.
5. Preserve two working Debian kernel boot entries, backups of
   `/home`/EFI, and sufficient root capacity; build in a separate
   non-root workspace. Root `/boot` has ~14 GiB free, not a dedicated
   partition.
6. Stage NVIDIA 580.196.07 source and binary artifacts separately;
   prove kernel 7.3.4 driver compilation and `vermagic` before boot.
7. Test i915 desktop migration, AMD fallback, cold boot, V100 CUDA/
   Vulkan and RAID health; qualify stable only on completed evidence.

**Limit:** There is not yet a 7.3.4 `olddefconfig` result, so this
document is a **fully parsed 7.2.15 baseline review**, not a claim
that every 7.3.4 Kconfig symbol or proprietary module is compatible.
