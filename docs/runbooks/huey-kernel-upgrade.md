# HueyOS Kernel Upgrade Runbook

Human-operated procedure for installing a HueyOS custom kernel release,
booting it for the first time, running the qualification checks, and rolling
back if anything fails.

This runbook is the **only** sanctioned path for:

- installing a release built by `huey-kernel release`;
- promoting a new kernel as the target's default;
- enrolling a MOK certificate for Secure Boot signing;
- recovering from a failed first boot.

It is not automated. No build, CI, or script in the repository executes the
install, bootloader, MOK, or reboot operations described below.

**Read this entire document before starting.** If any of the preflight
checks in §2 fails, stop and resolve the failure before proceeding.

---

## 1. Scope and audience

- **Audience:** the project maintainer or an authorized operator who has
  physical access to (or IPMI/KVM-equivalent remote access to) the
  workstation.
- **Target:** the v100-workstation profile described in
  `kernel/huey-linux/README.md` (Intel i9-12900K, AMD RX 570 display, NVIDIA
  Tesla V100-PCIE-32GB compute, Debian Forky, proprietary NVIDIA 580.x).
- **Pre-built artifact:** a release directory produced by
  `huey-kernel release` and verified by `huey-kernel verify` with
  `boot_ready=True` and no ERROR/CRITICAL findings.

**This runbook does not cover:**
- building a release (see `scripts/kernel/build-kernel.sh`,
  `build-nvidia.sh`, `build-initramfs.sh`, `huey-kernel release`);
- multi-GPU or multi-node deployment (out of scope until the single-V100
  qualification completes);
- any operation on a workstation whose current kernel is not currently
  booted and working.

---

## 2. Preflight: physical access and baseline capture

### 2.1 Physical recovery access is REQUIRED

**Do not start this runbook until you have confirmed:**

1. **Physical presence at the workstation, or IPMI/KVM access**, for the
   first boot and every subsequent reboot until §10 completes.
2. **A known-good recovery medium** — the Debian installation USB that was
   used to install this workstation, or an equivalent, **in hand** and
   verified as bootable. If the new kernel fails to boot and the previous
   kernel entry is somehow unreachable, this medium is the last line of
   recovery.
3. **A working second keyboard** or a way to type at the console **even if
   the display stays blank**. This is common with kernel display-path
   failures; the console (e.g. serial, or the firmware's built-in console)
   must remain usable.

If any of these cannot be confirmed, **do not proceed**. There is no
"remote-only" path in this runbook for the first boot.

### 2.2 Baseline capture (read-only)

Before installing anything, capture the current state so that §12 and §13
have a reference point.

```bash
# Save the current boot state and hardware inventory.
sudo mkdir -p /root/huey-upgrade-baseline
uname -r                                                          | sudo tee /root/huey-upgrade-baseline/uname.txt
sudo nvidia-smi                                                   | sudo tee /root/huey-upgrade-baseline/nvidia-smi.txt
sudo dkms status                                                  | sudo tee /root/huey-upgrade-baseline/dkms-status.txt
sudo modinfo -F version nvidia                                    | sudo tee /root/huey-upgrade-baseline/nvidia-version.txt
sudo modinfo -F vermagic nvidia                                   | sudo tee /root/huey-upgrade-baseline/nvidia-vermagic.txt
mokutil --sb-state 2>/dev/null                                    | sudo tee /root/huey-upgrade-baseline/sb-state.txt
ls /boot                                                          | sudo tee /root/huey-upgrade-baseline/boot-listing.txt
sudo cp -a /etc/default/grub     /root/huey-upgrade-baseline/grub-default.txt
sudo cp -a /boot/grub/grub.cfg   /root/huey-upgrade-baseline/grub.cfg.before
sudo cp -a /etc/modprobe.d       /root/huey-upgrade-baseline/modprobe.d.before
sudo cp -a /etc/modules-load.d   /root/huey-upgrade-baseline/modules-load.d.before
```

Additional artifacts to preserve if you use Steam/Proton or an NVIDIA Vulkan
wrapper on this machine:

```bash
# Preserve the user's custom NVIDIA Vulkan wrapper and Steam launcher.
cp -a ~/.config/environment.d            ~/huey-upgrade-baseline-env.d 2>/dev/null || true
cp -a ~/.local/share/Steam/compatibilitytools.d ~/huey-upgrade-baseline-steam 2>/dev/null || true
cp -a ~/.config/steam-*                  ~/huey-upgrade-baseline-steam-config 2>/dev/null || true
# Custom ICD manifests (do not switch system-wide ICDs during this upgrade).
sudo cp -a /usr/share/vulkan/icd.d        /root/huey-upgrade-baseline/vulkan-icd.d.before 2>/dev/null || true
ls ~/.local/share/vulkan/icd.d            > /root/huey-upgrade-baseline/vulkan-user-icd.txt 2>/dev/null || true
```

### 2.3 Record the thermal baseline (see §11)

```bash
nvidia-smi --query-gpu=temperature.gpu,utilization.gpu --format=csv \
  | sudo tee /root/huey-upgrade-baseline/thermal-baseline.txt
```

A prior snapshot recorded **86 °C at 0 % utilization**. If the baseline
still shows idle temperatures above **80 °C**, **stop and resolve cooling
before proceeding**. See §11 for abort thresholds.

---

## 3. Acquire and inspect the release

Copy the verified release directory to the workstation and confirm its
integrity **before** installing anything.

```bash
RELEASE_DIR=/path/to/release/7.2.15-huey1   # from huey-kernel release
cd "$RELEASE_DIR"

# Confirm the manifest and checksums are intact.
sha256sum -c SHA256SUMS
cat MANIFEST.json | python3 -m json.tool | less
```

Confirm in `MANIFEST.json`:

- `"boot_ready": true`
- `"static_checks_passed": true`
- `"checks_summary.errors": 0`
- `"checks_summary.critical": 0`
- `"distribution_restricted"` reflects what you expect (proprietary modules
  present → `true`)
- `"source_lock.status": "pinned"`

If any of these is not what you expect, **stop** and re-run
`huey-kernel verify --release-dir "$RELEASE_DIR"` and diagnose.

---

## 4. Secure Boot: MOK enrollment precheck

If `mokutil --sb-state` reports `SecureBoot enabled`:

1. Confirm the release was signed (the manifest's artifact list contains
   signed modules; `huey-kernel verify` would have flagged unsigned modules).
2. Confirm the signing certificate (`MOK.der`) is present in the release
   under the path described in `kernel/huey-linux/signing-policy.md`.
3. Follow `kernel/huey-linux/signing-policy.md` §4.1 to enroll the MOK
   **before** the first boot of the custom kernel:
   ```
   mokutil --import <MOK.der>
   ```
4. **Do not reboot yet.** Return here after enrollment is queued.

If `mokutil --sb-state` reports `SecureBoot disabled`:

- The signed modules will still load (signature checking is relaxed on
  many kernels with `CONFIG_MODULE_SIG_FORCE=n`), but follow the signing
  policy anyway. Do not skip signing because Secure Boot is off; it may be
  turned on later by firmware updates or by another administrator.

If `mokutil --sb-state` reports **anything else, or is missing**:

- **Stop.** The Secure Boot state is unknown; the release cannot be
  promoted safely. Install `mokutil`, or resolve the EFI-variable
  availability issue, and re-run the baseline capture.

---

## 5. Package installation order

The `.deb` packages must be installed in the correct order. Both installs
invoke maintainer scripts that mutate `/boot`, `/etc/initramfs-tools`, and
GRUB configuration. **The `linux-image` package's post-install script runs
`update-initramfs` and `update-grub`**, and the `linux-headers` package
triggers DKMS to build any registered out-of-tree modules for the new
kernel.

That is exactly why this runbook exists, and why no build or CI script runs
these commands.

### 5.1 Install order

```bash
RELEASE_DIR=/path/to/release/7.2.15-huey1
KR=7.2.15-huey1

# 1. Kernel headers first, so DKMS can build against the new kernel.
sudo dpkg -i "$RELEASE_DIR/linux-headers-${KR}"_*.deb

# 2. Kernel image. This runs update-initramfs and update-grub.
sudo dpkg -i "$RELEASE_DIR/linux-image-${KR}"_*.deb
```

**Do not run `dpkg -i` on both in a single invocation.** The post-install
scripts run in unpredictable order, and the headers-first order is the one
that leaves a working DKMS build if the operator aborts after step 1 (the
existing kernel is still booted and untouched).

### 5.2 Forbidden commands during this runbook

Never run the following until §16 is reached and §15 has passed:

- `sudo apt autoremove`
- `sudo apt purge <any kernel or headers>`
- `sudo apt remove <any kernel or headers>`
- `sudo update-grub` with a changed default entry
- `sudo grub-install` with a changed target
- `sudo dkms install` for any driver not part of this upgrade
- `sudo mokutil --delete` for any enrolled key (except as documented in the
  signing policy's rotation procedure, and only after a working replacement
  is enrolled)

Any of the above can remove or hide the currently-working kernel, which is
your only rollback path.

---

## 6. Confirm the DKMS build against the new kernel

DKMS is triggered by the `linux-headers` package. Confirm it built against
the new kernel:

```bash
KR=7.2.15-huey1

# Must list the new kernel release, e.g.:
#   nvidia/580.196.07, 7.2.15-huey1, x86_64: installed
sudo dkms status | grep "nvidia"

# Verify the built modules match the new release.
sudo modinfo -k "$KR" -F vermagic nvidia
sudo modinfo -k "$KR" -F version  nvidia
```

The first line's `vermagic` **must** contain `"$KR"`. If it does not, do not
continue. Diagnose:

```bash
# Show the DKMS build log for the new kernel.
sudo dkms status
sudo ls /var/lib/dkms/nvidia/*/build
sudo cat /var/lib/dkms/nvidia/*/"$KR"/x86_64/log/make.log 2>/dev/null | tail -200
```

The most common failure here is that the kernel image installed **without**
its matching headers. If headers are missing, install them (see §5.1) and
re-run `dkms build` / `dkms install` **for the new kernel only**:

```bash
sudo dkms install -k "$KR" nvidia/580.196.07
```

---

## 7. Inspect the target initramfs before first boot

The custom kernel's initramfs was produced by `huey-kernel initramfs`
(Step 17). If the release did not include a prebuilt initramfs, the
`linux-image` post-install script produced a default one — **but that
default is not the one the profile specifies**. Either way, inspect what
ended up in `/boot`:

```bash
KR=7.2.15-huey1
lsinitramfs "/boot/initrd.img-${KR}" | grep -E "nvidia|amdgpu" \
  | sudo tee /root/huey-upgrade-baseline/initramfs-${KR}.listing

# Must show nvidia.ko and nvidia-uvm.ko (some suffix of .ko.zst/.ko.gz is fine).
# Must show at least one amdgpu entry.
# Must NOT show nouveau.ko.
```

If `nouveau.ko` appears, **stop** and re-run
`huey-kernel verify --release-dir "$RELEASE_DIR"` on the release you
installed. The release is not boot-ready for the V100 profile.

If the initramfs does not contain the NVIDIA modules, the
`CONFIG_DRM_NOUVEAU` and `nvidia` profile policies are not being applied to
this boot. Do not promote the kernel until §7 passes.

---

## 8. GRUB entry preservation and one-time boot

The `linux-image` post-install script adds a GRUB menu entry for the new
kernel and **does not change the default**. Confirm this:

```bash
# Show the GRUB default entry before and after install.
diff /root/huey-upgrade-baseline/grub-default.txt /etc/default/grub
diff /root/huey-upgrade-baseline/grub.cfg.before /boot/grub/grub.cfg | head -100
```

- `GRUB_DEFAULT` in `/etc/default/grub` **must not change**. If the install
  modified it, restore it from `grub-default.txt` (do not blindly
  `update-grub`; see §9.3).
- The new kernel entry must appear in `grub.cfg`. The old kernel entry must
  also remain. If the old entry is missing, restore it from
  `grub.cfg.before` before proceeding.

### 8.1 One-time boot selection — use GRUB's menu, not `grub-reboot`

Preferred: **select the new kernel from the GRUB menu manually** at next
boot. This leaves no persistent state and cannot be misinterpreted by a
future boot.

If the workstation is in a remote location but you have IPMI/KVM, use the
**virtual console** to press `e` or arrows at the GRUB screen.

`grub-reboot` is **not** used by this runbook because:

- it requires the exact menu entry name, which varies by distro and may
  change on any `update-grub`;
- it relies on the GRUB environment file (`grubenv`) staying writable and
  unmodified, which is not guaranteed after a kernel install;
- a manual menu selection is the clearest recovery signal if something
  goes wrong, because the operator is directly interacting with the
  bootloader.

### 8.2 Note the rollback entry

Record the exact title of the current (working) kernel entry:

```bash
grep -E "^menuentry|^\s+menuentry" /boot/grub/grub.cfg \
  | grep -i "Debian GNU/Linux" \
  | sudo tee /root/huey-upgrade-baseline/grub-menu-titles.txt
```

If the new kernel fails to boot, you will select one of these titles in
§12.

### 8.3 If you must regenerate grub.cfg

Only if the diff in §8 shows the old entry was *removed*, regenerate it:

```bash
# Verify what will change BEFORE regenerating.
sudo cp /boot/grub/grub.cfg /root/huey-upgrade-baseline/grub.cfg.pre-regen
sudo grub-mkconfig -o /tmp/grub.cfg.new
diff /boot/grub/grub.cfg /tmp/grub.cfg.new | less

# If satisfied, replace.
sudo cp /tmp/grub.cfg.new /boot/grub/grub.cfg
```

Do **not** run `update-grub` as a reflex. Confirm what changes first.

---

## 9. First boot

Reboot when §8 is complete.

```bash
sudo reboot
```

At the GRUB menu:

1. Use the arrow keys to **select the custom kernel entry** (`7.2.15-huey1`
   or similar).
2. Do **not** press Enter twice in a row. Press Enter once and wait.
3. If the screen goes blank and stays blank for more than **60 seconds**
   after GRUB hands off, do not wait longer — proceed to §12 (rollback).

The firmware will not be modified by this boot. The next normal boot
(without operator selection at the GRUB menu) will return to the default
entry (the previous working kernel), because §8 verified the default entry
was not changed. This is the "one-time" guarantee: no persistent boot
state changes.

---

## 10. Post-boot qualification

After the custom kernel boots, run these checks **in order**. Stop at the
first failure and go to §13.

### 10.1 Kernel and storage

```bash
uname -r
# Must be the release that was installed, e.g. 7.2.15-huey1.

sudo dmesg | grep -E "Kernel command line|Kernel panic|Call Trace"
# Should not show a panic or call trace from the boot path.

df -hT /
# Root filesystem must be mounted with the expected filesystem type.
```

### 10.2 Display path (AMD RX 570)

```bash
lspci -nnk | grep -A3 -E "VGA|3D"
# amdgpu must be the in-use kernel driver for the RX 570.

lsmod | grep amdgpu
# Must be loaded.

gnome-shell --version 2>/dev/null || echo "GNOME not running on this TTY"
```

If you are at the physical console, confirm that the GNOME / Wayland session
started normally.

### 10.3 Compute path (Tesla V100)

```bash
lsmod | grep -E "^nvidia"
# nvidia and nvidia-uvm must be loaded.

nvidia-smi
# Must list the Tesla V100-PCIE-32GB and the driver version (580.196.07).

nvidia-smi --query-gpu=name,pci.bus_id,uuid,compute_cap,driver_version \
  --format=csv
# pci.bus_id and uuid must match the V100 the workspace was built for.
# compute_cap must be 7.0.

# Confirm the toolkit is what the release was verified against.
nvcc --version 2>/dev/null || echo "no toolkit on PATH"
# Compare to MANIFEST.json's recorded CUDA toolkit version (not the CUDA
# API the driver advertises via nvidia-smi).
```

**Do not confuse `nvidia-smi`'s "CUDA Version" line with the installed
toolkit.** `nvidia-smi` reports the *driver-advertised CUDA API version*;
`nvcc --version` reports the *installed toolkit*. The manifest records both
separately. The policy doc (`signing-policy.md`) and the verifier
(`verifier.py`) enforce this distinction.

### 10.4 Framework smoke tests (opt-in, GPU-loading)

Only now, and only if the workstation is physically attended and the
thermal baseline from §2.3 was acceptable:

```bash
./scripts/kernel/test-hardware.sh --gpu-smoke --yes
```

This runs a small CUDA probe, an `ollama ps` check, and a ComfyUI process
check. It may raise the V100 temperature. **Abort if the temperature
crosses §11's threshold** and go to §12.

### 10.5 Custom Steam/Proton Vulkan wrapper

```bash
# Confirm the user's custom NVIDIA Vulkan ICD wrapper still resolves.
ls -la ~/.local/share/vulkan/icd.d/ 2>/dev/null
cat  ~/.local/share/vulkan/icd.d/*.json 2>/dev/null | head -40

# Confirm the Steam compatibility tool and environment are unchanged.
ls -la ~/.local/share/Steam/compatibilitytools.d/ 2>/dev/null
```

If any of the user's custom wrapper files are missing or overridden,
restore them from `~/huey-upgrade-baseline-steam*` and
`~/huey-upgrade-baseline-env.d`. **Do not replace the system-wide Vulkan
ICD** to make Steam work; the custom wrapper is the supported path.

---

## 11. Thermal abort thresholds

The runbook pauses at any of these conditions, and the operator must
investigate cooling **before** re-running any GPU stress test:

| Condition | Action |
|---|---|
| V100 idle (0 % utilization) **> 80 °C** | Stop. Investigate airflow, fan curve, ambient temperature. Do not proceed. |
| V100 under a single CUDA smoke probe **> 85 °C** | Stop the probe. Investigate. Do not proceed to multi-workload tests. |
| Sustained (≥ 60 s) **> 85 °C** at any utilization | Abort. Investigate cooling. Do not proceed. |
| Thermal throttling indicated by `nvidia-smi -q -d PERFORMANCE` | Stop. The GPU is throttling and the environment is not ready for qualification. |

A prior `nvidia-smi` snapshot on this host reported **86 °C at 0 %
utilization**. That is the exact signal these thresholds are designed to
catch. Do not treat a successful driver probe as a thermal qualification.

Record the observed temperatures alongside the qualification results:

```bash
nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,clocks_throttle_reasons.active \
  --format=csv | sudo tee -a /root/huey-upgrade-baseline/thermal-after.txt
```

---

## 12. Rollback: return to the previous kernel

If anything in §10 or §11 fails, or the first boot does not reach a working
login prompt within a reasonable time:

### 12.1 Reboot and select the previous kernel

1. Reboot the workstation.
2. At the GRUB menu, use the arrow keys to select the **previous working
   Debian kernel** (the one recorded in `grub-menu-titles.txt`).
3. Boot it. The default GRUB entry should also be that kernel (see §8.3),
   so even a normal reboot without manual selection returns to it.
4. Verify you are back:
   ```bash
   uname -r
   # Must NOT be the new custom release.
   sudo dkms status
   # Must show nvidia built for the running kernel as installed.
   nvidia-smi
   # Must list the V100.
   ```

### 12.2 If the previous kernel also fails to boot

This should not happen: the previous kernel was working before §9, and no
step in this runbook modified its image, its initramfs, or its matching
NVIDIA module. But if it does:

1. Boot the **recovery medium** from §2.1.
2. Chroot into the root filesystem.
3. Restore `/boot/grub/grub.cfg` from
   `/root/huey-upgrade-baseline/grub.cfg.before`.
4. Reinstall the previous kernel and its headers from the local package
   cache (`/var/cache/apt/archives`), or from the recovery medium.
5. Rebuild the initramfs for the previous kernel:
   `update-initramfs -u -k <previous-release>`.
6. Re-run `grub-mkconfig -o /boot/grub/grub.cfg` **only after** diffing
   against `grub.cfg.before`.

### 12.3 Un-install only the new kernel (do not touch the old)

Once back on the working kernel:

```bash
KR=7.2.15-huey1

# Remove ONLY the new kernel and headers.
sudo apt remove "linux-image-${KR}" "linux-headers-${KR}"

# Do NOT run apt autoremove or apt purge here.
# Do NOT remove /lib/modules/$(uname -r) or its /boot files.
```

If `apt remove` proposes to remove the currently-running kernel or its
headers, **abort** with `Ctrl-C` and inspect what is being pulled in.

---

## 13. Failed DKMS recovery

If §6 fails (DKMS did not build for the new kernel) but the workstation is
still running the previous kernel and is otherwise healthy, the new kernel
is not boot-ready. Recovery paths:

### 13.1 Fix the DKMS build against the new kernel

1. Confirm the headers package for the new kernel is installed:
   ```bash
   dpkg -l "linux-headers-<new-kernel-release>" | grep ^ii
   ```
2. If missing, install it (see §5.1).
3. Retry the DKMS build for the **new kernel only**:
   ```bash
   sudo dkms install -k "<new-kernel-release>" nvidia/<version>
   ```
4. If the build still fails, capture the log:
   ```bash
   sudo cat /var/lib/dkms/nvidia/<version>/<new-kernel-release>/x86_64/log/make.log
   ```
   Provide this log when filing an issue against the release. Do not patch
   the vendor source in place.

### 13.2 Abandon the new kernel for this attempt

If the DKMS build cannot be completed, the new kernel will not load the
proprietary NVIDIA modules. Abandon the new kernel:

1. Do **not** promote the new kernel.
2. Reinstall the release's previous build or wait for a new release.
3. The workstation continues to boot the previous kernel; the new kernel's
   files in `/boot` and `/lib/modules` are inert but present. They can be
   removed by §12.3 once it is confirmed the workstation does not need
   them.

---

## 14. Independent recovery of display and compute

Recovery of the AMD display path and the NVIDIA compute path are **separate
operations**. Do not "fix" both at once.

### 14.1 If only the display is broken (RX 570 not showing)

- The workstation is up on the custom kernel, `amdgpu` is loaded, but the
  display path fails (blank screen, firmware missing, etc.).
- This is an **amdgpu** problem. Do not touch NVIDIA modules.
- Recovery:
  ```bash
  # Confirm the firmware for the RX 570 is present.
  ls /lib/firmware/amdgpu/polaris10_*_fw.bin
  # If missing, install or reinstall the linux-firmware package.
  ```
- If the display path still fails, boot the previous kernel (§12.1) and
  open an issue against the custom kernel's AMDGPU configuration (Step 10's
  `v100-workstation.config` or the Debian base config).

### 14.2 If only the compute path is broken (V100 not usable)

- The workstation boots and displays normally, but `nvidia-smi` fails, or
  `nvidia` is not loaded, or CUDA workloads error.
- This is an **nvidia** problem. Do not touch amdgpu, do not blacklist any
  display driver.
- Recovery:
  ```bash
  sudo dmesg | grep -iE "nvidia|nvrm|nv-" | tail -200
  sudo modinfo -F vermagic nvidia
  # Compare to uname -r.
  ```
- If `vermagic` does not match, go to §6 and §13 (DKMS).
- If `vermagic` matches but the module fails to load, capture the dmesg
  output and re-run `huey-kernel verify --release-dir "$RELEASE_DIR"`.

### 14.3 If both are broken

Boot the previous kernel (§12.1). Do not try to fix both on the new kernel
in a single attempt; the failure modes will overlap and make diagnosis
harder.

---

## 15. Preservation of the Steam/Proton Vulkan wrapper

The workstation has a user-specific NVIDIA Vulkan wrapper for opt-in use by
Steam/Proton. **It is not modified by the kernel upgrade.**

- Confirm the user's wrapper files are intact:
  ```bash
  ls -la ~/.local/share/vulkan/icd.d/
  ls -la ~/.local/share/Steam/compatibilitytools.d/
  ```
- Compare against `~/huey-upgrade-baseline-steam*` captured in §2.2.
- If files are missing or changed, restore them from the baseline copies.
- **Do not replace the system-wide Vulkan ICD** (`/usr/share/vulkan/icd.d/`)
  to make Steam work. The custom wrapper is the supported path; changing
  the system ICD affects every application, not just the opt-in wrapper.

If the wrapper appears broken on the new kernel, the safest path is §12.1:
boot the previous kernel, confirm the wrapper works there, then investigate
the new kernel without affecting the working state.

---

## 16. Promotion to default and cleanup (only after §10–§15 pass)

Only after **all** post-boot checks in §10 pass, and the thermal abort
thresholds in §11 were not crossed, and the display and compute paths in
§14 and Steam/Proton in §15 are intact:

### 16.1 Record the qualification result

```bash
mkdir -p /root/huey-qualification
{
  uname -r
  nvidia-smi
  sudo dkms status
  nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,clocks_throttle_reasons.active --format=csv
} | sudo tee /root/huey-qualification/result-$(date +%Y-%m-%d).txt
```

### 16.2 Promote the new kernel as the default (optional)

Promotion is **optional**. The system is fully functional with the previous
kernel as default and the new kernel available for manual selection at
GRUB. If you want the new kernel to be the default:

```bash
sudo cp /root/huey-upgrade-baseline/grub-default.txt /root/huey-upgrade-baseline/grub-default.txt.keep-for-rollback
sudoedit /etc/default/grub
# Change GRUB_DEFAULT to the new kernel's menu entry title (exact string).
sudo cp /boot/grub/grub.cfg /root/huey-qualification/grub.cfg.before-promotion
sudo grub-mkconfig -o /tmp/grub.cfg.promoted
diff /boot/grub/grub.cfg /tmp/grub.cfg.promoted | less
sudo cp /tmp/grub.cfg.promoted /boot/grub/grub.cfg
```

If anything goes wrong after this point, the previous kernel and its GRUB
entry are still present. `apt autoremove` and `apt purge` are still
forbidden.

### 16.3 Cleanup — forbidden commands

Never run, at any point in this runbook:

- `sudo apt autoremove`
- `sudo apt purge linux-*`
- `sudo apt remove linux-image-*` (any kernel other than the new one, and
  only after §10–§15 passed)

The previous working kernel is kept indefinitely as a rollback path. Its
cost is disk space; its value is a working workstation.

---

## 17. What this runbook intentionally does not do

- It does not disable Secure Boot.
- It does not modify the default GRUB entry unless §16.2 is explicitly
  performed.
- It does not remove the previous kernel.
- It does not switch the system-wide Vulkan ICD.
- It does not install any NVIDIA driver other than what the release
  contains.
- It does not run `nvidia-installer` or any vendor `.run` archive.
- It does not run `update-grub` without diffing the result first.
- It does not use `grub-reboot`; it uses the GRUB menu directly.

Every one of these is a deliberate safety commitment. If a future change
needs to relax one of them, that change belongs in a separately reviewed
document, not in an edit to this runbook.

---

## 18. References

- `kernel/huey-linux/README.md` — architecture and safe defaults.
- `kernel/huey-linux/signing-policy.md` — MOK enrollment and Secure Boot.
- `docs/hardware/tesla-v100-nvidia-driver-baseline.md` — observed driver
  baseline.
- Handoff `HueyOS_Custom_Kernel_Agent_Handoff.md` §Phase C and the
  post-step qualification milestones.
