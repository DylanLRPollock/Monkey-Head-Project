# HueyOS 7.3.4 testing2 — first-boot gates and recovery readiness

**Status:** NO-GO for installation or reboot until explicitly approved by
the operator after the recovery route has been validated. This checklist
documents evidence; it does **not** authorize an install, EFI edit,
module load, firmware change, GRUB regeneration, or reboot.

**Host:** Debian Forky i9-12900K, running `7.2.15+deb14-amd64`.
The RX 570 currently drives the desktop; the Tesla V100 32 GB uses
proprietary NVIDIA 580.196.07. Intel VMD exposes four Optane drives
assembled as `/dev/md0` RAID10 `offset=2`, Btrfs root subvolume
`@rootfs`. `/home` uses `md2` RAID0 and swap uses `md1` RAID1.

## Artifacts: prepared, not installed

| Component | Verified evidence | Unverified |
| --- | --- | --- |
| Linux kernel image/deb | Built and SHA-256 pinned in the audit | Runtime boot, PCI/VMD probing |
| NVIDIA R580 modules | Built and hashed for `7.3.4-huey-testing2` | Runtime loading, CUDA, Vulkan; many objtool return-thunk diagnostics |
| Policy2 initramfs | SHA-256 `8bce591f673c74d3eeadfc53f8563aa7d20c6f22af2ac7adff4744bcfc6a05b7` | Actual early userspace execution/RAID assembly |
| Initrd configuration | md0, md1, md2 only; `RESUME=none`; root-owned executable `/init` | Btrfs root mount, exact system boot flow |
| Debian rescue kernels | `7.2.15` and `7.2.12` present in current GRUB menu | Independent EFI recovery path |

All work through policy2 ran without installing anything. The known
working `/boot/vmlinuz-7.2.15+deb14-amd64` and matching initrd
must be preserved.

## Mandatory recovery verification before first boot

1. **Physically accessible console:** Verify keyboard and monitor
   access at the machine, and identify which GPU output displays
   firmware/GRUB. Do not assume the Intel motherboard HDMI works
   merely because the system has an iGPU.
2. **Independent recovery medium:** Have a bootable Debian rescue USB
   appropriate to UEFI x86_64, and **test that it reaches a working
   shell** on this hardware before using a test kernel. Checking a USB
   filename or a boot entry alone is insufficient.
3. **Storage recovery capability:** Verify the rescue environment can
   detect Intel VMD and all four Optane devices, load NVMe/MD RAID10/
   Btrfs support, and identify the root array
   `f3c8b907:d3b5a85f:a2578548:157bf1d2` with no failed members.
   **Do not forcibly assemble, mount read-write, repair, rebuild or
   reshape** any RAID/Btrfs volume during qualification.
4. **Root identification:** The expected root Btrfs filesystem UUID is
   `dddebb01-4f58-4782-82b3-0e77209afc8c`, with
   `rootflags=subvol=@rootfs`. Root lives on `/dev/md0`; `/boot`
   is *inside the Btrfs root*, not on the ESP.
5. **EFI recovery:** The confirmed ESP is the mounted FAT32
   partition previously identified by PARTUUID
   `58fae902-4199-444f-93b8-e845b62d8b95`. Its Linux device
   name is **not stable**: it appeared as `/dev/sdc1` in the earlier
   audit but is currently shown at `/dev/sdd1` in the latest
   `lsblk` output. Verify its PARTUUID afresh before any action.
   Firmware entry `Boot0004` points to that partition and is the
   current known-working UEFI route. `Boot0005` points to an
   Optane MD RAID10 member PARTUUID and **must not** be treated
   as fallback. The second Kingston SSD's first partition was
   previously identified as `NO-BOOT`, not a populated ESP;
   in the latest scan it appears as `/dev/sdb1`. Resolve using
   PARTUUID or `/dev/disk/by-id/`, never by a historical
   `/dev/sdX` label.
6. **Rollback path:** Before any testing2 installation, write and
   review exact steps to select *Debian 7.2.15* from GRUB Advanced
   Options with the working `Boot0004` EFI route. If it cannot be
   selected, use the tested rescue medium, not `Boot0005`. Record
   offline backups of essential configuration and the EFI contents
   before installation. Backups must not rely on the same ESP.
7. **GRUB default behavior:** Current `GRUB_DEFAULT=0`,
   `GRUB_TIMEOUT=5`. A kernel package installation or `update-grub`
   may add a newest-first menu entry and affect which kernel boots
   by default. A first boot must therefore require an explicit
   operator-selected testing2 entry and a tested rollback selection;
   do not assume the old kernel remains the default.
8. **Kernel security:** `CONFIG_MITIGATION_RETHUNK=y`,
   `CONFIG_MODULE_SIG=y`, `CONFIG_MODULE_SIG_ALL=y`,
   `CONFIG_MODULE_SIG_FORCE` disabled. External proprietary R580
   modules produced extensive `objtool` warnings on binary sections.
   Neither successful compilation nor cpio content checks establish
   safe runtime behavior. Resolve/accept risk explicitly before
   testing and retain mitigation defaults.

## Offline-only status and read-only diagnostic

Use no installation commands for this review. Once a recovery USB is
connected, this read-only inventory helps identify it without
guessing device names:

```bash
lsblk -o NAME,PATH,MODEL,SIZE,TRAN,RM,HOTPLUG,TYPE,FSTYPE,LABEL,PARTUUID,MOUNTPOINTS
findmnt -n -M /boot/efi -o SOURCE,FSTYPE,TARGET
readlink -f /dev/disk/by-partuuid/58fae902-4199-444f-93b8-e845b62d8b95
cat /proc/mdstat
cat /proc/cmdline
```

Do not run `dd`, `wipefs`, `mkfs`, `mdadm --create` or
`grub-install` during the inventory. The audit reports are
informational, not a substitute for a tested rescue boot.

## Known policy2 build caveats

- The offline fsck hook could not infer Btrfs filesystem type from
  `root=UUID=...` inside the sandbox.
- One `libfakeroot internal error: payload not recognized!` was
  logged; critical /init cpio ownership and mode checks passed.
- Plymouth omitted DRM modules with `MODULES=list`.
- mdadm could not open live array device nodes inside isolated
  Bubblewrap; all three array UUIDs were verified in the *extracted
  finished image*.
- Policy2 includes `RESUME=none` to disable early hibernation
  resume for the first test while leaving the host swap unchanged.

**Gate conclusion:** the policy2 archive is prepared for consideration
as a test artifact, **not** yet authorized for installation or boot.

## Recovery-medium inventory update — 2026-11-16

The operator's latest `lsblk -o NAME,PATH,MODEL,SIZE,TRAN,TYPE,FSTYPE,LABEL,MOUNTPOINTS` output shows **no USB storage device**: only two SATA WDC 10 TB disks, two SATA Kingston 240 GB SSDs, four NVMe Intel Optane modules, and zram. The USB rescue gate has therefore **not yet been met**. Do not infer that a rescue flash drive is already connected or bootable.

The `/dev/sdX` enumeration **changed** since the previous audit:

| Physical device | Previously observed | Current observation |
| --- | --- | --- |
| Kingston 240 GB SSD containing mounted FAT32 `/boot/efi` | `/dev/sdc` with ESP `/dev/sdc1` | `/dev/sdd` with ESP `/dev/sdd1` |
| Kingston 240 GB SSD containing unformatted `NO-BOOT` first partition | `/dev/sdd` with `/dev/sdd1` | `/dev/sdb` with `/dev/sdb1` |
| WDC 10 TB native Btrfs members | `/dev/sda`, `/dev/sdb` | `/dev/sda`, `/dev/sdc` |

Names in the table are inventory snapshots, **not stable hardware identifiers**. The currently mounted ESP must be resolved by the historical PARTUUID and `findmnt` before any EFI work. Do not infer that the GPT partition GUID was rechecked by the current basic `lsblk` output, which did not print PARTUUID.

**No-go continues**: a USB device must be identified, and a bootable rescue environment with VMD/Optane/MD RAID10/Btrfs capability must be independently tested under explicit operator approval before installing or booting HueyOS testing2.

## EFI PARTUUID resolution verified (2026-11-16, later read-only report)

Operator reran `findmnt -n -M /boot/efi -o SOURCE,FSTYPE,TARGET`,
`readlink -f /dev/disk/by-partuuid/58fae902-4199-444f-93b8-e845b62d8b95`,
and `lsblk` with PARTUUID, TRAN, RM, HOTPLUG and FSTYPE.

**The mounted ESP is now positively matched by three checks:**
- `findmnt`: `/dev/sdd1 vfat /boot/efi`.
- The persistent `/dev/disk/by-partuuid/58fae902-4199-444f-93b8-e845b62d8b95` symlink resolves to `/dev/sdd1`.
- `lsblk` shows Kingston `/dev/sdd1` as VFAT with the *same* PARTUUID.

The previous UEFI `Boot0004` entry referenced this exact PARTUUID,
so the existing working EFI partition's identity is now reconciled
despite SATA enumeration changes. `Boot0005` references PARTUUID
`910477d6-ef14-4b2e-bd49-f08c1d42a7c7`, which current `lsblk`
identifies on **`/dev/nvme3n1p1`**, an Optane md0 RAID10 member,
**not** an EFI System Partition. The other Kingston SSD's
`/dev/sdb1` is still non-filesystem/unformatted, PARTUUID
`0626d8aa-7175-4a4b-80fd-1779040e8d37`.

No `TRAN=usb` devices or removable/hotplug storage were observed;
every physical internal disk had `RM=0`, `HOTPLUG=0`.
The USB recovery medium remains **absent and untested**.

**Recovery rule:** Continue to use the PARTUUID rather than any
historical `/dev/sdc1` or `/dev/sdd1` name. No disk, firmware
entry, or bootloader change was performed. Testing2 is still NO-GO.
