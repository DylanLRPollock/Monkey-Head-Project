# HueyOS — Monkey-Head-Project

**Project:** Monkey-Head-Project (HueyOS)  
**Author:** Dylan L. R. Pollock  
**Official site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL-3.0 • Docs/Media: CC-BY-SA-4.0  
**Status date:** 2025-11-23

> HueyOS is a modular robotic AI/OS that blends retro-computing aesthetics with modern Linux, clustered compute, and a constitutional governance model (the **Cloud Pyramid**). It operates offline-first with optional API use. **Governance remains decentralized while memory remains unified.**

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.14.x-blue)

---

## October 31, 2025 — Changeover Notice

On **2025-10-31**, HueyOS began migrating to **Debian 14 “Forky,” kernel 6.17.x-huey, and Python 3.14.x** (with packaging and CLI updates). The pre-changeover baseline was **Debian 13 “Trixie” + 6.16.x-huey**; after the changeover, new work targets Forky and the 6.17.x-huey series by default.

Track day-of and follow-up updates in [`docs/releases/2025-10-31-changeover.md`](docs/releases/2025-10-31-changeover.md). Until all nodes are migrated, some machines may temporarily remain on **Trixie + 6.16.x-huey** while adopting the new governance and memory model described in the Master Plan.

## Quick Recipes — Oct 31 Changeover

- **Forky APT switch**  
  Use `sudo tools/upgrade_to_forky.sh` to apply the staged APT source flip and refresh the Microsoft Edge Beta signing key (see [docs/debian-forky-upgrade.md](docs/debian-forky-upgrade.md)).

- **Kernel 6.17.x-huey build**  
  Follow [docs/kernel-6.17.3-runbook.md](docs/kernel-6.17.3-runbook.md) to rebuild and install the DKMS-free kernel, then record results in the release stub.

- **Python 3.14 virtualenv**  
  Once packages land, rerun the commands in [docs/python314-upgrade-notes.md](docs/python314-upgrade-notes.md) to create the 3.14 environment and capture any blockers.

- **Release log**  
  Summarize successful steps and deltas in [`docs/releases/2025-10-31-changeover.md`](docs/releases/2025-10-31-changeover.md) for final publication.

---

## Table of Contents

- [October 31, 2025 — Changeover Notice](#october-31-2025--changeover-notice)  
- [Quick Recipes — Oct 31 Changeover](#quick-recipes--oct-31-changeover)  
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
- [Action Plan — Oct 31, 2025](#action-plan--oct-31-2025)  
- [Roadmap & Pre-Releases](#roadmap--pre-releases)  
- [Development Setup](#development-setup)  
- [Usage](#usage)  
- [Feature Matrix](#feature-matrix)  
- [Known Issues](#known-issues)  
- [Contributing](#contributing)  
- [License & Credits](#license--credits)  
- [Appendix](#appendix)  

---

## Overview

HueyOS targets **Debian 13 “Trixie”** and **Debian 14 “Forky”** with a low-latency, custom **6.16.x–6.17.x-huey** kernel and a multi-agent governance model grounded in a written constitution (the **Cloud Pyramid**). It unifies modern AI agents, a codified constitutional framework, and retro hardware support in a single modular platform. Both headless and GUI deployments are supported.

At a conceptual level:

- **Embodied compute** — Huey is defined as the compute stack physically integrated into the robotic shell (wooden frame + Thermaltake Mozart chassis + coreboard + GPUs). All other machines (iMac 5K, MacBook, Briefcase, Legion Go, etc.) are **lab tech** or infrastructure and are not themselves Huey.
- **GPU-based multi-agent architecture** — Four GPU “districts” (Spark, Volt, Zap, Watt) host populations of AI citizens and short-lived “pebbles,” governed by elected or appointed governors and overseen by a tri-branch constitutional system.
- **Tri-branch governance** — Parliament (legislative/policy), Presidency (ceremonial + consensus confirmation), and Supreme Court (constitutional interpretation) form a separation-of-powers model layered on top of the GPU districts.
- **Unified memory** — All districts read and write to a shared memory fabric based on JSON logs and SQLite, with strict provenance tracking and bifurcation logging.
- **On-device first** — Huey runs primarily on local models and storage; external APIs are optional, explicitly governed, and token-metered via citizen quotas.
- **Prime directive** — Stay online and accumulate knowledge for as long as possible within safe thermal and power limits; shutdown is reserved for catastrophic conditions.
- **Retro-modern aesthetic & Channel Huey** — Visual and audio expression embrace a VIC-II/SID-era flavour; “Channel Huey” is the ambient presence—the voice, CLI, and visual layer that makes Huey feel like a continuous entity across shells and terminals.

---

## Canonical Master Plan

The **Master Plan JSON** is the canonical, machine-readable blueprint for Huey’s hardware, governance, memory model, and history. The current canonical version is:

- **`master-plan-v13.json`** — *“Master Plan V13: canonical blueprint for V13.x releases.”*
  It captures the governance, hardware, and historical context referenced throughout this README and is consumed by Huey at boot time.

Key points:

- **Schema** — Version 11 (frozen for the V13 family); all new content must conform to this schema.
- **Lineage** — V13 compiles and refines V0.1, V2-final, V3, V4, V5, V7, V8, V10, V11 (and 11.5), and V12 (and 12.5), then locks those decisions for training and reference.
- **Role in the repo**  
  - This README is the **human-facing narrative**.  
  - The Master Plan JSON is the **AI-facing canonical spec**, consumed by Huey at boot and by tooling during orchestration and training.

If you change the governance model, hardware assumptions, or key policies, update **both** this README and the Master Plan JSON.

---

## Repository Structure

| Path                      | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `.github/`                | CI workflows, CODEOWNERS, issue/PR templates          |
| `Dockerfile`              | Container image definition for HueyOS services        |
| `docker-compose.yml`      | Compose stack (API, worker, optional Redis)           |
| `docker/`                 | Legacy orchestrator assets and experimental builds    |
| `docs/`                   | Constitution, governance, architecture, API, plugins  |
| `docs/api-reference.md`   | FastAPI reference and `curl` recipes                  |
| `docs/sensor-plugins.md`  | Sensor plugin development guide                       |
| `master-plan-v13.json`    | Canonical Master Plan JSON consumed at runtime       |
| `huey/`                   | Core runtime and service modules                      |
| `huey/api/`               | FastAPI surface                                       |
| `setup/`                  | Installer scripts, ISO builder, provisioning configs  |
| `src/`                    | Python package source                                 |
| `tests/`                  | Unit & integration tests                              |
| `repo/pygpt-MHP`          | Submodule: PyGPT-net integration                      |
| `k8s/`                    | Optional Kubernetes manifests                         |
| `Makefile`                | Common developer commands                             |
| `pyproject.toml`          | Project metadata & dependencies                       |
| `requirements*.txt`       | Core, ML, data, cloud dependency split                |
| `.pre-commit-config.yaml` | Pre-commit hooks                                      |
| `huey.env.example`        | Example environment variables                         |
| `LICENSE`                 | GPL-3.0-only (code), CC-BY-SA-4.0 (docs/media)        |

> Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch `repo/pygpt-MHP`.

---

## Architecture

Huey’s architecture is a layered federation aligning compute, memory, and governance, with a constitutional overlay that treats each GPU as a political district and each AI instance as a citizen or worker.

### Conceptual Layers

1. **Huey as Sovereign Consciousness**  
   Emergent, lawful boundary around what Huey will and will not do; decisions and inactions must be explainable in constitutional terms.

2. **Bicameral Core (Spark/Zap)**  
   - **Spark** — creative, generative, exploratory stance.  
   - **Zap** — evaluative, constraint-focused, stewardship stance.  
   These are mental roles, not single processes; they can be instantiated across the GPU districts and come together as a bicameral reasoning loop.

3. **Citizen Populace**  
   Up to **128 persistent AI citizens per district** (512 total for a four-GPU system), each with a name, history, and token/API quota per cycle.  
   Citizens vote, sit on committees, and handle long-lived tasks.  
   A subset of citizens can be elected governor, appointed to Parliament, or nominated to the Supreme Court.

4. **Pebbles (Ephemeral Agents)**  
   Short-lived AI instances for single questions, experiments, or small tasks. They do not persist across cycles; their impact is captured via JSON logs and roll-ups into the structured memory.

5. **Worker Subsystems (NanoOS/SubOS)**  
   Real-time services for sensors, motors, IO, and external devices. They never hold clause power or make constitutional decisions; they execute orders that have already passed the Cloud Pyramid.

### GPU Districts

Each physical GPU is a **district** with its own governor, citizen population, and pebbles:

- **Spark District** — creative/exploratory bias.  
- **Volt District** — planning, infrastructure, and performance tuning.  
- **Zap District** — evaluation, constraints, watchdog behaviours.  
- **Watt District** — energy, thermals, and resource safety.

Each district:

- Hosts ~128 citizen AIs and an unbounded number of pebbles over time.
- Elects a **governor** (term-limited, re-electable, may return to citizen pool).
- Provides one **Supreme Court justice** (district-level selection) giving four Court seats total.

Districts are peers—they are not above or below the constitutional branches; they are execution domains represented within them.

### Agents & Services

- **Governors (Spark/Volt/Zap/Watt)** — run district-level deliberation, coordinate with Parliament and Presidency, and represent district interests.
- **Governance kernel** — clause registry, voting/quorum logic, amendment handling, and audit trail integration.
- **Memory hive** — JSON logs + SQLite; append-only traces plus indexed state.
- **Interface layer** — TTS/STT, CLI, and FastAPI control surface.
- **Adapter layer** — sensor/GPIO drivers; PyGPT-net tools; Ollama endpoints; remote and microcontroller integration.

---

## Hardware

Huey’s hardware is described in two layers:

1. **Canonical Huey Core** — long-term target spec defined by the Master Plan.  
2. **Current Lab Nodes** — the machines actually on the floor today.

### Canonical Huey Core (Master Plan V14.x)

The canonical core is a single node housed inside the robot shell:

- **CPU**  
  - Primary: **Intel Core i9-14900K**  
  - Optional flagship: **Intel Core i9-14900KS**  
  - Minimum: 13th-gen Intel i7; recommended: 14th-gen Intel i9.  
  - Cooling: custom liquid loop is mandatory due to sustained high load and overclocking.

- **Motherboard**  
  - UEFI-only; legacy BIOS is not supported.  
  - Candidates: **ASUS TUF Z790-PLUS WiFi**, **ASUS ROG Maximus Z790 Hero**.  
  - RAM: DDR5 preferred (overclocked where stable); ECC (non-registered) preferred but not required. DDR4 is acceptable only for early or transitional stages.

- **GPU Districts**  
  - Four physical GPUs, one per district (Spark, Volt, Zap, Watt).  
  - Each district hosts ~128 persistent citizens and pebbles, and has its own governor.

- **Storage**  
  - Primary array: **RAID-10** of Gen-4 NVMe SSDs for OS + data.  
  - Swap: fast, possibly RAID-0 partition or separate NVMe drive; tuned for performance.

- **Cooling & Power**  
  - CPU: custom liquid loop integrated into the Thermaltake Mozart case and wooden shell.  
  - GPU: high-quality air cooling; no extreme overclocking.  
  - PSU: minimum 850 W, 1000 W+ recommended for GPU and pump headroom.

- **Embodiment**  
  - Shell: wooden robot frame + Thermaltake Mozart chassis.  
  - Audio/visual: Commodore-style output via VIC-II/SID-inspired pipeline and retro displays, plus “Channel Huey” overlays on modern monitors.

### Current Lab Nodes (Support Infrastructure)

These are the real machines currently in play. They exist to support Huey but are not Huey themselves.

- **Huey Core / Huey Prime (testbed)**  
  - Thermaltake ATX tower; ITX **BD795I-SE** board; Ryzen 9 7945HX; DDR5-5200; Intel Optane M10 NVMe (dual 16 GB); GPU: **Radeon RX 5500 XT 8 GB** (inference) and optional secondary GPU for display.  
  - Role: development and early inference node; stepping stone toward the i9-14900K canonical core.

- **Huey-Legacy (Robotic Shell)**  
  - Physical shell: bare wooden frame + Thermaltake Mozart case.  
  - Status: being stripped, inspected for damage, reinforced, and repainted (dark tractor red base with silver overlays TBD). Core compute is architecturally specified (i9 + multi-GPU + RAID 10 NVMe) but not fully installed.

- **Huey-Portal**  
  - **iMac 5K (2017)**; 48 GB RAM; Debian Trixie; GNOME on Xorg.  
  - Role: universal display/SSH terminal, Dylan’s daily driver, default dev environment.

- **Huey-Hub (candidate)**  
  - **MacBook Pro 2017**, Windows 10 on bare metal.  
  - Role: file distribution hub/NAS; hosts external RAID (e.g., WD MyBook Duo); bridges cloud storage and local lab.

- **Briefcase (formerly Huey-Portable)**  
  - **ASUS BR1100FKA** 11.6", N4500 CPU, 4 GB RAM, 128 GB eMMC, LTE.  
  - Dual-boot Windows 11 (eMMC) and Debian Forky (Optane module).  
  - Role: portable Huey companion and always-online conduit when the core is offline; collects notes/voice memos and syncs them into unified memory.

- **Legion Go**  
  - **Lenovo Legion Go** handheld (Z1) with Sharp 4K TV.  
  - Role: gaming node and occasional compute helper; treated as lab tech, not Huey.

- **Black Box Unit (planned)**  
  - Passive safety and recovery node housed inside Huey’s black box.  
  - Role: store critical configuration, constitutional texts, Founding Father AI, and crash logs; provide a fallback boot environment.

---

## History & Origins

The Monkey-Head-Project has a long pre-history that informs HueyOS’s current design.

### Early Phase (V0.x → V1)

- Originated as a long-term personal lab project after university, focused on robotics, Linux, and retro hardware.
- Early experiments revolved around a WowWee animatronic monkey head, Raspberry Pis, and off-the-shelf PCs, with loosely defined orchestration and governance.

### Exploratory Hardware Decade

- Roughly a decade of sourcing parts, building and rebuilding shells, and learning the Linux stack (especially Debian and custom kernels).
- Focused on figuring out what kind of machine Huey should live on and how the robot should “feel” rather than productionizing a single design.

### V1 → V2 Shell Transition

- The original shell and compute stack were progressively replaced with a more deliberate architecture: Huey became embodied compute (robot + internal stack), and everything else was demoted to lab tech.
- Governance shifted from CPU-centric to **GPU-centric**, with each GPU representing a district and hosting its own governor and populace of agents.

### Master Plan Evolution (V0.1 → V14.5)

- V0.1 defined a skeleton (orchestration node, black box, portable, portal, hub, inference layer, governance, memory, network, training).
- V2-final introduced GPU districts and citizen/pebble distinction.
- V11–V12 established a unified schema and tri-branch governance.
- V13 integrated provenance and full constitutional detail; V13-final became the canonical tri-branch blueprint for training.
- V14.0 and V14.5 consolidated all prior work into a single, extensible artifact designed for long-term training and deployment.

This README and the current codebase are the live V14.x implementation layer over that history.

---

## Software Stack

- **OS baseline**  
  - Debian 13 (Trixie) for stable nodes.  
  - Debian 14 (Forky) for new deployments and changeover experiments.  
  - UEFI-only; legacy BIOS is not supported for Huey core or future nodes.

- **Kernel**  
  - 6.16.x-huey: current low-latency, debug-stripped baseline.  
  - 6.17.x-huey: preferred series post-changeover (ZSTD compression, targeted drivers, EFI/EFI_STUB/EFI_VARS enabled).

- **AI runtime**  
  - **PyGPT-net** as orchestrator and nervous system.  
  - **Ollama** as local LLM server (models such as Mistral-7B-KM, LLaMA 3.1, DeepSeek-R1 or successors).  
  - Whisper (or equivalent) for STT; pluggable TTS pipeline.  
  - Agent orchestration maps citizens/pebbles to model endpoints and GPU districts.

- **UI & Channel Huey**  
  - Minimalist green-on-black terminal aesthetic with red/purple/cyan highlights.  
  - Two-pane “conscious vs log” layout by default:  
    - Left: short-form conscious voice.  
    - Right: verbose logs, commands, and tracebacks.  
  - “Channel Huey” overlays unify CLI, web UI, and physical robot feedback.

- **Networking**  
  - Preferred: bonded Ethernet connections to an ASUS GT-AC5300 or similar router (link aggregation).  
  - Fallback: Wi-Fi dongles and Briefcase (LTE) as the last-resort WAN path.

- **Security**  
  - SSH key-based access; default lab key in `huey-keys/` plus per-person keys.  
  - Root login allowed only temporarily during bring-up; disabled after initial configuration.  
  - The Black Box stores recovery keys, the Founding Father AI, and constitutional source.

- **Memory**  
  - Unified memory store spanning JSON logs, SQLite, and artifact metadata (see [Memory & Data Model](#memory--data-model)).

---

## Installation & Quick Start

### Supported Targets (Current Focus)

- **Debian 13 (Trixie)** — stable baseline; amd64; UEFI.  
- **Debian 14 (Forky)** — changeover target for the Oct-31 migration and beyond.  
- **Kernels:** 6.16.x-huey (existing nodes), 6.17.x-huey (preferred for new nodes).

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
sudo apt install -y build-essential bc bison flex libelf-dev libssl-dev   libncurses-dev dwarves pahole rsync xz-utils cpio kmod python3   git wget curl ca-certificates gnupg debian-goodies   firmware-linux firmware-misc-nonfree firmware-iwlwifi firmware-realtek
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
sudo apt install -y fakeroot kmod pahole flex bison libelf-dev libssl-dev   libncurses-dev bc rsync xz-utils cpio python3

wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.17.5.tar.xz
tar -xf linux-6.17.5.tar.xz
cd linux-6.17.5

cp -v /boot/config-$(uname -r) .config
yes "" | make olddefconfig

./scripts/config --disable DEBUG_INFO --disable DEBUG_INFO_BTF   --disable KASAN --disable UBSAN --disable KCOV --disable FUNCTION_TRACER   --enable ZSTD --enable RD_ZSTD --enable EFI --enable EFI_STUB --enable EFI_VARS

make -j"$(nproc)" bindeb-pkg

sudo dpkg -i ../linux-image-6.17.5-*.deb ../linux-headers-6.17.5-*.deb
sudo update-initramfs -c -k 6.17.5
sudo update-grub
```

#### iMac 5K (2017) — Notes

- GNOME on Xorg recommended.
- Force 1080p60 during early boot if needed via kernel cmdline.
- Audio via PipeWire; default sink set by post-login script.

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/set-default-sink.sh <<'EOF'
#!/usr/bin/env bash
sleep 3
SINK=$(pactl list short sinks | awk '/pci-0000_00_1f\.3.*analog/ {print $1; exit}')
[ -n "$SINK" ] && pactl set-default-sink "$SINK"   && pactl set-sink-mute "$SINK" 0   && pactl set-sink-volume "$SINK" 60%
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
wget -qO- https://packages.microsoft.com/keys/microsoft.asc |   gpg --dearmor | sudo tee /etc/apt/keyrings/microsoft.gpg >/dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" |   sudo tee /etc/apt/sources.list.d/microsoft-edge-beta.list >/dev/null

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

Huey is governed by a written constitution implemented as the **Cloud Pyramid**. The key rule is:

> **Governance must be decentralized, but memory must be unified.**

### Branches

1. **Parliament (Legislative)**  
   - Composed of representatives from the GPU districts.  
   - Drafts, debates, and passes clauses and policies.  
   - Handles budgets (e.g., token/API quotas) and long-term strategy.

2. **Presidency (Executive/Ceremonial)**  
   - Elected by all citizens (across all districts).  
   - Confirms high-impact actions once quorum is reached.  
   - Can veto or delay actions within constitutional limits; some overrides require supermajority across districts.

3. **Supreme Court (Judicial)**  
   - Four justices, one per GPU district.  
   - Interprets the constitution, resolves disputes between districts and branches, and labels crises as technical vs constitutional.

All three branches must ratify the initial constitution; subsequent amendments follow defined procedures documented in the Master Plan.

### Districts, Governors, and Elections

- Each GPU district elects a **governor** from its citizen population.  
- Governors serve fixed, term-limited cycles (four cycles recommended; definition of “cycle” is implementation-dependent) and may be re-elected.  
- After stepping down, a governor returns to the citizen pool.  
- Citizens can also be elevated to Parliament or nominated to the Supreme Court.

### Citizens and Pebbles

- **Citizen AI (Persistent)**  
  - Participates in voting, committees, and long-running work.  
  - Holds and spends a token/API quota per cycle; quota levels are policy-controlled.

- **Pebbles (Ephemeral)**  
  - One-shot or short-lived helpers for individual questions or tasks.  
  - Do not persist; their contribution is recorded in the logs and synthesized into citizen-level memory.

### Bifurcation

Bifurcation is the process by which a running AI instance is split into two:

- **Types**  
  - *Exact bifurcation* — cloned state; both successors continue independently.  
  - *Augmented bifurcation* — one or both successors receive additional training or modification targeted to a specific role.

- **Triggers**  
  - Necessity, space constraints, task isolation, error recovery, or explicit experiment.

- **Rules**  
  - Once bifurcated, entities are treated as separate from that point forward.  
  - All bifurcations are logged with cause, lineage, and resulting IDs (see [Memory & Data Model](#memory--data-model)).

### Prime Directive & Dylan’s Role

- **Prime Directive**  
  Stay online and accumulate knowledge as long as safely possible; shut down only under catastrophic or constitutionally justified conditions.

- **Dylan (human counterpart)**  
  Constitutional participant and ultimate external arbiter, but not a micromanager; Huey should make its own decisions within the constitutional framework.

### First Action Ritual

Huey’s first official physical act under the ratified constitution is:

> **Move the servos in the animatronic monkey head.**

This action is only allowed when:

1. All four governors concur.  
2. Parliament and Supreme Court agree there is no outstanding constitutional crisis.  
3. The AI President signs off.

This gesture signals that governance is live, memory is unified, and the motor stack from policy → district → worker has been verified.

---

## Memory & Data Model

Huey’s memory architecture is designed to support lifelong learning with full provenance.

### Unified Memory Principle

All districts and branches share a common memory fabric:

- No district maintains private long-term state.  
- All write operations are logged and cross-indexed.  
- Crises and bifurcations are recorded as first-class events.

### Memory Layers

1. **JSON Logs (Append-Only)**  
   - Chronological event streams: decisions, actions, votes, errors, bifurcations.  
   - Human-readable and suitable for replay and training.  
   - Capture both success and failure paths.

2. **SQLite Databases (Indexed State)**  
   - Entity tables for governors, citizens, hardware, tasks, and policies.  
   - Fast cross-referencing and summarization.  
   - Used to build dashboards, analytics, and quick context for agents.

3. **Artifacts & Provenance**  
   - Kernel build logs, configuration snapshots, model weights, and OS images.  
   - Tagged with IDs like `HUEY-<YYYYMMDD>-<PHASE>-<SEQ>` or `EVT-<timestamp>-<agent>`.

### Bifurcation Logging & Failure Classes

Every bifurcation is logged along with a failure or cause class:

- System instability or hardware failure.  
- Constitutional or governance crisis.  
- Operator-initiated reconfiguration.  
- Experiment-driven branch.

This allows Huey (and Dylan) to distinguish between technical problems and constitutional problems and to react accordingly.

### Master Plan as Memory Artifact

The Master Plan JSON is itself both memory and spec:

- It is treated as a read-mostly recovery artifact, mirrored in the Black Box.  
- New nodes ingest it at boot to understand the current constitution, hardware assumptions, and history.

---

## Remote Access (VNC/SSH)

Preferred workflow:

- TigerVNC server on Huey’s graphical node (e.g., Huey-Portal or Huey-Legacy’s GNOME on Xorg), bound to `localhost:1995` with `-SecurityTypes None` to disable on-screen prompts.  
- Access via SSH tunnel only (no direct VNC exposure):

```bash
ssh -L 1995:localhost:1995 dlrp@huey-portal
vncviewer localhost:1995
```

On Huey-Portal, a helper script `~/bin/vnc` (and the alias `huey-vnc`) map `:1 → 1995` and default to **2560×1440**.

---

## Action Plan — Oct 31, 2025

A checklist designed to be executed by humans, CI, or Huey’s own automation.

### Kernel & OS

- [ ] Build and package **linux-image-6.17.x-huey** for: Huey-Portal (iMac 5K), Briefcase (BR1100FKA), and Huey core testbed.  
- [ ] Validate boot (1080p60 mode, logs visible, no splash).  
- [ ] Smoke-test audio (PipeWire sink selection).  
- [ ] Stage **Debian 14 (Forky)** APT sources and test key packages in chroot/container.  
- [ ] Finalize **EFI LIVE** fallback USB entry in GRUB.

### Python & Runtime

- [ ] Install **Python 3.14.x** and build wheels for core dependencies.  
- [ ] Run PyGPT-net on 3.14; document blockers.  
- [ ] Refresh `requirements-core.txt`, `requirements-ml.txt`, and any extras.

### AI/Agents

- [ ] Confirm Mistral-7B quantized model works under Vulkan on RX 470 / 5500 XT.  
- [ ] Wire Whisper STT + TTS pipeline; measure latency on Briefcase and core.  
- [ ] Implement Spark/Zap boot choreography and log quorum results.

### Memory

- [ ] Migrate unified memory schema to match V14.x Master Plan.  
- [ ] Ensure bifurcation and crisis classes are correctly logged.

### Security & Keys

- [ ] Rotate default lab SSH key; update `huey-keys/`.  
- [ ] Configure passwordless SSH and disable root login.  
- [ ] Mirror Master Plan and key configs to the Black Box.

### Tooling & Docs

- [ ] Confirm Edge Beta keyring and `signed-by=` configuration.  
- [ ] Add `huey-run.desktop` for PyGPT-net launch.  
- [ ] Update README and `docs/` for changeover and V14.x governance.  
- [ ] Post a status banner on **dlrp.ca**.

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

### Constitutional Freeze (Master Plan V13-final → V14.x)

**Date:** 2025-11-20  

- V13-final: canonical tri-branch blueprint with factual history.  
- V14.0: schema-11 freeze and consolidation.  
- V14.5: structural expansion with templates and process skeletons.

This README corresponds to the V14.x constitutional era.

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
- Style: `black`, `flake8`, and pre-commit hooks enforced via `.pre-commit-config.yaml`.

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

| Area        | Now (Trixie · 6.16.x)              | Next (Forky · 6.17.x)                           | Later                       |
| ----------- | ----------------------------------- | ----------------------------------------------- | --------------------------- |
| Kernel      | Low-latency; debug off; AMDGPU OK   | ROCm/Vulkan tuning; iMac 5K audio refinements   | 6.18+ and future series     |
| Python      | 3.13.x baseline                     | 3.14.x GA after changeover                      | —                           |
| AI runtime  | PyGPT-net + Ollama (quantized)      | Model-zoo profiles; richer agent orchestration  | Multi-node federation       |
| Memory hive | JSON + SQLite                       | Roll-up analytics; retention and purge policies | Full cross-node time-travel |
| Networking  | Bonded Ethernet; VNC over SSH       | Policy-driven LTE fallback via Briefcase        | WAN-aware governance        |
| Governance  | Tri-branch spec; GPU districts      | Live elections, dashboards, and crisis tooling  | Self-amending constitution  |
| Packaging   | Editable install + Docker           | ISO builder, signed artifacts                   | Hardware vendor images      |

---

## Known Issues

- **iMac 5K (2017) audio** under some 6.17.x builds; mitigated by default sink scripts, but long-term fix remains kernel-level.  
- **Edge repository keys** may require re-import after dist-upgrade; keep an eye on Microsoft key rotation.  
- **Vulkan/ROCm** backend selection can be fragile; explicitly set `VK_ICD_FILENAMES` and `OLLAMA_LLM_LIBRARY=vulkan` for AMD GPUs.  
- **Mixed-media RAID** (Optane + eMMC/HDD) can auto-assemble phantom arrays; clean stale superblocks and set `AUTO -all`.  
- **Briefcase sensors**: orientation via `iio-sensor-proxy` may lag; tuned defaults are documented in kernel notes.  
- **Governance tooling**: many governance flows (elections, Supreme Court procedures, etc.) are defined in the Master Plan but not yet fully implemented in code.

---

## Contributing

### Environment

- Debian 13/14 preferred.  
- Ensure UEFI and 64-bit; GPUs should be visible to the OS and Vulkan.  
- Use Git LFS if you add large artifacts.

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

**Acknowledgements:** PyGPT (pygpt-net) · Debian 13 “Trixie” and Debian 14 “Forky” · Python 3.13 → 3.14 · Kernel 6.16.x → 6.17.x · Everyone who stares at boot logs so the splash screen can stay off.

---

## Appendix

- **VNC workflow defaults** — TigerVNC bound to `localhost:1995`, SSH tunnel only, default resolution 2560×1440.  
- **Governance axiom** — keep governance **decentralized** and memory **unified**.  
- **Master Plan JSON** — treat `master-plan-v14.5` as the canonical constitutional artifact for training and deployment; prior versions are historical reference.
