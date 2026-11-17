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

## Recovery USB connected — offline inventory pass (2026-11-16)

The operator captured `lsblk` **before and after** physically connecting
a new USB drive. Before: no external USB storage device. After:
`/dev/sde` (generic "Storage Device", `14.8G`, `TRAN=usb`,
`RM=1`, `HOTPLUG=1`) appeared without changing existing mounts.

The newly observed USB contains:
- `/dev/sde1`: `756M` `iso9660`, mounted at
  `/run/media/dlrp/Debian 13.7.0 amd64 n...` (label truncated
  by terminal output; consistent with a Debian 13.7 amd64 netinst ISO).
  Partition UUID `2ca9630d-01`.
- `/dev/sde2`: `3.6M` FAT (`vfat`), partition UUID
  `2ca9630d-02`. Small EFI partition layout is consistent
  with an isohybrid installer stick.

**Evidence level:** removable Debian 13.7 installer USB presence and
partition signatures are CONFIRMED. UEFI boot from it, rescue menu,
installer kernel Intel VMD support, MD RAID10 activation, Btrfs root
visibility, and usable shell are **NOT YET VERIFIED**. Do not confuse
a mounted installer ISO with a successfully boot-tested rescue system.
Debian's official installer manual documents rescue mode:
https://www.debian.org/releases/trixie/amd64/

**Safe next review:** use read-only `lsblk`, `blkid`,
`findmnt` and inspection of the already-mounted ISO contents.
Never issue `dd`, `mkfs`, `wipefs`, installer partitioning,
GRUB reinstall, or a firmware boot-variable update for this check.

A physical firmware boot-menu USB boot and rescue-shell verification
is a **separate future explicit-approval step**, not yet performed.
For boot qualification choose the installer **rescue** option,
never partition/format/install, and use non-modifying storage detection.
Recovery from an unverified medium is not yet adequate rollback.

## Debian 13.7 USB installer file check — positive (2026-11-16)

The operator confirmed `/dev/sde` is a 14.8 GiB removable
USB device containing an ISO9660 Debian 13.7.0 amd64 installer
volume and a 3.6 MiB VFAT EFI partition. The physical `sde1`
volume UUID is `2026-09-12-09-39-25-00`, partition UUID
`2ca9630d-01`; `sde2` has FAT UUID `DEB0-0001`,
partition UUID `2ca9630d-02`.

Read-only file listing of the **mounted** installer filesystem:
- `EFI/boot/bootx64.efi` (about 1012 KiB)
- `EFI/boot/grubx64.efi` (about 2.6 MiB)
- `install.amd/vmlinuz` (about 12 MiB)
- `install.amd/initrd.gz` (about 24 MiB)
- `md5sum.txt` (approximately 82 KiB)
- `boot/`, `isolinux/`, `.disk/`, `pool/`, and `firmware/`

This establishes the presence of plausible **UEFI installer files**
and an installer kernel/initrd, but says nothing definitive about
firmware boot behavior, the rescue menu, signature trust, ISO
content-integrity verification or storage access from the
installer. Before any recovery reboot, a non-destructive
`md5sum -c md5sum.txt` on the mounted ISO can check against
its embedded file manifest. This is useful for accidental file
corruption, **not** authentication against an independent trusted
official SHA-256 digest. Use rootless read-only checks.

The bootable-rescue gate stays OPEN until an **explicitly approved**
USB-only recovery boot reaches a shell and verifies Intel VMD,
four NVMe/Optane RAID10 member visibility, `md0` UUID,
and Btrfs root access without writes.

## USB checksum check — efi.img mismatch, documented Debian case (2026-11-16)

The operator ran the read-only mounted-ISO integrity check with
`md5sum --check --quiet md5sum.txt`.
**Result: exactly one file mismatch**:

```
./boot/grub/efi.img: FAILED
md5sum: WARNING: 1 computed checksum did NOT match
```

This **must not be silently marked PASS**; the USB's internal manifest
does not completely match. However, Debian's official
[VerifyISOImage](https://wiki.debian.org/VerifyISOImage) and
[XorrisoDdTarget](https://wiki.debian.org/XorrisoDdTarget)
documentation describe **this exact `efi.img` checksum mismatch**.
On a hybrid ISO, `boot/grub/efi.img` is the FAT ESP image also
exposed as a writable partition on the USB. A previous OS or
firmware/installer session can alter FAT metadata or add files,
producing a checksum mismatch without damaging the rest of the
installer. Debian bug [#1056998](https://bugs.debian.org/1056998)
documents an example and the overlap mechanism.

**Evidence-based interpretation:** no other file was reported
mismatching by the command, but a single failure does not prove
the EFI image is harmless or that it can boot on this host. The
first-boot recovery gate remains UNMET. Do **not** rewrite the
stick just for this finding until a safe, non-destructive
`fsck.vfat -n` check of its partition GUID
`2ca9630d-02` and, if useful, comparison against a separately
downloaded and officially verified ISO. Never run repair-mode
fsck or a write operation on this recovery candidate during
qualification. The official signed Debian ISO SHA256SUMS can
authenticate an original download but cannot be expected to
match a previously modified hybrid USB image.

## Debian USB FAT partition — read-only consistency check (2026-11-16)

After the Debian installer USB's internal md5sum check found only
`boot/grub/efi.img` changed, the operator used its persistent
PARTUUID `2ca9630d-02` to select the 3.6 MiB VFAT partition
(currently `/dev/sde2`). `findmnt` showed it unmounted,
and `sudo /usr/sbin/fsck.vfat -n` emitted:

```
fsck.fat 4.2 (2021-01-31)
/dev/sde2: 6 files, 1821/1828 clusters
```

**Result:** No FAT errors or repair recommendations appeared.
The command's exit status was not separately recorded. The EFI FAT
filesystem is almost completely allocated (1821/1828 clusters),
which is not by itself a filesystem integrity failure on this
small prebuilt EFI volume. Debian's fsck.fat `-n` means
a non-writing/no-operation check.

This supports **FAT structural consistency only**. It does **not**
prove that `efi.img` is identical to the Debian release's original
contents, that Secure Boot accepts the EFI loaders, or that the
firmware can boot this USB. Do not modify/repair/rewrite the
stick solely for the embedded EFI image checksum mismatch.

**Recovery-media status:** identified USB + installer files + no
reported FAT filesystem errors = positive offline checks;
an actual UEFI rescue-mode boot and Optane/VMD/RAID10/Btrfs
visibility test are still REQUIRED before this becomes a
qualified independent recovery route.

### Controlled USB rescue-boot gate (not yet authorized)

Require the operator's explicit approval for a reboot and
verified local physical access to keyboard/monitor. Use the
motherboard's **one-time boot device picker** to choose the
removable Debian UEFI USB, leaving firmware BootOrder,
`Boot0004`, the host ESP, and installed GRUB unchanged.
At the Debian installer boot menu, choose **Advanced options >
Rescue mode** (or equivalent). Never select ordinary Install or
Graphical install; do not partition or repair any disk.

In the installer rescue shell, inspect devices using non-destructive
commands such as `cat /proc/mdstat`,
`lsblk -f`, `cat /proc/cmdline` and, if available,
`mdadm --detail --scan`. Do not manually force-assemble,
mount read-write, reshape, resync, create filesystems, or run
`grub-install`. The rescue environment may assemble arrays or
offer to mount a root volume automatically; these actions require
careful inspection of prompts, and the operator should avoid
any step with unclear write semantics. The next phase is
**observation**, not repair. Any necessary mount/assembly
must be separately assessed for read-only safety.

Official Debian rescue-mode documentation:
https://www.debian.org/releases/trixie/amd64/ch08s06.en.html

Testing2 remains uninstalled and first-boot status is **NO-GO**.

## First USB rescue boot completed — partial recovery qualification (2026-11-16)

The USB has now been **booted successfully** through the physical
UEFI boot picker. Debian 13.7 Rescue Mode reached the BusyBox 1.37
shell after selecting **Do not use a root file system**.
In the rescue shell:

- `ls /dev/nvme*n1p1` returned all four Intel Optane
  member partitions.
- `cat /proc/mdstat` showed supported RAID personalities
  but **no active MD arrays**. The rescue session deliberately
  **did not assemble md0**, mount Btrfs root, or repair anything.
- `exit` returned from the rescue shell. Following the
  reboot, `uname -r` confirmed the known-good
  `7.2.15+deb14-amd64` kernel.
- All three internal arrays came up in the running Debian
  system: `md0` RAID10 `[4/4] [UUUU]`,
  `md1` RAID1 `[2/2] [UU]`, `md2` active RAID0.
  `nvidia-smi` confirms the V100 32 GB is operating with
  the original proprietary driver `580.196.07`.

**Gate changes:** the independent USB firmware boot, BusyBox
rescue shell and VMD/Optane device detection are now VERIFIED.
The ability to assemble `md0` and access
`@rootfs` read-only from rescue has **not** been tested.
A successful normal boot does not substitute for full rescue
readiness if a future kernel/GRUB problem affects the host.
No further rescue intervention is warranted just to get a
green checklist; the remaining uncertainty must be
acknowledged in the first-boot risk decision.

The operator also ran `sudo update-grub` on the recovered
working kernel. GRUB configuration was regenerated and
both known-good kernel/initrd pairs were discovered.
`os-prober` was disabled, which does not prevent these
Debian entries. Before a test boot, confirm the current
generated GRUB entries still use expected Btrfs
`root=UUID=dddebb01-4f58-4782-82b3-0e77209afc8c`
and `rootflags=subvol=@rootfs`. Do **not** automatically
regenerate or change GRUB again while offline qualifications
continue.

No kernel-package install, module insertion, or boot into
`7.3.4-huey-testing2` has been carried out. First test boot
is still on HOLD pending NVIDIA ret-thunk review and
explicit operator approval of the rollback plan.

## GRUB root parameters re-verified after successful host update-grub (2026-11-16)

After exiting Debian 13.7 rescue mode and successfully booting the working
Debian `7.2.15+deb14-amd64` kernel, the operator ran a **read-only**
`sudo grep` over the regenerated `/boot/grub/grub.cfg`. The five
reported Linux menu lines (regular, advanced and recovery options) target
`/@rootfs/boot/vmlinuz-7.2.15+deb14-amd64` or
`/@rootfs/boot/vmlinuz-7.2.12+deb14-amd64`, and each includes
`root=UUID=dddebb01-4f58-4782-82b3-0e77209afc8c` and
`rootflags=subvol=@rootfs`. Both installed Debian kernels therefore
retain the documented correct boot root and subvolume.

This **closes the post-update-grub root-parameter verification gate**,
not overall first-boot authorization. Both Debian kernels remain
installed, and no testing2 GRUB entry exists. Rescue USB boot and
all four Optane node discovery succeeded; independent MD RAID10
assembly/Btrfs root access in the rescue environment is **not yet
qualified**. NVIDIA proprietary R580 580.196.07 return-thunk
objtool warnings and controlled rollback/first-boot risk acceptance
remain open. No more GRUB or host bootloader modifications are needed.
