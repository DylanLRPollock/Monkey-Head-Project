# Hardware Enablement Guide — Huey OS (Forky Standard · HueyOS 7.0 Kernel Family)

**System Platform**: Supermicro X9QRI-F+  
**Chipset**: Intel C602  
**CPU**: 4 × Xeon E5-4627 v2  
**GPU**: 2 × AMD Radeon RX 570 (8GB)  
**Network**: 10GbE Areion (AQuantia AQtion)  
**Storage**: 2 × Kingston SSD 240 GB (RAID)  
**Bluetooth**: ASUS USB-BT500  
**Wi-Fi**: USB 2.4GHz adapter
**OS Base**: Debian “Forky” (standardized baseline)
**Kernel Family**: HueyOS **7.0-based** custom RT kernels

> **Current state:** Hardware enablement is standardized on the **Forky + 7.0 kernel family** line.  
> The former **6.16.12 → 6.18.2 migration-era line** is now historical and is no longer the deployment target for active systems.

## Kernel Model and Role Split

HueyOS now separates kernel responsibilities into two maintained lanes:

- **Core kernel lane (hueyos-core-7.0-rt)**  
  Stable hardware baseline for boot, storage, networking, and platform management.
- **Pulse kernel lane (hueyos-pulse-7.0-rt)**  
  Rapid-iteration lane for scheduler tuning, AI workload latency controls, and feature experiments.

### Operational policy

- **Core** is the default for production and recovery images.
- **Pulse** is for validated performance profiles and staged rollout.
- Both lanes share the same hardware compatibility matrix and required firmware set documented below.
- Promotion path is **Pulse → Core** only after soak validation and regression sign-off.

---

## Core Drivers (Built-in or Native)

### 🧩 Chipset — Supermicro X9QRI-F+ (Intel C602)

- Uses standard AHCI/XHCI for SATA, USB 3.0, and PCIe.
- No driver install needed; supported since kernel 3.17.
- IPMI: built-in `ipmi_si` driver; use `ipmitool`, `ipmi-dbg` for userland access.

### 🧠 CPUs — Intel Xeon E5-4627 v2

- Install: `intel-microcode` (from Debian “non-free-firmware”).
- Load microcode at boot for security and stability.
- Source: `apt install intel-microcode`

### 🎮 GPU — AMD Radeon RX 570 (2 × 8GB)

- Use open-source `amdgpu` (in kernel).
- Install firmware: `firmware-amd-graphics`
- Optional: AMD ROCm/OpenCL (All-Open stack) via `amdgpu-install -y --usecase=graphics`
- Kernel Flags: `CONFIG_DRM_AMDGPU`, Polaris family support

### 🌐 NIC — Aquantia AQtion / ROG Areion (10 GbE)

- Driver: `atlantic` (in-kernel)
- MTU tuning: `ip link set enpXsY mtu 9000`
- Optional vendor driver: `atlantic-x.y.z.deb` from Marvell; requires build tools

### 💾 Storage — 2 × Kingston SSD (240 GB RAID)

- C602 “Intel Rapid Storage” = fakeraid (avoid in BIOS)
- Recommended: Linux software RAID via `mdadm`
- Install: `apt install mdadm`
- Optional (BIOS RAID): `dmraid` + `dm-mod` kernel module

### 🧲 Bluetooth — ASUS USB-BT500 (Realtek)

- Driver: Kernel `btusb` + `firmware-realtek`
- Kernel Flags: `CONFIG_BT_HCIBTUSB` = m

### 📡 Wi-Fi — USB 2.4GHz Dongle

- Identify chipset: `lsusb`
- Firmware options: `firmware-realtek`, `firmware-atheros`, `firmware-iwlwifi`
- Manual install: `dpkg -i firmware-*.deb`
- Enable non-free: add `contrib non-free non-free-firmware` to `/etc/apt/sources.list`

---

## System Setup Steps

1. **Enable Non-Free Firmware Sources**  
   Edit `/etc/apt/sources.list`:  
   Add `contrib non-free non-free-firmware` to all active mirror lines.  
   Then run:  
   ```bash
   sudo apt update
   ```

2. **Install Firmware Packages**  
   For offline install:
   ```bash
   apt download firmware-linux firmware-amd-graphics firmware-realtek firmware-linux-nonfree intel-microcode
   sudo dpkg -i *.deb
   ```

3. **Build a HueyOS 7.0 Kernel (Core or Pulse lane)**
   - Select lane target:
     - `hueyos-core-7.0-rt` for production/stability
     - `hueyos-pulse-7.0-rt` for performance staging
   - Keep config parity across both lanes for hardware enablement flags.
   Minimum `.config` flags:
   - `CONFIG_AHCI`
   - `CONFIG_XHCI_HCD`
   - `CONFIG_DRM_AMDGPU`
   - `CONFIG_NET_VENDOR_AQUANTIA`
   - `CONFIG_BT_HCIBTUSB`
   - `CONFIG_MD_RAID456`
   - `CONFIG_DM_RAID`
   - `CONFIG_FIRMWARE_IN_KERNEL=y`

4. **Initialize RAID**  
   ```bash
   sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdX /dev/sdY
   sudo mkfs.ext4 /dev/md0
   echo '/dev/md0 /mnt/raid ext4 defaults 0 0' | sudo tee -a /etc/fstab
   ```

5. **Vendor Driver Installs (Optional)**  
   - 10 GbE: build `atlantic-x.y.z.deb` (if required)
   - AMD ROCm: `amdgpu-install -y --usecase=graphics`

---

## Notes for Huey OS Deployment

- Founding Father AI will reside on `/mnt/huey/sd0` in `FoundingPartition.sys` (read-only)
- All initialization logic checks `intel-microcode` presence before citizenship is granted
- Z-Wave mesh should come online with default Debian GPIO bus overlays
- All installation logs should be mirrored to `/var/log/huey_bootstrap/` (RAID)
- Core/Pulse lane selection must be recorded in deployment metadata for audit and rollback control

---

*Guide maintained by Huey AI for Dylan · Last updated: 2026-04-10*
