# Tesla V100 32 GB: verified NVIDIA Linux driver baseline

**Project:** Monkey-Head-Project / HueyOS  
**Host:** `i9`, Debian Forky, Intel Core i9-12900K / ASUS TUF Z790-PLUS WIFI  
**Evidence captured:** November 11, 2026, 00:12:58 (host-local time)  
**Scope:** Observed **single-card** workstation configuration; not a completed four-GPU qualification or a project-wide requirement for every host.

## Installed GPU and driver

| Component | Verified result | Evidence |
| --- | --- | --- |
| Accelerator | NVIDIA Tesla V100-PCIE-32GB (Volta/GV100, compute capability 7.0) | `nvidia-smi`; architecture is V100 hardware specification |
| PCI bus ID | `00000000:01:00.0` | `nvidia-smi` |
| GPU framebuffer | `32768 MiB` | `nvidia-smi` |
| Linux NVIDIA driver | **`580.196.07`**, R580 series | Both `nvidia-smi` and `sudo modinfo nvidia` |
| NVIDIA kernel-module flavor | Proprietary NVIDIA driver, not the NVIDIA open GPU kernel modules | Host installation configuration |
| CUDA version shown by `nvidia-smi` | **`13.0`** | Driver-reported CUDA API compatibility; **not** the installed `nvcc` toolkit version |
| DKMS for kernel `7.2.12+deb14-amd64` | `nvidia/580.196.07 ... installed` | `sudo dkms status` |
| DKMS for kernel `7.2.15+deb14-amd64` | `nvidia/580.196.07 ... installed` | `sudo dkms status` |

The exact NVIDIA installer version used for this workstation is `NVIDIA-Linux-x86_64-580.196.07.run`. This is a **documented and verified local configuration**, not an instruction to download/run that installer blindly or to pin all project hosts to it. Newer versions require compatibility testing, especially for Volta, out-of-tree DKMS, and CUDA inference workloads.

**CUDA version distinction:** `nvidia-smi`'s “CUDA Version: 13.0” reflects the driver-side compatibility interface. Check `nvcc --version` to determine whether a standalone CUDA Toolkit is installed and which toolkit version is active; a Python environment's bundled CUDA runtime may be different again.

## Reproduce the driver check

```bash
uname -r
nvidia-smi
sudo modinfo nvidia | grep '^version:'
sudo dkms status | grep '^nvidia/'
nvcc --version  # optional: only if the CUDA Toolkit's nvcc is installed
```

On the observed workstation, `modinfo` and `dkms` were not on the unprivileged user's `PATH`; `sudo modinfo` and `sudo dkms` succeeded. Missing commands in the interactive shell **did not** mean the driver or DKMS modules were absent.

For a narrower machine-readable check:

```bash
nvidia-smi --query-gpu=name,pci.bus_id,driver_version,memory.total,temperature.gpu --format=csv
sudo modinfo -F version nvidia
sudo dkms status
```

A `580.196.07` match confirms the observed driver version, but **does not by itself prove** that new kernel packages, CUDA workloads, and Vulkan/Proton all work. Validate each layer after changes.

## Kernel upgrade and rollback procedure

The captured DKMS output contains installed builds for **both Debian kernels `7.2.12` and `7.2.15`**. It does **not** establish that a future 7.3.x kernel has a working NVIDIA build.

1. Install the candidate kernel and its **matching headers** from the configured Debian repository; examine `apt -s full-upgrade` before committing.
2. Confirm `sudo dkms status` reports `nvidia/580.196.07` **installed for the new kernel** before relying on it.
3. Keep the last known working kernel in GRUB as a rollback option.
4. After reboot, verify `uname -r`, `nvidia-smi`, `sudo modinfo -F version nvidia`, then test the actual Ollama / ComfyUI / PyTorch CUDA workload.
5. If testing gaming, verify the opt-in NVIDIA Vulkan/Proton path separately. The AMD RX 570 can remain the desktop display GPU; NVIDIA Vulkan driver selection is not implied by CUDA or `nvidia-smi` working.

Do not assume DKMS success simply because a kernel image installed. Do not remove the previous bootable kernel until the replacement has been exercised.

## V100 graphics and desktop arrangement

The **Tesla V100** is used as a compute accelerator on this workstation. The **AMD Radeon RX 570** drives the GNOME/Wayland display. A user-scoped, opt-in NVIDIA Vulkan driver setup was used for Steam/Proton; this graphics integration is separate from the CUDA kernel-module checks above.

The working Far Cry 4 Steam launch option observed during troubleshooting was:

```text
VK_LOADER_DRIVERS_SELECT='*nvidia*' PROTON_LOG=1 /home/dlrp/.local/bin/v100-vulkan %command%
```

That path and wrapper are **host-local examples**, not portable repository defaults. Without `VK_LOADER_DRIVERS_SELECT='*nvidia*'`, Steam's runtime had selected `*radeon*` and excluded the custom NVIDIA ICD manifests.

## Thermal observation requiring attention

The November 11 `nvidia-smi` snapshot reported **86°C**, performance state `P0`, **60 W**, **0% utilization**, **0 MiB GPU process memory**, and no listed active processes. This is **an observation, not proof of a driver fault**, but it warrants cooling/airflow and sensor investigation before sustained inference or gaming, especially because the Tesla V100 PCIe is a high-power accelerator. Recheck temperature, fan/airflow, throttling and power under controlled conditions rather than treating a successful driver load as a thermal acceptance test.

## Change policy

- **Record:** exact driver, kernel, GPU identity, CUDA toolkit/runtime versions, Vulkan ICD configuration, and diagnostic commands.
- **Keep separate:** hardware-specific driver deployment and Python package dependencies; the proprietary driver is **not** a pip requirement.
- **Test before changing:** do not automatically replace this verified driver version or switch to an open kernel module solely because a newer branch exists.
- **Future scale:** the planned four-V100 target requires per-GPU discovery, thermal qualification, power and PCIe topology verification; this document only captures the current single-card host.
