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

## Staged first test without proprietary NVIDIA modules (2026-11-16)

The proprietary R580 modules had `47,484` objtool
`naked return` warnings with `CONFIG_MITIGATION_RETHUNK=y`.
Although `.return_sites` and thunk-relocation metadata are
present, vendor binary returns remain unverified.

To reduce the initial test scope, a **third distinct offline
initramfs** can be built using
`scripts/kernel/huey-734-testing2-private-no-nvidia.sh`.
Its required boot modules are VMD/NVMe, md RAID10/1/0,
Btrfs and AMDGPU. It verifies **absence** of both
`nvidia*.ko` and `nouveau.ko` in the finished archive
and validates the same md0/md1/md2, md3-absent and
`RESUME=none` policies as the prior verified policy2 image.
Do **not** use the older policy2 image as an NVIDIA-free
test candidate; it still contains NVIDIA and UVM.

**A NVIDIA-free initrd is not by itself full isolation:**
the installed root filesystem could still contain driver
modules and udev rules. Linux supports the kernel parameter
`module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm`
to prevent the proprietary modules being loaded in the
future one-time test boot. Ensure this parameter is applied
**only** to an explicitly selected testing2 entry, never
the working Debian boot. No GRUB or modprobe settings are
to be changed until a separate installation and first-boot
rollback procedure is formally reviewed and approved.
Source: https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html

This image build workflow remains **offline and rootless**,
and its new image is neither built nor validated until
the operator runs it and sends results. The live Debian
environment is not modified. **First-boot remains NO-GO.**

## NVIDIA-free test initramfs: builder false positive and reuse-only postcheck

The third private no-NVIDIA initramfs **built and extracted**
successfully. Its final audit failed not due to an actual
proprietary NVIDIA module but because a name-match against
`modules.order` flagged unrelated in-tree Linux modules
`typec_nvidia.ko` and `nvidia-wmi-ec-backlight.ko`.
Kernel Kbuild's `modules.order` is an alias-resolution ordering
file, not a record of which actual module binaries have
been packed into the initramfs.

After the failure, use the new, rootless and read-only
`scripts/kernel/huey-734-testing2-no-nvidia-postcheck.sh`
to verify the **already-produced** image in
`work/no-nvidia-test1`. It reports a SHA-256 only if
the embedded private RAID/resume policy and the actual
archive module inventory pass checks. It must refuse to
overwrite an existing report. The builder has also been
fixed so future uses don't conflate the in-tree drivers
with proprietary NVIDIA R580 modules.

The new image must still be prepared for an explicitly
approved one-time boot with
`module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm`
to keep the proprietary code isolated even after the root
filesystem mounts. The absence of vendor files in initramfs
alone does not establish post-root isolation.

No build rerun, kernel installation, driver loading or
GRUB change should be performed to correct this metadata
false positive. First-boot status remains NO-GO.

## No-NVIDIA third archive validated; next gate is pre-install inventory (2026-11-16)

The previously built no-NVIDIA test1 archive has now **passed**
the separate read-only postcheck. SHA-256:
`fb2c4985f64c2a77f4cc2f175665311f179ac632d261a150ea7c58f673f4a3df`.
Verified: essential Intel VMD, NVMe, md RAID10/1/0,
Btrfs and AMDGPU modules and early hooks; zero proprietary
R580/Nouveau modules in the initramfs; active md0/md1/md2
UUID configuration and no md3; `RESUME=none`; root-owned
executable `/init`. Previous `modules.order`
NVIDIA-named in-tree module false positive is resolved.

The artifact remains in a private, **uninstalled** directory.
Preserve this file and digest. Do not rebuild it or overwrite
it in place. The standard policy2 image remains separately
pinned and is **not** the NVIDIA-isolated alternative.

Before authorizing first-boot packaging and one-time GRUB
entry, do read-only checks of:
1. Btrfs `/` free space (because `/boot` resides in
   `@rootfs`), EFI free space and mounts; note EFI has
   only one verified functioning Kingston FAT ESP.
2. Confirmation installed fallback Debian kernels
   `7.2.15+deb14-amd64` and
   `7.2.12+deb14-amd64` remain intact and that no
   testing2 kernel is installed.
3. Exact test-only GRUB kernel parameter
   `module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm`,
   plus `root=UUID=dddebb01-4f58-4782-82b3-0e77209afc8c`
   and `rootflags=subvol=@rootfs`. Avoid global
   `GRUB_CMDLINE_LINUX` changes or default boot switch.
4. Ability to select known-good Debian boot and rescue USB
   manually after a failure. Rescue USB has booted,
   though independent md0 assembly/Btrfs root recovery
   remains untested and must appear in the risk assessment.

No installation, host driver changes, GRUB writes, reboot or
CUDA testing is currently authorized. Next stage is
**pre-install review**, not a first-boot GO decision.

## Root and EFI pre-install space / mount verification (2026-11-16)

Operator ran `df -h / /boot/efi`, `findmnt /`,
`findmnt /boot/efi`, and `ls -lh /boot/vmlinuz-*
/boot/initrd.img-*` on working Debian
`7.2.15+deb14-amd64`:

- `/`: `/dev/md0`, Btrfs `@rootfs`,
  **27G size / 15G used / 12G available (55%)**;
  `rw,noatime,ssd,discard=async,space_cache=v2,subvolid=256,subvol=/@rootfs`.
- `/boot/efi`: currently `/dev/sdc1`, VFAT,
  **976M size / 9.7M used / 966M available (1%)**.
  Do not rely on the variable SATA device name; use
  persistent PARTUUID `58fae902-4199-444f-93b8-e845b62d8b95`
  when identifying the verified working ESP.
- `/boot` is **inside the Btrfs `@rootfs` subvolume**,
  not its own partition, and not on the EFI filesystem.
- Both Debian fallback kernel/initrd pairs remain present:
  `7.2.15+deb14-amd64` vmlinuz **14M**, initrd **310M**;
  `7.2.12+deb14-amd64` vmlinuz **14M**, initrd **314M**.

**Gate status:** mount consistency and reported free-space
inventory **PASS**; this is not yet confirmation of sufficient
unallocated Btrfs metadata/data chunks or total candidate
installation footprint. Check the actual private
`no-nvidia-test1` initrd size, Linux image .deb size and
read-only `btrfs filesystem usage` before planning a
controlled install.

The no-NVIDIA third archive remains pinned at SHA-256
`fb2c4985f64c2a77f4cc2f175665311f179ac632d261a150ea7c58f673f4a3df`.
It is uninstalled. Both fallback Debian kernels and EFI
must be preserved. No change to the default boot entry,
modprobe configuration, GRUB, system packages or RAID is
authorized by this space inspection. First boot stays
**NO-GO** pending controlled isolation/rollback review.

## Btrfs allocation and compressed artifact size gate — PASS (2026-11-17)

Read-only `btrfs filesystem usage -T /` confirms on
`/dev/md0` **26.81 GiB** total,
**17.52 GiB** allocated and **9.28 GiB**
unallocated, with **11.73 GiB** estimated free
(minimum estimate **7.09 GiB**), and no missing
Btrfs device. Root remains Btrfs `@rootfs`.
The kernel `.deb` package is **115 MiB
compressed**, and verified third no-NVIDIA
initramfs is **59 MiB**, SHA-256
`fb2c4985f64c2a77f4cc2f175665311f179ac632d261a150ea7c58f673f4a3df`.
These measurements indicate adequate planning headroom,
but cannot guarantee installation space without checking
the decompressed package footprint.

Uploaded historical image logs and listings confirm:
the original fakeroot image had stale md3 and
resume-from-md1; policy2 removed these but
included NVIDIA; the third no-NVIDIA image keeps
active RAID config and resume fix and removes
the only proprietary modules and firmware in the
policy2 archive. The third image also includes
`amdgpu/polaris10_*` firmware, required by the
RX 570 family. None has been runtime booted.

**Next required hold:** inspect Linux image `.deb`
control metadata, `Installed-Size`, maintainer
scripts and kernel hook invocation paths read-only,
because `dpkg -i` can alter `/boot`, GRUB,
initramfs and DKMS (including proprietary NVIDIA
builds). A controlled isolated first boot requires
not inadvertently invoking any of those hooks
or replacing the tested no-NVIDIA archive.
Do not install the package or change GRUB
before the full rollback plan is reviewed.

## Debian image package metadata / installed hook inventory (2026-11-17)

Operator inspected the pinned **uninstalled** candidate
`linux-image-7.3.4-huey-testing2_7.3.4-huey-testing2-1_amd64.deb`
read-only with `dpkg-deb -f`, `dpkg-deb --ctrl-tarfile |
tar -tf -`, and `ls -1` of installed kernel hook directories:

- `Package: linux-image-7.3.4-huey-testing2`
- `Version: 7.3.4-huey-testing2-1`
- `Installed-Size: 133515` KiB (~130.4 MiB, a package
  metadata estimate, not complete transient installation costs).
- The .deb contains control files `control`, `md5sums`,
  `preinst`, `postinst`, `prerm`, `postrm`.
- Live host `/etc/kernel/postinst.d/` has **dkms**,
  **initramfs-tools**, **unattended-upgrades**,
  **zz-update-grub**.
- Live host `/etc/kernel/postrm.d/` has
  **initramfs-tools**, **zz-update-grub**.

**Interpretation:** an ordinary `dpkg -i` is not an isolated,
no-NVIDIA test image staging method. Maintainer scripts and
post-install hooks **could** regenerate initramfs, update
GRUB, and trigger DKMS including proprietary NVIDIA
builds. Listing names is **not proof** of the exact execution
path or whether each hook would run; inspect the actual
package scripts, installed hook files, and any relevant
`/etc/kernel/preinst.d/` and `/etc/kernel/prerm.d/`
before finalizing install method.

**Next review should be read-only:** extract script content
with `dpkg-deb --ctrl-tarfile "$PKG" | tar -xOf - ./preinst`
and `./postinst`; inspect the local DKMS, initramfs and
GRUB hooks using `sed` or `cat`, but never invoke scripts.
Do not install, run `update-initramfs`, rebuild vendor
modules or regenerate GRUB.

Storage metrics from preceding audit show ~9.28 GiB
unallocated Btrfs blocks, ~11.73 GiB estimated free, and
59 MiB SHA-pinned NVIDIA-free test initrd. Kernel package
size 115 MiB compressed and metadata installed-size
~130.4 MiB: these are different measures. Both known-good
Debian image/initrd pairs are retained.

First-boot remains **NO-GO** until package side-effect
path, manual test boot entry, NVIDIA kernel-level
blacklist and rollback risks are documented and accepted.

## Actual package preinst/postinst and host postinstall hook review (2026-11-17)

The operator **read**, but did not execute, the `preinst`
and `postinst` scripts from the staged image `.deb`,
plus these exact installed hook files:
`/etc/kernel/postinst.d/{dkms,initramfs-tools,unattended-upgrades,zz-update-grub}`.

**Observed scripts and effects if a normal dpkg install/configure occurs:**

- Both package `preinst` and `postinst` export `INITRD=Yes`,
  set `DEB_MAINT_PARAMS="$*"`, then use `run-parts`
  to invoke any existing hook directories in **both**
  `/etc/kernel/{preinst,postinst}.d` and
  `/usr/share/kernel/{preinst,postinst}.d`, passing
  `7.3.4-huey-testing2` and
  `/boot/vmlinuz-7.3.4-huey-testing2`.
  Listing local postinst hooks alone is not the complete
  hook inventory; check `/usr/share/kernel` and preinst hooks too.
- `dkms` postinst hook invokes
  `/usr/lib/dkms/dkms_autoinstaller start "$inst_kern"`
  **if** the autoinstaller executable exists. This
  may rebuild any registered NVIDIA module; whether the
  current proprietary 580.196.07 install is registered
  with DKMS needs read-only `dkms status` inspection.
- `initramfs-tools` hook checks version and runs
  `update-initramfs -c -k "$version" -b "$bootdir"`
  for a `configure` invocation with `INITRD=Yes`.
  Therefore a normal kernel package install will create
  a **host-generated initramfs** for testing2 under
  `/boot`. It does *not* overwrite our separately pinned
  private 59 MiB image in the user's workspace; it
  **does create a different, unqualified image** that
  GRUB could point at, potentially including proprietary
  NVIDIA and old live resume/mdadm policy.
- `zz-update-grub` runs `update-grub` when the
  configure postinst phase applies, the bootloader
  config exists, and the system is not detected as
  a container. This regenerates host `grub.cfg`
  and can alter the default selected entry when
  `GRUB_DEFAULT=0`; do not assume that the old Debian
  kernel remains the automatic boot selection.
- `unattended-upgrades` hook only touches
  `/var/run/reboot-required` and appends the
  package to `reboot-required.pkgs` under its normal
  conditions; it **does not itself reboot**.

**Decision:** a direct `sudo dpkg -i
linux-image-7.3.4-huey-testing2_...amd64.deb`
is **NO-GO** for the proposed initial NVIDIA-free
boot qualification. Its maintainer/hook chain can
regenerate the initramfs, run DKMS and refresh the
bootloader, defeating controlled artifact identity
and one-time boot isolation.

**Approach for future design (not yet authorized):**
Prefer a *side-by-side*, auditable staging of the
verified kernel image, versioned modules and the exact
SHA-pinned no-NVIDIA initrd, plus a manually selectable
test-only GRUB entry with
`root=UUID=dddebb01-4f58-4782-82b3-0e77209afc8c`,
`rootflags=subvol=@rootfs` and
`module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm`.
This needs a tested dry-run/rollback and independent
versioned `/lib/modules` tree before any privileged
filesystem change. Manual staging avoids postinst
hooks but also bypasses package-manager ownership and
must have a clear cleanup/removal procedure. An
alternative managed install would need a proven,
non-disruptive hook policy and explicit approval;
do not mask host hooks ad hoc.

**Next minimal read-only gate:** inspect the active
DKMS registration and remaining `/etc/kernel/preinst.d`,
`/usr/share/kernel/postinst.d` hooks, and the package's
`prerm`/`postrm` for safe eventual removal. No
boot/install commands are authorized by this result.

## Additional kernel hook and DKMS command inventory (2026-11-17)

Operator ran read-only `command -v dkms` and `ls -la` for the
remaining kernel hook directories. The shell reported
`DKMS not installed` **only because `command -v dkms` was false**;
this does not independently rule out a binary outside PATH,
nor the specific executable `/usr/lib/dkms/dkms_autoinstaller`
used by the previously inspected postinst hook.

- `/etc/kernel/preinst.d/`: executable `dkms`
  (266 bytes, Sep 16 2025) and `intel-microcode`
  (529 bytes, Nov 22 2025).
- `/usr/share/kernel/preinst.d/`: absent.
- `/usr/share/kernel/postinst.d/`: executable
  `00-legacy-boot` (529 bytes, Aug 30 2026)
  and `touch-reboot-required` (414 bytes, Sep 1 2025).

**Review before deployment** the exact contents of those four
executable hooks, and verify actual DKMS auto-installer presence.
The observed package `preinst` and `postinst` both run these
directories through `run-parts`, so even when the usual
DKMS CLI is absent, the Intel microcode and legacy-boot hooks
may still run during a normal dpkg installation.

Avoid treating `00-legacy-boot` as harmless based on name.
Do not execute any hook during inspection. User-requested
NVIDIA-free first boot remains **NO-GO** for installation/reboot
until the effect of these hooks is understood and a
non-mutating manual staging/rollback plan is reviewed.

## Operator purged Debian 7.2.12 kernel image; only 7.2.15 remains bootable (2026-11-17)

**This supersedes prior text stating there are two installed Debian fallback kernels.**
The operator explicitly chose to purge the old 7.2.12 kernel and executed:
`sudo apt -s purge 'linux-image-7.2.12+deb14-amd64'`,
followed by `sudo apt purge 'linux-image-7.2.12+deb14-amd64'`
after a simulation that removed only that image package.

Observed effects:
- Image package `linux-image-7.2.12+deb14-amd64` (7.2.12-1)
  was purged; post-removal initramfs-tools deleted
  `/boot/initrd.img-7.2.12+deb14-amd64`.
- The live `/etc/kernel/prerm.d/dkms` hook **actually invoked DKMS**,
  removing proprietary `nvidia/580.196.07` modules
  `nvidia`, `nvidia-uvm`, `nvidia-modeset`, `nvidia-drm`,
  `nvidia-peermem` **for 7.2.12 only**, then `depmod`.
  This confirms some DKMS functionality exists despite the
  earlier `command -v dkms` check reporting unavailable. 
  Do not infer DKMS is entirely absent or that 7.2.15's
  NVIDIA driver has been disrupted. Reverify `nvidia-smi`
  on the current kernel after cleanup.
- The normal postrm hook ran `update-grub`, discovering
  only `/boot/vmlinuz-7.2.15+deb14-amd64`
  and its initrd, plus UEFI firmware settings.
- The operator confirmed `uname -r =
  7.2.15+deb14-amd64`, and `/boot` contains
  `vmlinuz-7.2.15+deb14-amd64` (14M)
  and `initrd.img-7.2.15+deb14-amd64` (310M).
  GRUB's `linux` lines all retain the correct
  `/@rootfs/boot/...` path, `root=UUID=
  dddebb01-4f58-4782-82b3-0e77209afc8c` and
  `rootflags=subvol=@rootfs`.
- `dpkg -l | grep '7.2.12'` still reports six **installed**
  packages:
  `linux-base-7.2.12+deb14-amd64`,
  `linux-binary-7.2.12+deb14-amd64`,
  `linux-headers-7.2.12+deb14-amd64`,
  `linux-headers-7.2.12+deb14-common`,
  `linux-kbuild-7.2.12+deb14`, and
  `linux-modules-7.2.12+deb14-amd64`.
  Those can be simulated for purge as a separate next step;
  no results of that simulation are available yet.

**Updated rollback status:** Debian `7.2.15` is the
**sole installed bootable fallback**. Independent recovery USB
boots and detects the four Optane partitions but has **not**
yet demonstrated md0 RAID10 assembly/Btrfs root mount.
This is a higher-risk state than the earlier two-fallback plan.
Do not automatically install or boot `7.3.4-huey-testing2`
or change the default GRUB entry. Preserve working
`7.2.15`; use only a reviewed, manually selected test
entry and explicit failure/recovery procedure in future.

## Debian 7.2.12 purge fully completed; V100 re-verified (2026-11-17 02:18 EST)

The operator performed a simulated purge of the six residual
7.2.12 packages, confirmed the proposed changes were limited
to exactly those six, and then approved/executed the purge:

- `linux-base-7.2.12+deb14-amd64`
- `linux-binary-7.2.12+deb14-amd64`
- `linux-headers-7.2.12+deb14-amd64`
- `linux-headers-7.2.12+deb14-common`
- `linux-kbuild-7.2.12+deb14`
- `linux-modules-7.2.12+deb14-amd64`

The purge reported **203 MB freed**. Read-only postchecks:

```text
dpkg -l | grep '7.2.12' || echo "No 7.2.12 packages remain"
No 7.2.12 packages remain
uname -r
7.2.15+deb14-amd64
nvidia-smi: 580.196.07, CUDA 13.0, Tesla V100-PCIE-32GB,
            46 C, 38 W, 0 MiB allocated; no processes
```

This completes the operator-authorized removal of **all**
7.2.12 packages. The 7.2.15 kernel and its initramfs remain
the **only known installed and working boot pair**. The
proprietary NVIDIA R580 driver is demonstrably intact on
7.2.15; prior DKMS removal was specific to 7.2.12.
Previous GRUB verification showed only correct 7.2.15
Btrfs `/@rootfs` entries after the image purge.

**Current first-boot risk status:** the independent Debian
13.7 rescue USB boots and sees all four Optane partitions,
but has **not** demonstrated assembly of the md0 RAID10
or read-only access to `@rootfs` from recovery. The one
working boot pair must not be removed or overwritten.
The SHA-pinned no-NVIDIA 7.3.4 testing2 initrd
`fb2c4985f64c2a77f4cc2f175665311f179ac632d261a150ea7c58f673f4a3df`
remains uninstalled, and there is no 7.3.4 GRUB entry.
No reboot or installation was performed as part of the
remaining-six-packages purge.

**Next engineering milestone:** prepare an auditable,
version-isolated, side-by-side manual boot staging and
rollback plan rather than running the candidate `.deb`
package's DKMS, initramfs-tools, and update-grub hooks.
Require a test-only kernel parameter
`module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm`,
known-good Debian default, and a clearly validated way to
reselect 7.2.15 in GRUB if testing2 fails. A recovery USB
root-array assembly test would reduce residual rollback risk.

## Operator authorized side-by-side installation preparation (2026-11-17)

The operator said **"Let's install"** after the successful
purge of Debian 7.2.12, confirmation of a healthy running
Debian 7.2.15, NVIDIA 580.196.07 and pinned third no-NVIDIA
initrd. A new guarded **manual test-staging shell artifact**
was authored in the chat container (not executed on the host):
`huey-734-testing2-stage-manual-boot.sh`.
SHA-256 of the authored shell script:
`24925c869545a04a92e0edd7afa5ece5737196aea129e21fae1dd22b800c771d`.
`bash -n` and static no-hook checks passed on that artifact;
host-specific execution and safety checks are **still untested**.

**Critical design decision:** the test kernel is intended to
reside under `/boot/huey-testing2/vmlinuz-7.3.4-huey-testing2`
with the pinned initrd in the same dedicated directory,
**not** a top-level `/boot/vmlinuz-*` file. Thus normal
GRUB `10_linux` kernel discovery should not promote the
unqualified 7.3.4 test image on a future host
`update-grub`. In-tree Linux modules would be copied to a
new `/usr/lib/modules/7.3.4-huey-testing2` directory and
`depmod` run for **that version only**.
The staged test is intentionally **unmanaged by dpkg**, so
its eventual cleanup is separate from `apt purge`.

**Strict prereqs:** running Debian
`7.2.15+deb14-amd64`, healthy
`/dev/md0` RAID10, Btrfs `@rootfs` UUID
`dddebb01-4f58-4782-82b3-0e77209afc8c`,
`GRUB_DEFAULT=0`, intact primary kernel/initrd,
and an already-generated GRUB `41_custom` dynamic
`custom.cfg` loader. Abort if any unique test path
is already present. Validate `grub-script-check`
before exposing the manual boot entry.

**Pinned install sources:**
- Kernel package SHA:
  `25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0`.
- Build `.config` SHA:
  `db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3`.
- Offline no-NVIDIA initrd SHA:
  `fb2c4985f64c2a77f4cc2f175665311f179ac632d261a150ea7c58f673f4a3df`.

The separate, manually selectable GRUB entry targets
`/@rootfs/boot/huey-testing2/` with the expected
root UUID/subvolume, and parameters:
`module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm,nvidia_peermem`
and `systemd.unit=multi-user.target`.
It uses GRUB's dynamic `custom.cfg` include and does
**not** call `update-grub`, `dpkg -i`,
`update-initramfs`, NVIDIA/DKMS hooks,
`grub-install`, or a reboot command.
Source docs: Debian GRUB `41_custom` and
https://wiki.archlinux.org/title/GRUB;
Linux kernel
https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html

**Status:** script authored and static-checked, **NOT
EXECUTED ON THE WORKSTATION**. On operator execution,
the script must print a post-stage report and stop.
Before first reboot, verify its staged paths, digest,
GRUB entry/default, and the status of Debian 7.2.15.
Recovery USB RAID assembly is still untested. If a
test boot fails or hangs, restart and select/default
to known-good 7.2.15; avoid trying to purge the
unmanaged 7.3.4 kernel using apt.
