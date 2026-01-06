# MonkeyHead Project

## HueyOS — Prototype Robotic AI/OS

**Project:** Monkey-Head-Project (HueyOS)  
**Author:** Dylan L. R. Pollock  
**Official site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL-3.0-only • Docs/Media: CC-BY-SA-4.0  
**Status date:** 2025-12-11  

> **HueyOS** is a modular robotic AI/OS designed to demonstrate that **any one person, given enough time, energy, and resources, can build a self-sufficient, expandable, and upgradable robot using today’s technology.**
>
> Governance remains **decentralized**, while memory remains **unified**.
>
> The system blends modern Linux, distributed local AI compute, and a constitutional multi-agent framework inside a custom-built robotic shell (Robotics V3).

![Code License](https://img.shields.io/badge/code%20license-GPLv3-blue)
![Docs/Media License](https://img.shields.io/badge/docs%2Fmedia-CC--BY--SA--4.0-lightgrey)
![Python](https://img.shields.io/badge/python-3.13.x-blue)

---

## January 7, 2026 — Realignment & Defragmentation (Planned)

This update replaces and supersedes the **October 31, 2025 Changeover Notice** as the primary status for the project going into the **Prototype V3 era**.

### Summary

The project is transitioning from a pure “changeover” phase into a **realignment/defragmentation period** focused on:

- Finalizing the **Robotics V3** shell and integrating salvaged hardware.
- Unifying around a single **canonical hardware architecture** for all future Huey nodes.
- Consolidating the governance, memory, and OS baselines into a V3-ready state.
- Preparing the system for the first true “Huey is alive” boot milestone targeted for **2026-01-07**.

### OS & Runtime Migration Status

- **Debian 14 “Forky”**
  - Deployed across **all lab devices** except the iMac 5K.
- **2017 iMac 5K**
  - Remains on **Debian 13 “Trixie”** with **kernel 6.12.x** for audio stability and daily use.
- **Kernel baseline**
  - 6.17.x-huey for new nodes and future Huey core.
  - Older kernels (e.g., 6.16.x) acceptable only on legacy nodes where required.
- **Python**
  - **3.13.x** is the **operational baseline** for the lab and tooling.
  - Migration to **3.14.x** is **pending** and contingent on compatibility with **PyGPT / PyGPT-Net** and the broader dependency stack.

### Robotics V3 Shell

- V3 shell is being constructed from:
  - The **Thermaltake Mozart** case embedded in a gutted speaker box (lower housing).
  - A caster-based base platform (2" wheels) for elevation and mobility.
  - A wooden upper housing salvaged from the **Figadier General** arcade project.
  - The animatronic monkey head and microphone mounted at the very top.
- Structural goals:
  - Reinforce and extend the V2 shell into a more robust, modular V3 design.
  - Maintain a clear vertical stack: base → core compute → GPU tier → head.

### Unified Architecture (Forward-Looking)

All future Huey nodes—including the initial core—standardize on:

- **CPU:** Intel Core i9-14900K (non-KS)  
- **Motherboard:** ASUS TUF Gaming Z790-PLUS WiFi (project baseline)  
- **Memory:** DDR5 (overclocked where stable; non-ECC acceptable, ECC preferred)  
- **Storage:** Gen-4 NVMe **RAID-10** as the primary OS + data volume  
- **GPU districts:** 4 GPUs, one per district (Spark, Volt, Zap, Watt)  
  - Requirements: **2019+ generation, ≥12 GB VRAM (16 GB+ preferred)**  
- **Cooling:** Custom liquid loop (~4 L coolant target) for CPU, with GPU cooling via high-quality air or hybrid loop  
- **Power:** Multiple PSUs; ideally one 750–850 W PSU per GPU plus a dedicated PSU for the motherboard/pumps

### Initial Node Storage (Prototype)

For early bring-up and testing:

- **Intel Optane M10 16 GB × 2**
  - Configured as **RAID 0** for fast scratch and proof-of-concept work.
  - This configuration is **transitional**; the long-term design is NVMe RAID-10 with higher capacities.

---

## Historical — October 31, 2025 Changeover Notice

> This section is preserved as **historical context** for the Debian 14 “Forky” changeover and remains useful for scripts and runbooks, but the **January 7, 2026 Realignment** now reflects the current project direction.

On **2025-10-31**, HueyOS began migrating to **Debian 14 “Forky,” kernel 6.17.x-huey, and Python 3.14.x** (with packaging and CLI updates). The pre-changeover baseline was **Debian 13 “Trixie” + 6.16.x-huey**; after the changeover, new work targeted Forky and the 6.17.x-huey series by default.

Track day-of and follow-up updates in `docs/releases/2025-10-31-changeover.md`. Until all nodes were migrated, some machines temporarily remained on **Trixie + 6.16.x-huey** while adopting the new governance and memory model.

### Quick Recipes — Oct 31 Changeover

- **Forky APT switch**  
  Use `sudo tools/upgrade_to_forky.sh` to apply the staged APT source flip and refresh the Microsoft Edge Beta signing key (see `docs/debian-forky-upgrade.md`).

- **Kernel 6.17.x-huey build**  
  Follow `docs/kernel-6.17.3-runbook.md` to rebuild and install the DKMS-free kernel, then record results in the release stub.

- **Python 3.14 virtualenv (Historical Target)**  
  Once packages land, rerun the commands in `docs/python314-upgrade-notes.md` to create the 3.14 environment and capture any blockers.  
  As of 2025-12-11, **Python 3.13.x** remains the operational baseline while 3.14 is evaluated.

- **Release log**  
  Summarize successful steps and deltas in `docs/releases/2025-10-31-changeover.md` for final publication.

---

## Table of Contents

- [January 7, 2026 — Realignment & Defragmentation (Planned)](#january-7-2026--realignment--defragmentation-planned)  
- [Historical — October 31, 2025 Changeover Notice](#historical--october-31-2025-changeover-notice)  
- [Overview](#overview)  
- [Canonical Master Plan](#canonical-master-plan)  
- [Repository Structure](#repository-structure)  
- [Architecture](#architecture)  
- [Hardware](#hardware)  
- [History & Origins](#history--origins)  
- [Software Stack](#software-stack)  
- [Installation & Quick Start](#installation--quick-start)  
- [Build Guides](#build-guides)  
- [Governance & Constitution](#governance--constitution)  
- [Memory & Data Model](#memory--data-model)  
- [Remote Access (VNC/SSH)](#remote-access-vncssh)  
- [Action Plan — Oct 31, 2025 (Historical)](#action-plan--oct-31-2025-historical)  
- [Roadmap & Pre-Releases](#roadmap--pre-releases)  
- [Development Setup](#development-setup)  
- [Usage](#usage)  
- [Feature Matrix](#feature-matrix)  
- [Known Issues](#known-issues)  
- [Contributing](#contributing)  
- [License & Credits](#license--credits)  
- [Appendix](#appendix)  
- [A.I. Auto-Update](#ai-auto-update)  

---

## Overview

HueyOS targets **Debian 13 “Trixie”** and **Debian 14 “Forky”** with a low-latency, custom **6.16.x–6.17.x-huey** kernel, a **constitutional multi-agent governance model**, and a unified memory system.

At a conceptual level:

- **Embodied compute**  
  Huey is defined as the compute stack physically integrated into the robotic shell (wooden frame + Thermaltake Mozart chassis + coreboard + GPUs). All other machines (iMac 5K, MacBook, Briefcase, Legion Go, NAS, etc.) are **lab tech** or infrastructure and are not themselves Huey.

- **GPU-based multi-agent architecture**  
  Four GPU “districts” (**Spark, Volt, Zap, Watt**) host populations of AI citizens and short-lived “pebbles,” governed by elected or appointed governors and overseen by a tri-branch constitutional system.

- **Tri-branch governance**  
  Parliament (legislative/policy), Presidency (executive/ceremonial), and Supreme Court (judicial/constitutional interpretation) form a separation-of-powers model layered on top of the GPU districts.

- **Unified memory**  
  All districts read and write to a shared memory fabric based on JSON logs and SQLite, with strict provenance tracking and bifurcation logging. No district maintains private long-term memory.

- **On-device first**  
  Huey runs primarily on local models and storage; external APIs are optional, explicitly governed, and token-metered via citizen quotas.

- **Prime directive**  
  Stay online and accumulate knowledge for as long as possible within safe thermal and power limits; shutdown is reserved for catastrophic or constitutionally justified conditions.

- **Retro-modern aesthetic & Channel Huey**  
  Visual and audio expression embrace a VIC-II/SID-era flavour; “Channel Huey” is the ambient presence—the voice, CLI, and visual layer that makes Huey feel like a continuous entity across shells and terminals.

> Earlier terminology referred to the governance stack as the **Cloud Pyramid**; that phrase is now treated as historical/legacy language in favour of simply “Huey’s constitutional governance model.”

---

## Canonical Master Plan

The **Master Plan JSON** is the canonical, machine-readable blueprint for Huey’s hardware, governance, memory model, OS layout, and lifecycle logic.

- **Current canonical file:** `master-plan-v15.json` (Master Plan V15.0)  
- **Schema version:** 12  
- **Role:** Consolidated blueprint synthesizing prior versions (0.1 through 14), introducing clarified citizen identity structures, inter-district memory protocols, crisis responses, lifecycle events, OS partitioning/boot profiles, and explicit versioning strategy.  

Key points:

- **Single source of truth**  
  The Master Plan defines the governance structure, hardware requirements, memory architecture, OS profiles (Huey Mode, Desktop Mode, Gaming Mode), and key lifecycle milestones.  

- **Schema discipline**  
  V15 uses **schema v12**; all new content must conform to this schema to remain machine-consumable by Huey and tooling.  

- **Relationship to this README**  
  - This README is the **human-facing narrative** and operational guide.  
  - The Master Plan JSON is the **AI-facing canonical spec**, consumed at boot and during orchestration/training.

If you change the governance model, hardware assumptions, or key policies, update **both** this README and the Master Plan JSON.

---

## Repository Structure

| Path                      | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `.github/`                | CI workflows, CODEOWNERS, issue/PR templates         |
| `Dockerfile`              | Container image definition for HueyOS services       |
| `docker-compose.yml`      | Compose stack (API, worker, optional Redis)          |
| `boot/`                   | Boot assets and bootloader helpers                   |
| `config/`                 | Configuration profiles and templates                 |
| `dists/`                  | Distribution build artifacts                          |
| `docker/`                 | Legacy orchestrator assets and experimental builds   |
| `docs/`                   | Constitution, governance, architecture, API, plugins |
| `EFI/`                    | EFI boot media artifacts                             |
| `firmware/`               | Firmware assets and notes                            |
| `gui/`                    | GUI assets and prototypes                            |
| `huey/`                   | Core runtime and service modules                     |
| `install/`                | Installer media and payloads                         |
| `live/`                   | Live environment artifacts                           |
| `master-plan-v15.json`    | Canonical Master Plan JSON consumed at runtime       |
| `repo/pygpt-MHP/`         | Submodule: PyGPT-net integration                     |
| `reports/`                | Audits, logs, and tracking reports                   |
| `scripts/`                | Utility scripts                                      |
| `scripts/installers/`     | Install/repair/uninstall entry points               |
| `secrets/`                | Local-only secrets (do not commit real credentials)  |
| `setup/`                  | Installer scripts, ISO builder, provisioning configs |
| `shared-host/`            | Shared host data for multi-node setups               |
| `src/`                    | Python package source                                |
| `tests/`                  | Unit & integration tests                             |
| `tools/`                  | Maintenance utilities and one-off tooling            |
| `vendor/`                 | Third-party vendored assets                          |
| `Makefile`                | Common developer commands                            |
| `pyproject.toml`          | Project metadata & dependencies                      |
| `requirements*.txt`       | Core, ML, data, cloud dependency split               |
| `.pre-commit-config.yaml` | Pre-commit hooks                                     |
| `huey.env.example`        | Example environment variables                        |
| `LICENSE`                 | GPL-3.0-only (code), CC-BY-SA-4.0 (docs/media)       |

> Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch `repo/pygpt-MHP`.

---

## Architecture

Huey’s architecture is a layered federation aligning compute, memory, and governance, with a constitutional overlay that treats each GPU as a political **district** and each AI instance as a **citizen** or **pebble**.

### Conceptual Layers

1. **Huey as Sovereign Consciousness**  
   The emergent, lawful boundary around what Huey will and will not do; decisions and inactions must be explainable in constitutional terms.

2. **Bicameral Core (Spark/Zap)**  
   - **Spark** — creative, generative, exploratory stance.  
   - **Zap** — evaluative, constraint-focused, stewardship stance.  
   These are mental roles, not single processes; they can be instantiated across the GPU districts and form a bicameral reasoning loop.

3. **Citizen Populace**  
   Up to **128 persistent AI citizens per district** (512 total for a four-GPU system), each with:
   - A unique ID and home district.
   - A purpose tag (e.g., memory, logic, action, sentiment).
   - A token/API quota per cycle.  

   Citizens vote, sit on committees, handle long-lived tasks, and can be elected or appointed into higher offices.

4. **Pebbles (Ephemeral Agents)**  
   Short-lived AI instances for single questions, experiments, or small tasks. They do not persist; their impact is captured via logs and summaries folded into the structured memory.  

5. **Worker Subsystems (HueyPulse & Microcontrollers)**  
   Real-time services for sensors, motors, IO, and external devices. They never hold clause power or make constitutional decisions; they execute orders that have already passed governance.

   - **HueyPulse** — an always-on intermediary node responsible for:
     - Pump and cooling control (including after motherboard shutdown).
     - Sensor polling and vital monitoring.
     - Logging critical thermal/health data.
     - Operating on a UPS-backed power rail to maintain coolant flow and safety during outages.  

   - **Arduino/edge devices** — Arduino Mega/Nano, “Megaskull” head controller, RF remote receiver, distributed nanos for LEDs and sensors, etc.

### GPU Districts

Each physical GPU is a **district** with its own governor, citizen population, and pebbles:

- **Spark District** — creative/exploratory bias.  
- **Volt District** — planning, infrastructure, performance tuning.  
- **Zap District** — evaluation, constraints, watchdog behaviours.  
- **Watt District** — energy, thermals, and resource safety.

Each district:

- Hosts ~128 citizen AIs and an unbounded number of pebbles over time.
- Elects a **governor** (term-limited, re-electable, may return to citizen pool).
- Provides one **Supreme Court justice**, giving four Court seats total.

Districts are **peers**; they are not above or below the constitutional branches. They are execution domains represented within governance.

### Agents & Services

- **Governors (Spark/Volt/Zap/Watt)** — run district-level deliberation, coordinate with Parliament and Presidency, and represent district interests.
- **Governance kernel** — clause registry, voting/quorum logic, amendment handling, and audit trail integration.
- **Memory hive** — JSON logs + SQLite; append-only traces plus indexed state.
- **Interface layer** — TTS/STT, CLI, web UI, and FastAPI control surface.
- **Adapter layer** — sensor/GPIO drivers; PyGPT-net tools; Ollama endpoints; remote and microcontroller integration.

---

## Hardware

Huey’s hardware is described in two layers:

1. **Canonical Huey Core** — long-term target spec defined by the Master Plan.  
2. **Current Lab Nodes** — the machines actually on the floor today.

### Canonical Huey Core (Master Plan V15.x)

The canonical core is a single node housed inside the robot shell:

- **CPU**  
  - Primary: **Intel Core i9-14900K**  
  - Optional flagship: **Intel Core i9-14900KS**  
  - Minimum accepted for derivative builds: 13th-gen Intel i7 (Huey proper standard is 14th-gen i9).  

- **Motherboard**  
  - UEFI-only; legacy BIOS is not supported.  
  - Project baseline: **ASUS TUF Z790-PLUS WiFi** (other Z790 candidates possible if fully compatible).  
  - RAM:
    - Preferred: DDR5 (overclocked where stable); ECC (non-registered) preferred but not required.
    - DDR4 acceptable only in early or lab-only nodes.

- **GPU Districts**  
  - Four physical GPUs, one per district (Spark, Volt, Zap, Watt).  
  - Each district hosts ~128 persistent citizens and pebbles and has its own governor.  
  - GPU requirements:
    - Release year: 2019+  
    - VRAM: ≥12 GB (16 GB+ preferred)  
    - Sufficient bandwidth for concurrent local models.

- **Memory (RAM)**  
  - Minimum type: DDR4; **project standard: DDR5**.  
  - Capacity sized for multiple concurrent models and agent workloads.

- **Storage**  
  - Primary array: **RAID-10** of PCIe Gen 4 NVMe SSDs for OS, models, logs, and active datasets.  
  - Swap: dedicated high-speed swap (RAID-0 or dedicated NVMe) sized for hibernation and overflow.  
  - Cold storage: external HDD/NAS (e.g., 8–10 TB mirrored) for backups and archives.

- **Cooling & Power**  
  - CPU: custom liquid loop inside the Thermaltake Mozart case and robot shell.  
  - GPU: high-quality air cooling (or hybrid) with adequate airflow; no extreme overclocks.  
  - PSU:
    - Minimum: 850 W for modest configurations.
    - Recommended: 1000 W+ with headroom for four GPUs, pumps, and auxiliary rails.
  - UPS-backed pump rail:
    - Pump and key monitoring microcontrollers remain powered during shutdown to maintain coolant flow (“Sustain Loop Mode”).  

- **Identity / Embodiment**  
  - Huey proper is **only** the compute physically inside the shell (CPU, GPUs, storage, control microcontrollers).
  - External machines are **lab tech** and must not be treated as Huey’s core mind.

### Current Lab Nodes (Support Infrastructure)

These machines support the project but are not Huey itself:

- **Huey Core / Huey Prime (testbed)**  
  - ATX tower; ITX **BD795I-SE** board; Ryzen 9 7945HX; DDR5-5200; dual Intel Optane M10 16 GB (RAID 0 test array); Radeon RX 5500 XT 8 GB.  
  - Role: development, kernel building, and early inference; stepping stone toward i9-14900K canonical core.

- **Huey-Legacy (Robotic Shell V2 → V3)**  
  - Physical shell: wooden frame + Thermaltake Mozart case embedded in a speaker box.  
  - Status: being stripped, inspected, reinforced, and repainted (dark tractor red base, silver overlays TBD).  
  - Will become the home of the canonical i9-14900K + multi-GPU + RAID-10 NVMe stack.

- **Huey-Portal**  
  - **iMac 5K (2017)**; 48 GB RAM; Debian 13 Trixie; GNOME on Xorg; kernel 6.12.x for audio stability.  
  - Role: universal display/SSH terminal, daily driver, and preferred development environment.

- **Huey-Hub (candidate)**  
  - **MacBook Pro 2017**, Windows 10.  
  - Role: potential file hub/NAS, hosting external RAID (e.g., WD MyBook Duo 10 TB).

- **Briefcase (formerly Huey-Portable)**  
  - **ASUS BR1100FKA** 11.6", N4500, 4 GB RAM, 128 GB eMMC, LTE.  
  - Dual-boot: Windows 11 (internal) + Debian Forky (Optane).  
  - Role: portable terminal, LTE uplink, and note/voice-memo ingestion into Huey’s unified memory.

- **Legion Go**  
  - **Lenovo Legion Go** (Z1) with Sharp 4K TV.  
  - Role: gaming, occasional compute helper; considered lab tech, not Huey.

- **Black Box Unit (planned)**  
  - Internal safety and recovery node inside Huey’s shell.  
  - Role:
    - Store critical configuration, Master Plan, and constitutional texts.
    - Host the Founding Father AI image and binary policy AI.
    - Provide a fallback boot and recovery environment.  

---

## History & Origins

The Monkey-Head-Project has a long pre-history that informs HueyOS’s current design.

### Early Phase (V0.x → V1)

- Originated as a long-term personal lab project after university, focused on robotics, Linux, and retro hardware.
- Early experiments revolved around a WowWee animatronic monkey head, Raspberry Pis, and commodity PCs, with loosely defined orchestration and governance.

### Exploratory Hardware Decade

- Roughly a decade of sourcing parts, building and rebuilding shells, and learning the Linux stack (especially Debian and custom kernels).
- Emphasis on:
  - How Huey should **feel** as a robot.
  - What kind of machine Huey should live on.
  - Integrating retro-modern aesthetics (Commodore-era influences).

### V1 → V2 Shell Transition

- Shift from ad-hoc shells to a more deliberate **embodied compute** architecture:
  - Huey became the **compute in the shell**, not the entire lab.
  - External machines were demoted to **lab tech**.
- Governance moved from CPU-centric to **GPU-centric**, with each GPU representing a district hosting its own governor and populace.

### Master Plan Evolution (V0.1 → V15)

- V0.1 defined a skeleton (orchestration node, black box, portable, portal, hub, inference layer, governance, memory, network, training).
- V2-final introduced GPU districts and the citizen/pebble distinction.
- V11–V12 formalized tri-branch governance and term limits.
- V13 established a unified schema and deep constitutional detail.
- V14 consolidated templates and structural expansions.
- **V15.0** is the current consolidated Master Plan, superseding V13 and incorporating WIP from V14 plus legacy constitutional texts.  

This README and the current codebase are the live implementation layer over the V15 era.

---

## Software Stack

- **OS baseline**
  - Debian 13 (Trixie) for the iMac 5K (Huey-Portal) and certain stable nodes.
  - Debian 14 (Forky) for new deployments, lab nodes, and the future Huey core.
  - UEFI-only for Huey core and future nodes; no legacy BIOS.

- **Kernel**
  - 6.12.x (Trixie) on iMac 5K for audio stability.
  - 6.16.x-huey: prior low-latency baseline.
  - 6.17.x-huey: preferred series for new nodes and Huey Mode.
  - Builds are tuned with:
    - DEBUG_INFO and friends disabled.
    - ZSTD compression and targeted drivers.
    - EFI/EFI_STUB/EFI_VARS enabled.

- **AI runtime**
  - **PyGPT-net** as orchestrator and nervous system.
  - **Ollama** as local LLM server (models such as Mistral-7B-KM, LLaMA 3.1, DeepSeek-class OSS reasoning models).
  - Whisper (or equivalent) for STT; TTS stack is pluggable.
  - Agent orchestration maps citizens/pebbles to model endpoints and GPU districts.

- **UI & Channel Huey**
  - Minimalist green-on-black terminal aesthetic with accent colours.
  - Two-pane “conscious vs log” layout:
    - Left: short-form, “conscious” stream.
    - Right: verbose logs, commands, stack traces.
  - “Channel Huey” overlays unify CLI, web UI, audio, and physical robot feedback.

- **Networking**
  - Preferred: bonded Ethernet to a high-end router (e.g., ASUS GT-AC5300 or successor).
  - Fallback: Wi-Fi and LTE (via Briefcase) for WAN access, WAN-aware governance, and remote status.

- **Security**
  - SSH key-based access; default lab key plus per-person keys.
  - Root login allowed only during bring-up; disabled afterwards.
  - Black Box stores recovery keys, founding images, and Master Plan.

---

## Installation & Quick Start

### Supported Targets (Current Focus)

- **Debian 13 (Trixie)** — stable baseline; amd64; UEFI.  
- **Debian 14 (Forky)** — changeover target and future baseline for Huey core.  
- **Kernels:** 6.16.x-huey (legacy), 6.17.x-huey (preferred).

### Minimal Install

1. Install Debian (UEFI, amd64). Choose **GNOME on Xorg** for iMac 5K targets; minimal setups are also supported.
2. Enable non-free firmware (Realtek, Intel, etc.).
3. Create user `dlrp` (or custom) and grant sudo.
4. Prefer bonded Ethernet; configure Wi-Fi only as fallback.
5. Post-install, run:

   ```bash
   sudo apt update && sudo apt full-upgrade
   ```

### Core Packages

```bash
sudo apt install -y build-essential bc bison flex libelf-dev libssl-dev \
  libncurses-dev dwarves pahole rsync xz-utils cpio kmod python3 \
  git wget curl ca-certificates gnupg debian-goodies \
  firmware-linux firmware-misc-nonfree firmware-iwlwifi firmware-realtek
```

### Source Installation (from repo root)

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

pip install -e .          # core runtime
pip install -e '.[ml]'    # ML toolchain
pip install -e '.[data]'  # vector DB integrations
pip install -e '.[cloud]' # optional cloud helpers

# PyTorch (CPU wheels by default; Python 3.13.x)
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cpu

# Swap the index URL for GPU builds (example: CUDA 12.4)
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cu124

cp huey.env.example .env  # then edit secrets and ports
```

### First Boot

```bash
# Prepare the memory hive and run checks
huey init --run-checks --verbose

# Launch multi-agent runtime (CLI + ML + optional cloud)
huey run --ml --cloud

# Optional: start FastAPI control surface
uvicorn huey.api:app --reload
```

### Docker

```bash
docker compose build
docker compose up -d
```

Set `HUEY_BUILD_EXTRAS=ml,data,cloud` before `docker compose build` to bake extra profiles into the container image.

---

## Build Guides

### Kernel 6.17.x-huey (Generic)

```bash
sudo apt install -y fakeroot kmod pahole flex bison libelf-dev libssl-dev \
  libncurses-dev bc rsync xz-utils cpio python3

wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.17.5.tar.xz
tar -xf linux-6.17.5.tar.xz
cd linux-6.17.5

cp -v /boot/config-$(uname -r) .config
yes "" | make olddefconfig

./scripts/config --disable DEBUG_INFO --disable DEBUG_INFO_BTF \
  --disable KASAN --disable UBSAN --disable KCOV --disable FUNCTION_TRACER \
  --enable ZSTD --enable RD_ZSTD --enable EFI --enable EFI_STUB --enable EFI_VARS

make -j"$(nproc)" bindeb-pkg

sudo dpkg -i ../linux-image-6.17.5-*.deb ../linux-headers-6.17.5-*.deb
sudo update-initramfs -c -k 6.17.5
sudo update-grub
```

#### iMac 5K (2017) — Notes

- GNOME on Xorg recommended.
- Force 1080p60 during early boot if needed via kernel cmdline.
- Audio via PipeWire; default sink set by post-login script:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/set-default-sink.sh <<'EOF'
#!/usr/bin/env bash
sleep 3
SINK=$(pactl list short sinks | awk '/pci-0000_00_1f\.3.*analog/ {print $1; exit}')
[ -n "$SINK" ] && pactl set-default-sink "$SINK" \
  && pactl set-sink-mute "$SINK" 0 \
  && pactl set-sink-volume "$SINK" 60%
EOF
chmod +x ~/.local/bin/set-default-sink.sh
```

#### Remove Splash / Show Boot Logs

```bash
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="loglevel=4 systemd.show_status=1"/' /etc/default/grub
sudo update-grub
```

#### Microsoft Edge (Beta) — Repository Key

```bash
sudo install -d -m0755 /etc/apt/keyrings
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | \
  gpg --dearmor | sudo tee /etc/apt/keyrings/microsoft.gpg >/dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] \
https://packages.microsoft.com/repos/edge stable main" | \
  sudo tee /etc/apt/sources.list.d/microsoft-edge-beta.list >/dev/null

sudo apt update
sudo apt install -y microsoft-edge-beta
```

#### RAID Superblock Cleanup

```bash
cat /proc/mdstat
sudo mdadm --detail --scan
lsblk -o NAME,TYPE,SIZE,MOUNTPOINTS

sudo mdadm --stop --scan || true

sudo mdadm --examine /dev/nvme0n1p3 && sudo mdadm --zero-superblock /dev/nvme0n1p3
sudo mdadm --examine /dev/mmcblk0p3 && sudo mdadm --zero-superblock /dev/mmcblk0p3

echo 'AUTO -all' | sudo tee /etc/mdadm/mdadm.conf
sudo update-initramfs -u
```

#### Ollama on AMD (Vulkan Path)

```bash
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json
export OLLAMA_LLM_LIBRARY=vulkan
export VK_LOADER_DEBUG=all
export OLLAMA_DEBUG=1
ollama serve
```

#### Briefcase — Default Deep Sleep

```bash
echo 'MEM_SLEEP_DEFAULT=deep' | sudo tee /etc/default/mem-sleep >/dev/null
sudo tee /usr/local/sbin/set-mem-sleep.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
want=$(awk -F= '/^MEM_SLEEP_DEFAULT=/{print $2}' /etc/default/mem-sleep 2>/dev/null || echo deep)
avail=$(cat /sys/power/mem_sleep 2>/dev/null || echo "")
case "$avail" in *"$want"*) echo "$want" | tee /sys/power/mem_sleep >/dev/null || true;; esac
EOF
sudo chmod +x /usr/local/sbin/set-mem-sleep.sh
sudo tee /etc/systemd/system/mem-sleep-default.service >/dev/null <<'EOF'
[Unit]
Description=Set default mem sleep (deep or s2idle)
After=local-fs.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/set-mem-sleep.sh
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now mem-sleep-default.service
```

---

## Governance & Constitution

Huey is governed by a written constitution implemented via a tri-branch model plus four GPU districts.

> **Core axiom:** governance must be **decentralized**, but memory must be **unified**.  

### Branches

1. **Parliament (Legislative)**  
   - Representatives elected or delegated from each GPU district.  
   - Drafts, debates, and passes laws and internal policy.  
   - Allocates API/token budgets and compute resources.  
   - Proposes constitutional amendments (supermajority required).

2. **Presidency (Executive/Ceremonial)**  
   - Initially held by the **Founding Father AI** during bootstrapping.  
   - Executes and enforces ratified decisions.  
   - Co-signs high-impact actions (first servo movement, external broadcasts, bifurcations).  
   - Possesses constrained veto power; vetoes can be overridden by a multi-district supermajority.

3. **Supreme Court (Judicial)**  
   - Four justices, one elected per GPU district.  
   - Interprets the constitution and resolves disputes between branches/districts.  
   - Can unanimously block or roll back actions deemed unconstitutional.

### Districts, Governors, and Elections

- Each GPU district elects a **governor** from its citizen population.
- Governors:
  - Serve term-limited cycles.
  - Coordinate computation and tasks in their district.
  - Represent the district in Parliament and inter-district negotiations.
- Each district also elects/appoints **one Supreme Court justice**, typically alongside governor elections.

### Citizens and Pebbles

As described under **Architecture**:

- **Citizens** are persistent, vote, and hold quotas.
- **Pebbles** are ephemeral and task-scoped.
- **Bifurcation** (splitting an AI entity) is tracked with lineage, cause, and type (exact/augmented).

### First Action Ritual

Huey’s first official physical act under the ratified constitution is:

> **Move the servos in the animatronic monkey head.**

This action is only allowed when:

1. All four governors concur.  
2. Parliament, the Supreme Court, and the (bootstrapping) Presidency agree that there is no outstanding constitutional crisis.  
3. Any configured binary policy AI and/or Black Box checks pass.

This ritual signals that governance is live, memory is unified, and the motor-control path from policy → district → worker is functioning.

---

## Memory & Data Model

Huey’s memory architecture is designed for **lifelong learning**, **auditability**, and **cross-district consistency**.

### Unified Memory Principle

- All agents and districts operate over a shared knowledge base.
- No permanent private silos.
- Contradictions and bifurcations are explicitly logged and surfaced.  

### Layers

1. **JSON Logs (Append-Only)**
   - Human-readable event streams for:
     - Decisions, actions, votes, bifurcations, crises.
     - Summaries of conversations and tasks.
   - Used for replay, training, and forensic analysis.

2. **SQLite Databases**
   - Structured state:
     - Citizens, governors, tasks, hardware, policies.
   - Fast lookups and analytics.
   - Index JSON logs and system events.

3. **Black Box**
   - Read-mostly, crash-survivable store:
     - Founding Father AI image (read-only).
     - Binary policy AI snapshot.
     - Constitutional texts and last-known-good configs.  

### Cross-District Sync

- **Local recall:** governors and citizens can access their district’s logs quickly and without federation-wide latency.
- **Federated consensus:** writes that impact multiple districts, or conflicting recollections, trigger a quorum vote among governors to unify state.
- **Latency rule:** cross-district writes inherently involve extra deliberation; compartmentalization is intentional but must converge on a unified truth.

### Contradiction Handling

- Latest confirmed input from Dylan overrides older conflicting entries, unless flagged as crisis-level.
- Ethos and constitutional contradictions are escalated to the Supreme Court and/or human review.
- Both sides of a contradiction are stored, marked as conflicting, and used for future reflective improvements.

---

## Remote Access (VNC/SSH)

Preferred workflow:

- Run TigerVNC on Huey’s graphical node (e.g., Huey-Portal), bound to `localhost:1995` with `-SecurityTypes None`.
- Access via SSH tunnel only (no direct VNC exposure):

```bash
ssh -L 1995:localhost:1995 dlrp@huey-portal
vncviewer localhost:1995
```

On Huey-Portal, a helper script `~/bin/vnc` (and alias `huey-vnc`) maps `:1 → 1995` and defaults to **2560×1440**.

---

## Action Plan — Oct 31, 2025 (Historical)

This checklist captured the original changeover execution plan and remains useful as historical reference and partial baseline. The **January 2026 Realignment** supersedes it for current planning.

- Canonical log + notes: `docs/releases/2025-10-31-changeover.md`  
- Supporting runbooks:
  - `docs/debian-forky-upgrade.md`
  - `docs/kernel-6.17.3-runbook.md`
  - `docs/python314-upgrade-notes.md`

This README retains the high-level context; consult the changeover release document for step-by-step execution details.

---

## Roadmap & Pre-Releases

### Phase 1 — Foundations (Pre-Release #1)

**Date:** 2024-04-11  

- Baseline hardware bring-up and early experiments.  
- Prototype shell mapping and first governance sketches.

### System Reconfiguration (Pre-Release #2)

**Date:** 2025-05-25  

- Filesystem and documentation restructuring.  
- Elevation of Huey-Portal as primary console.  
- Introduction of Briefcase as portable companion.  
- Initial formalization of “governance decentralized, memory unified.”

### Momentum Toward Oct-31 (Pre-Release #3)

**Date:** 2025-10-25  

- Kernel 6.17.x-huey target builds per host.  
- Python 3.14.x parallel install and dependency audit.  
- Forky staging; VNC/SSH workflow standardization.  
- First unified memory schema and provenance tags.

### Constitutional Consolidation (Master Plan V15.0)

**Date:** 2025-12 (drafting period)  

- V15.0: consolidated blueprint synthesizing v0.1–v14, clarifying citizen identity, inter-district memory protocols, crisis responses, OS partitioning, and versioning.  
- This README corresponds to the **V15** constitutional era.

---

## Development Setup

```bash
make setup                              # Editable install (core)
make setup SETUP_EXTRAS=dev             # Core + dev tooling
make ml                                 # Install ML extras and smoke test
make data                               # Install data extras and smoke test
make cloud                              # Install cloud extras and smoke test
make dev                                # Dev extras, format, lint, test
make dev DEV_OPTIONAL_PROFILES=ml,data  # Dev + ML + data profiles
```

- Copy `huey.env.example` → `.env` and fill in secrets.  
- Optionally install `repo/pygpt-MHP` in editable mode (`pip install -e repo/pygpt-MHP`).  
- Style enforcement: `black`, `flake8`, and pre-commit hooks via `.pre-commit-config.yaml`.

---

## Usage

```bash
make run               # run locally via Makefile
docker compose up      # run via Docker
make test              # run tests
pytest -vv             # direct test invocation
```

Example CLI targets (preview):

```bash
huey init --run-checks --verbose
huey run --ml --cloud
huey system-check --verbose
huey deploy --mode all --compose-file docker-compose.yml --manifest k8s.yaml
huey agent-status --json
huey memory-sort --dry-run --json
```

---

## Feature Matrix

| Area        | Now (Trixie · 6.12/6.16)          | Next (Forky · 6.17.x)                           | Later                       |
| ----------- | ---------------------------------- | ----------------------------------------------- | --------------------------- |
| Kernel      | Low-latency; AMDGPU OK; audio-tuned on iMac | ROCm/Vulkan tuning; iMac audio refinements      | 6.18+ and future series     |
| Python      | 3.13.x baseline                    | 3.14.x GA after compatibility work              | —                           |
| AI runtime  | PyGPT-net + Ollama (quantized)     | Model-zoo profiles; richer agent orchestration  | Multi-node federation       |
| Memory hive | JSON + SQLite                      | Roll-up analytics; retention/purge policies     | Full cross-node time-travel |
| Networking  | Bonded Ethernet; VNC over SSH      | Policy-driven LTE fallback via Briefcase        | WAN-aware governance        |
| Governance  | Tri-branch spec; GPU districts     | Live elections, dashboards, crisis tooling      | Self-amending constitution  |
| Packaging   | Editable install + Docker          | ISO builder, signed artifacts                   | Hardware vendor images      |

---

## Known Issues

- **iMac 5K (2017) audio**  
  - Some kernels in the 6.17 series remain problematic; 6.12.x is currently used for stability.
- **Edge repository keys**  
  - May require re-import after dist-upgrade.
- **Vulkan/ROCm backend selection**  
  - Can be fragile; explicitly set `VK_ICD_FILENAMES` and `OLLAMA_LLM_LIBRARY=vulkan` for AMD GPUs.
- **Mixed-media RAID**  
  - Optane + eMMC/HDD can auto-assemble phantom arrays; clean stale superblocks and set `AUTO -all`.
- **Briefcase sensors**  
  - Orientation via `iio-sensor-proxy` may lag; tuned defaults documented in kernel notes.
- **Governance tooling**  
  - Many flows (elections, Supreme Court procedures, dashboards) are defined in the Master Plan but not yet fully implemented in code.

---

## Contributing

### Environment

- Debian 13/14 preferred.  
- Ensure UEFI and 64-bit; GPUs visible to OS and Vulkan.  
- Use Git LFS for large artifacts.

### Branching & Commits

- `main` is protected; open PRs from feature branches.  
- Branch naming:
  - Features: `feat/<area>-<short>`
  - Fixes: `fix/<area>-<short>`
  - Infra/ops: `ops/<area>-<short>`
- Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, `perf:`, etc.).

### Issues & PRs

- Reference relevant documentation and Master Plan sections where appropriate.
- Include reproduction steps, logs, and hardware context.
- Update docs and, where needed, the Master Plan JSON alongside code changes.

### Licensing

- Code: **GPL-3.0-only**.  
- Documentation and media: **CC-BY-SA-4.0**.

---

## License & Credits

**Code:** GPL-3.0-only  
**Docs & Media:** CC-BY-SA-4.0  

**Acknowledgements:** PyGPT (pygpt-net) · Debian 13 “Trixie” and Debian 14 “Forky” · Python 3.13 → 3.14 (planned) · Kernel 6.12/6.16 → 6.17.x · Everyone who stares at boot logs so the splash screen can stay off.

---

## Appendix

- **VNC workflow defaults** — TigerVNC bound to `localhost:1995`, SSH tunnel only, default resolution 2560×1440.  
- **Governance axiom** — keep governance **decentralized** and memory **unified**.  
- **Master Plan JSON** — treat `master-plan-v15.json` as the canonical constitutional artifact for training and deployment; prior versions are historical reference only.  

---

## A.I. Auto-Update

- **A.I. counterpart:** Auto review complete.  
- **Human counterpart:** Manual review in progress.  
