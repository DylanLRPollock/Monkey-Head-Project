# HueyOS Custom Kernel Builder

This directory is the entry point for the **HueyOS custom Linux kernel build and
release framework** for the `DylanLRPollock/Monkey-Head-Project` repository.

The framework produces a **version-matched kernel/driver bundle** for a
Debian-compatible kernel that supports the project's workstation hardware:

- AMD RX 570 as the **display** GPU (must remain untouched)
- NVIDIA Tesla V100-PCIE-32GB (`sm_70`, Volta) as the **compute** GPU
- Proprietary NVIDIA driver **580.196.07** (R580 branch)

It is **not** a replacement for the running Debian installation. It is a
reproducible, auditable toolkit that produces separately verifiable artifacts.

---

## 1. What is built, and what is not

| Artifact | How it is produced | Linked into `vmlinux`? |
|---|---|---|
| Custom Linux kernel image (`.deb`) | `make -j4 bindeb-pkg` on pinned Debian source | n/a |
| Matching kernel headers (`.deb`) | Same build | n/a |
| In-tree drivers (`amdgpu`, NVMe, PCIe, ext4, USB, etc.) | Kernel config (`=y` or `=m`) | Yes if `=y`, otherwise loadable `.ko` |
| NVIDIA proprietary R580 modules (`nvidia`, `nvidia-uvm`, `nvidia-modeset`, `nvidia-drm` as appropriate) | Built **out-of-tree** for the **exact** `KERNELRELEASE` | **No** — separate `.ko` files |
| Target-version initramfs | Debian `initramfs-tools` in staging | n/a |
| Verification manifest (SHA-256, provenance, approval state) | `release.py` | n/a |

### Key distinction: kernel vs. module

- **In-tree drivers** may be configured `=y` (built into the kernel image) or `=m`
  (loadable modules). The AMDGPU display path, storage controllers, PCIe, USB,
  and filesystems are handled this way.
- **The NVIDIA proprietary driver cannot be linked into `vmlinux`.** It is a
  vendor out-of-tree module. The V100 requires the **proprietary** NVIDIA module
  flavor; the newer open GPU kernel modules are limited to Turing and later
  architectures and are **not compatible with Volta `sm_70`**.
- **`baked in` for the NVIDIA driver means:** the `.ko` files are built for the
  exact target `KERNELRELEASE` and included in the **initramfs**, not merged
  into the kernel binary.

---

## 2. Safe defaults and dry-run behavior

All commands **default to non-destructive** behavior on the running host.

| Command | Host writes | Default |
|---|---|---|
| `inventory` | none (read-only) | safe |
| `doctor` | none (read-only) | safe |
| `plan` | none | safe |
| `config` | `build/huey-kernel/...` only | safe (supports `--dry-run`) |
| `build-kernel` | `build/huey-kernel/...` only | safe (supports `--dry-run`) |
| `build-nvidia` | `build/huey-kernel/...` only | safe (supports `--dry-run`) |
| `initramfs` | `build/huey-kernel/...` only | safe (supports `--dry-run`) |
| `sign` | `build/huey-kernel/...` only | safe (supports `--dry-run`) |
| `verify` | none | safe |
| `release` | `build/huey-kernel/release/...` only | safe (supports `--dry-run`) |

There is **no** `install` or `reboot` subcommand. Installation and first boot
are handled by a separate, human-approved runbook
(`docs/runbooks/huey-kernel-upgrade.md`).

### Non-negotiable safe defaults

1. **No root compilation.** The kernel is built by a normal build user in an
   isolated workspace.
2. **No automatic host mutation.** Nothing writes to `/boot`, `/lib/modules`,
   `/etc`, apt sources, DKMS, systemd, MOK, or GRUB without an explicit,
   separate operator-approved step.
3. **No `shell=True` or `eval`** on untrusted text. Argv arrays, timeouts,
   controlled environments, and return-code checks only.
4. **No root-owned build artifacts in source.** Build output lives under
   `build/huey-kernel/` (gitignored).
5. **No fabricated success.** A dry run is not a build. An installed DKMS
   record is not proof that GPU compute works. A booting kernel is not proof
   that Vulkan/Steam works.
6. **Do not disable Secure Boot to make builds pass.** Discover its state,
   document signing, and require human MOK enrollment.
7. **No public redistribution of vendor binaries.** Public repository contains
   code, config, and documentation only.
8. **CPU/host protection.** Build concurrency starts at `-j4` for the current
   16 GiB RAM workstation; timeouts, disk usage, and log sizes are bounded.
9. **Fail closed.** Unknown kernel release, missing headers, ambiguous NVIDIA
   source, missing GPU identity, or invalid artifacts block promotion.
10. **Reproducibility.** Source package identity and SHA-256 are pinned;
    compiler, tool versions, config delta, and output hashes are recorded.

---

## 3. Host vs. target separation

| Concept | Meaning |
|---|---|
| **Host** | The current Debian Forky workstation running the build. Used for read-only inspection and as a build machine. |
| **Target** | The new kernel release (`KERNELRELEASE`) with its matching headers, modules, and initramfs. |
| **Live host** | The currently booted kernel and its loaded NVIDIA modules. Never modified by build, config, or verify steps. |

Secure Boot state, MOK keys, and bootloader entries are inspected read-only
and addressed only in the separate, human-approved install phase.

---

## 4. Prerequisites

**Repository environment**
- Python **3.13**
- Existing repo tooling: `pytest`, `ruff`, `mypy` as configured in the root
  `pyproject.toml`

**Debian kernel build host**
```
build-essential bc bison flex libssl-dev libelf-dev
libncurses-dev dwarves fakeroot linux-source
dpkg-dev kmod initramfs-tools
```
These are **not** installed automatically. `doctor` reports which are missing
and refuses to proceed if a required tool is absent.

**NVIDIA 580.196.07 proprietary source**
- Must be obtained through an authorized, license-compliant method
  (existing local DKMS source tree or a vendor archive retrieved by the
  operator).
- The framework never downloads or executes the vendor installer against the
  live OS.

---

## 5. Expected artifacts

A successful build produces, under `build/huey-kernel/release/<KERNELRELEASE>/`:

1. `linux-image-<KERNELRELEASE>_*.deb`
2. `linux-headers-<KERNELRELEASE>_*.deb`
3. A staged NVIDIA proprietary module package (or a reproducible build
   reference) for the **exact** kernel release.
4. The target-version `initramfs`, or an explicit `not boot-ready` status if
   generation was skipped or failed.
5. `MANIFEST.json` with SHA-256 hashes, source lock reference, tool versions,
   config delta summary, signing status, and human approval state.

A release is **not** marked `ready` until the human-approved hardware
qualification runbook has been completed.

---

## 6. Exact commands (dry-run first)

After installing HueyOS, invoke the builder through the main CLI as
`huey kernel <subcommand>`. The standalone `huey-kernel <subcommand>`
entry point is also available for scripts and focused workflows.

All example commands are run from the repository root.

```bash
# 1. Read-only baseline of the host
huey kernel inventory --json
huey kernel doctor --json

# 2. Build plan (no host mutation)
huey kernel plan \
  --config kernel/huey-linux/build.yaml --json

# 3. Generate the effective kernel .config into the build output (dry-run first)
huey kernel config \
  --config kernel/huey-linux/build.yaml \
  --output-dir build/huey-kernel/config --dry-run

# 4. Build subcommands (each supports --dry-run)
huey kernel build-kernel  --config kernel/huey-linux/build.yaml --dry-run
huey kernel build-nvidia  --config kernel/huey-linux/build.yaml --dry-run
huey kernel initramfs     --config kernel/huey-linux/build.yaml --dry-run
huey kernel sign          --config kernel/huey-linux/build.yaml --dry-run

# 5. Offline verification of a release directory
huey kernel verify \
  --release-dir build/huey-kernel/release/<KERNELRELEASE> --json

# 6. Assemble the release manifest
huey kernel release \
  --config kernel/huey-linux/build.yaml --dry-run
```

Shell wrappers in `scripts/kernel/` are **thin** (`exec python -m
huey.kernel_build.cli <subcommand> "$@"`). They contain no independent logic.

---

## 7. What is intentionally **never** automated

The following operations are excluded from all build, config, and verify
subcommands. They belong to the separate, human-approved install runbook:

- `dpkg -i` against the live host
- `dkms install` against the running kernel
- `update-initramfs -u` writing to live `/boot`
- `update-grub` or any bootloader entry change
- MOK key enrollment
- `apt autoremove` or kernel purging
- Reboot or shutdown
- Publishing proprietary vendor binaries to public GitHub releases
- Any change to the AMD RX 570 display configuration, CUDA install, Ollama,
  ComfyUI, or the Steam/Proton Vulkan wrapper

---

## 8. Secure Boot

- `mokutil --sb-state` is queried **read-only** in `inventory` and `doctor`.
- When Secure Boot is enabled, staged NVIDIA modules (and the kernel EFI image,
  if the boot chain requires it) must be signed with a trusted local key.
- Signing keys live **outside** the repository, are owned by the operator, and
  are never logged.
- MOK public-key enrollment is documented in
  `kernel/huey-linux/signing-policy.md` but is **never** performed by a build
  subcommand.
- If Secure Boot is enabled and signing trust is not established, the release
  is marked `not boot-ready`.

---

## 9. GRUB rollback

The existing working Debian kernel and its matching NVIDIA module are
**preserved at all times**.

- Build and release steps never modify `/boot`, GRUB configuration, or the
  default boot entry.
- First test boot uses a **one-time boot selection** so the working kernel
  remains the fallback.
- Recovery via the previous kernel, DKMS rollback, AMD display recovery, and
  NVIDIA compute recovery are documented in
  `docs/runbooks/huey-kernel-upgrade.md`.
- Physical or console recovery access is required before the first test boot.

---

## 10. Licensing and redistribution

| Content | Public repo | Private/local build |
|---|---|---|
| Python framework code | ✅ allowed | ✅ |
| Kernel config fragments and documentation | ✅ allowed | ✅ |
| Debian `linux-source` lockfile and checksums | ✅ allowed | ✅ |
| NVIDIA `.ko`, installer archives (`.run`) | ❌ **never** | ✅ under vendor license |
| Signing keys, MOK private keys, PINs | ❌ **never** | ❌ keep outside repo entirely |
| GPU UUIDs and machine-specific secrets | ❌ **never** | ✅ as required |

Public GitHub Actions workflows must not fetch, upload, or cache proprietary
vendor binaries by default.

---

## 11. Supported vs. tested matrix

| Component | Observed baseline | Qualified status |
|---|---|---|
| Host platform | Intel i9-12900K, Debian Forky, 16 GiB RAM | Current workstation |
| Display GPU | AMD RX 570, `amdgpu`, GNOME/Wayland | Must remain untouched |
| Compute GPU | Tesla V100-PCIE-32GB, `sm_70`, PCI `00000000:01:00.0` | Single-card baseline; multi-GPU **not yet qualified** |
| NVIDIA driver | Proprietary **580.196.07** (R580) | Observed working on `7.2.12+deb14-amd64` and `7.2.15+deb14-amd64` |
| Driver-advertised CUDA API | `13.0` as shown by `nvidia-smi` | **Not** proof that CUDA Toolkit 13 is installed or that the V100 can execute arbitrary Toolkit 13 workloads |
| Local CUDA Toolkit | CUDA 12.9 (verify on the machine) | Not assumed by the framework |
| Kernel source | Debian `linux-source`, pinned in `source.lock.json` | Unresolved pin blocks `build-kernel` |
| Secure Boot | Unknown until `inventory` is run | Unsigned required modules mark `not boot-ready` |

> **Thermal gate.** A prior `nvidia-smi` snapshot reported **86 °C at 0 %
> utilization**. Sustained GPU stress and multi-GPU qualification require a
> separate cooling investigation and must not be inferred from a successful
> driver probe or a successful compile.

> **Driver API vs. toolkit.** `nvidia-smi` reporting “CUDA 13.0” is the driver’s
> advertised API version. It does not mean CUDA Toolkit 13 is installed, nor
> that Volta `sm_70` is supported by every Toolkit 13 framework path. Verify
> from the machine, per workload.

---

## 12. Driver baseline reference

The current observed driver evidence lives at:

- [`docs/hardware/tesla-v100-nvidia-driver-baseline.md`](../../docs/hardware/tesla-v100-nvidia-driver-baseline.md)

This README does not duplicate that evidence; it references it.

---

## 13. Config fragments and the existing assembler

The repository already contains:

- `scripts/kernel/assemble_config.sh` — supports `core`, `pulse`, and `lab`
  config profiles and invokes `merge_config.sh` when available.
- `src/huey/core/base.config`, `core.config`, `pulse.config`, `lab.config` —
  intentional fragments, **not** complete kernel `.config` outputs.
- `src/huey/huey_linux.py` — a legacy import bridge; left intact.

The new framework **consumes** these fragments. It does not replace them.

- `src/huey/core/lab.config` enables `CONFIG_DRM_NOUVEAU=y`. This fragment
  must **not** be applied unmodified to the V100 workstation profile, where
  Nouveau must not claim the Tesla V100.
- Fragments are merged with the actual Debian base config for the selected
  kernel source, resolved via `make olddefconfig`, and the resulting delta is
  reviewed before any build.

---

## 14. Running unit tests

```bash
# Unit tests for the kernel build framework
python -m pytest tests/kernel_build/ -q

# Lint
python -m ruff check src/huey/kernel_build/ tests/kernel_build/

# Type checks
python -m mypy src/huey/kernel_build/
```

Hardware-dependent checks (GPU runtime, thermal, Steam/Proton) are **not**
unit tests. They are performed only in a separately approved qualification
run and reported with measured results, not assumptions.

---

## 15. Related documents

- `kernel/huey-linux/build.yaml` — human-edited build intent
- `kernel/huey-linux/source.lock.json` — pinned kernel source identity and SHA-256
- `kernel/huey-linux/profiles/v100-workstation.config` — V100 workstation fragment
- `kernel/huey-linux/initramfs/modules.list` — early-load modules
- `kernel/huey-linux/initramfs/modprobe.d/huey-v100.conf` — target module policy
- `kernel/huey-linux/signing-policy.md` — Secure Boot and MOK procedure
- `docs/runbooks/huey-kernel-upgrade.md` — install, first boot, and rollback
- `.github/workflows/huey-kernel-builder.yml` — CI (tests and dry-run only)

---

## 16. Status

**Framework status:** implementation in progress (Step 1 of 45).

**Workstation status:** unchanged. No kernel, driver, DKMS, bootloader,
Secure Boot, CUDA, Ollama, ComfyUI, Steam, or RX 570 display configuration has
been modified by this README or by any command it documents.
