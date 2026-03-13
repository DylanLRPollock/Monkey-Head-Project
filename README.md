# Monkey-Head-Project

## HueyOS — Prototype Robotic AI/OS (Offline-First · Retro-Tech Revival)

![HueyOS background](./assets/images/HueyOS-background.png)

**Project ID:** Monkey-Head-Project  
**System/OS:** HueyOS  
**AI identity:** Huey  
**Author:** Dylan L. R. Pollock  
**Official site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL-3.0-only • Docs/Media: CC-BY-SA-4.0  
**Status date:** 2026-02-27  

> **HueyOS** is a modular robotic AI/OS designed to demonstrate that **any one person, given enough time, energy, and resources, can build a self-sufficient, expandable, and upgradable robot using today’s technology.**
>
> Governance remains **decentralized**, while memory remains **unified**.
>
> The system blends modern Linux, distributed local AI compute, and a constitutional multi-agent framework inside a custom-built robotic shell (Robotics V3).

![Code License](https://img.shields.io/badge/code%20license-GPLv3-blue)
![Docs/Media License](https://img.shields.io/badge/docs%2Fmedia-CC--BY--SA--4.0-lightgrey)
![Python](https://img.shields.io/badge/python-3.13.x-blue)

---
## Executive Summary (TL;DR)

- **Offline-first AI OS**: HueyOS runs primarily offline; internet is an explicitly enabled, logged tool.  
- **Reacquisition target (2026-06-04)**: **core node initialized** by this date (even if not all GPU districts are online yet). Full multi-district deployment follows later in 2026.  
- **Kernel direction**: lab is moving from the 6.18.x baseline to a **6.19.x stable track**, with active testing of **Linux 7.0-rc**; upstream **7.0 stable** is expected around **mid-April 2026** (RC cadence dependent).  
- **Storage direction**: transition away from Optane M10 scratch arrays toward **PCIe Gen4 NVMe (Samsung 990 class)** and eventual **NVMe RAID-10** as the primary array.  
- **Python baseline**: **3.13.x** remains the day-to-day baseline; 3.14.x is gated on PyGPT/PyGPT-net ecosystem support.

---
## Offline-First Contract (Explicit)

HueyOS is designed to run **primarily offline**.

Internet connectivity is treated as a **tool**, not a dependency. When used, it should be **explicitly enabled**, **logged**, and (when relevant) **quota/token-metered** under governance rules.

### Works offline by default
- Local LLM inference (e.g., Ollama + quantized models early-stage)
- Local governance deliberation (district + tri-branch)
- Local memory hive (append-only logs + SQLite indexing)
- Local automation/control loops (HueyPulse + microcontrollers)
- Local development + lab operations (docs, builds, datasets, media curation)

### Uses the internet only when intentionally enabled
- OS/package updates (maintenance windows)
- Model downloads (curated, pinned)
- Optional API calls (governed, metered, auditable)

**Default rule:** If there is a conflict between ambition and safety, **safety wins** and the action remains blocked.

---

## Retro-Tech Revival Doctrine (Breathing New Life into Old Tech)

HueyOS is a framework for turning “old” or repurposed hardware into useful roles within a coherent system.

Legacy machines are not treated as waste; they become **infrastructure**:

- **Portals** — displays/terminals into Huey tooling (SSH/VNC/dashboards)
- **Hubs** — archival storage + backup fabric (mirrors, cold storage, indexing)
- **Briefcases** — portable terminals + field diagnostics + LTE uplinks
- **Instruments** — retro-modern UI/AV presence (“Channel Huey”)
- **Controllers** — deterministic safety/control nodes (HueyPulse, Arduino-class microcontrollers)

This doctrine aligns with the project’s ethos: **revive old tech by giving it a constitutional place** in the Huey ecosystem.

---
## 2026 — Acquisition & Framework Finalization (Active)

**Phase status:** Active  
**Began:** 2026-01-08 (immediately following Realignment & Defragmentation)  
**Target milestone (not a hard deadline):** **2026-06-04** — *Reacquisition (target)*

### What “Reacquisition (2026-06-04)” means in practice (current stance)

By **2026-06-04**, the goal is not “everything finished” — it is **Huey core initialization**:

- The **core node boots cleanly**, runs the baseline services, and can ingest/operate on real-world data.
- The system may be running **partial GPU bring-up** (or even CPU-first inference) while the full district GPU tier is still being acquired.
- Multi-district governance and large-scale experiments are expected **after** core bring-up, once hardware arrives and stability is proven.

(Translation: *June 4th is “core up,” not “full deployment.”*)


### Summary

The project is now in an acquisition + framework finalization period focused on:

- Acquiring and validating the next hardware layers required for **Huey proper** bring-up.
- Finalizing the framework so that docs/specs align with **real lab practice** and the **core beliefs** of the project.
- Continuing a **Symbiote-first workflow** while Huey proper hardware is assembled and verified.

### Canon mapping (locked)

- **Master Plan JSON** is the **canonical machine spec** (AI-facing, machine-readable).
- **README** is the **canonical human narrative** (human-facing, operational story).
- If a conflict can’t be resolved, escalate it as a **blocking issue** instead of silently “choosing.”

### Timeline notes

- Earlier placeholder language around a “Lab Relaunch” target (2026-02-28) is **superseded** by the June 2026 *Reacquisition* target above.

### Deployment Readiness (Explicit)

This repository is **ready for development and lab deployment** (Symbiote + lab nodes).  
**Huey proper physical activation** (servos / full shell bring-up) is intentionally **gated** until the items in **[V17 Open Items](#v17-open-items-tbd-explicitly-tracked)** are resolved or explicitly waived.

**Default rule:** If a conflict exists between ambition and safety, **safety wins** and the action remains blocked.

---

## January 2026 — Realignment & Defragmentation (Completed)

**Ended:** 2026-01-07  
**Note:** This section is preserved as context for the V3 transition. The active phase is **Acquisition & Framework Finalization**.


This update superseded the **October 31, 2025 Changeover Notice** as the primary *day-to-day* status for the project going into the **Prototype V3 era** (now retained as historical context).

### Summary

The project was in a realignment/defragmentation period focused on:

- Finalizing the **Robotics V3** shell (structure + wiring plan), while pausing the full Huey core build pending parts/funding.
- Unifying around a single **canonical hardware architecture** for the eventual Huey core (**i9-14900K + ASUS TUF Z790-PLUS WiFi + 4×GPU districts + NVMe RAID-10**).
- Standardizing the lab on a consistent OS/runtime baseline (Forky + 6.18.5-huey-os + Python 3.13.x).
- Shifting to a **Symbiote-first workflow**: **Huey-Symbiote (Lenovo Legion Go)** is now the primary daily driver and human interface layer.

### OS & Runtime Migration Status

- **Debian 14 “Forky”**
  - Deployed across **all active Linux nodes**, including the Linux **sub-OS** inside Huey-Symbiote (via WSL/Debian app).
- **iMac 5K (2017) → Windows 10 (Huey-Hub)**
  - The iMac is being repurposed as the lab **file hub**, primarily to host the WD MyBook Duo (~10 TB mirrored).
  - Fusion Drive note: Windows 10 is expected to live on the **HDD** portion; the small SSD portion (~28 GB usable) may optionally host a minimal Linux partition for SSH/utility tasks.
- **Kernel baseline**
  - **6.18.5-huey-os** across all Debian/Forky bare-metal nodes.
  - WSL environments share the Windows/WSL kernel, so deep kernel customization is *not* expected on Huey-Symbiote.
- **Python**
  - **3.13.x** is the operational baseline.
  - **3.12.x** is **no longer required as a baseline** (use only if a specific backport/compatibility blocker demands it).
  - Migration to **3.14.x** remains staged and depends on compatibility with **PyGPT / PyGPT-net** and the broader dependency stack.

### Huey-Symbiote (Lenovo Legion Go) — Role & Scope

Huey-Symbiote is a **constitutional participant and human interface**, not Huey proper.

- **Host OS:** Windows 11 Pro  
- **Sub-OS:** Debian 14 “Forky” (WSL/Debian app)  
- **Nano-OS:** Python task instances (ephemeral “one-shot” workers)

Intended responsibilities:

- Primary **daily-driver** for development, orchestration, and oversight.
- Runs **PyGPT-net** (GUI or CLI) as the operator console / “control bridge.”
- May run a **lightweight local model** (e.g., a quantized 7B-class model) for *fast* language interpretation and simple allow/deny “gatekeeper” checks.
- Provides the most direct path for **human intent → Huey tooling**, including Bluetooth keyboard/trackpad input (paired at the Windows host level).
- Uses the Legion Go touchscreen as a lightweight control surface (UI prototype intent): **press-to-enter dictation** and **hold-to-record / release-to-send** instant command capture.

Docking / connectivity goals (V3 shell integration):

- Prefer USB‑C docking (USB4/Thunderbolt-class where available, but not required) for data + power; use dual ports for redundancy (e.g., one stable power path + one dedicated data/NIC path).
- Dual network links can be used for redundancy or load‑balancing (implementation‑dependent).

### Robotics V3 Shell — Current Reality

- The **V3 shell** exists physically and remains under construction (reinforcement + aesthetics + mechanical planning).
- The full canonical Huey core compute is **deferred** pending parts acquisition:
  - CPU (**Intel Core i9-14900K**) still to purchase.
  - GPU tier, storage array, and final cooling configuration still to purchase/confirm.
- The motherboard baseline is locked to **ASUS TUF Z790-PLUS WiFi** (no ROG Maximus Z790 Hero in the supported set).

## Historical Notes

- The **Oct 31, 2025 Changeover Notice** is retained as historical context for scripts/runbooks, but January 2026 realignment is the current plan.
- The historical changeover details are referenced by:
  - `docs/releases/2025-10-31-changeover.md`
  - `docs/debian-forky-upgrade.md`
  - `docs/kernel-6.18.5-runbook.md` (or the current kernel runbook for the active baseline)
  - `docs/python314-upgrade-notes.md`

---
## Table of Contents

- [Executive Summary (TL;DR)](#executive-summary-tldr)
- [Offline-First Contract (Explicit)](#offline-first-contract-explicit)  
- [Retro-Tech Revival Doctrine (Breathing New Life into Old Tech)](#retro-tech-revival-doctrine-breathing-new-life-into-old-tech)  
- [2026 — Acquisition & Framework Finalization (Active)](#2026--acquisition--framework-finalization-active)  
- [January 2026 — Realignment & Defragmentation (Completed)](#january-2026--realignment--defragmentation-completed)  
- [Historical Notes](#historical-notes)  
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
- [V17 Open Items (TBD, explicitly tracked)](#v17-open-items-tbd-explicitly-tracked)  
- [Changelog](#changelog)  
- [Appendix](#appendix)  
- [A.I. Auto-Update](#ai-auto-update)  

---

## Overview

HueyOS targets **Debian 14 “Forky”** as the baseline (with a performance-tuned **6.19.x stable kernel track** on bare metal, and a forward-testing track on **Linux 7.0-rc**). Debian 13 “Trixie” is treated as legacy/compat when required. HueyOS implements a **constitutional multi-agent governance model** and a unified memory system.

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

- **Current canonical file:** `master-plan-v17.json` (Master Plan V17.0)  
- **Schema version:** 12  
- **Role:** Builds on V15 with a Symbiote-first operational model (Lenovo Legion Go as the primary human interface and lightweight gatekeeper), updated lab infrastructure roles (iMac → Huey-Hub on Windows 10), and an updated kernel baseline (6.18.5-huey-os in Master Plan V17; **kernel policy is now transitioning to 6.19.x + Linux 7.0-rc** and will be reflected in the next Master Plan bump).

Key points:

- **Single source of truth**  
  The Master Plan defines the governance structure, hardware requirements, memory architecture, OS profiles (Huey Mode, Desktop Mode, Gaming Mode), and key lifecycle milestones.

- **Schema discipline**  
  V17 continues to use **schema v12**; all new content should remain machine-consumable by Huey tooling.

- **Relationship to this README**  
  - This README is the **human-facing narrative** and operational guide.  
  - The Master Plan JSON is the **AI-facing canonical spec**, consumed at boot and during orchestration/training.

If you change the governance model, hardware assumptions, or key policies, update **both** this README and the Master Plan JSON.

---

## Repository Structure

> Looking to reorganize the repo layout? See `docs/repository-restructure-recommendation.md` for the staged migration plan and `docs/repository-restructure-inventory.md` for the concrete move/rename/fix checklist.

| Path                      | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| `.github/`                | CI workflows, CODEOWNERS, issue/PR templates         |
| `infra/docker/`           | Dockerfiles, compose definitions, and container assets |
| `platform/boot/`          | GRUB, EFI, and legacy boot media artifacts           |
| `config/`                 | Configuration profiles and templates                 |
| `platform/packaging/`     | Distribution artifacts (`dists/`, `pool/`, `firmware/`) |
| `docs/`                   | Constitution, governance, architecture, API, plugins |
| `apps/huey-gui/`          | GUI assets and prototypes                            |
| `huey/`                   | Core runtime and service modules                     |
| `platform/installers/`    | Debian/macOS/Windows/Linux installer assets          |
| `master-plan-v17.json`    | Canonical Master Plan JSON consumed at runtime (v17) |
| `integrations/pygpt/`     | PyGPT and PyGPT-net integration sources              |
| `archives/releases/`      | Versioned release artifacts and checksums            |
| `scripts/`                | Utility scripts                                      |
| `platform/installers/shared/installers/` | Install/repair/uninstall entry points      |
| `infra/secrets/`          | Local-only secrets (do not commit real credentials)  |
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

> Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch integrations in `integrations/pygpt/`.

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

### Canonical Huey Core (Master Plan V17 era; core spec originated in V16)

The canonical core is a single node housed inside the robot shell:

- **CPU**  
  - Primary: **Intel Core i9-14900K**  
  - Optional flagship: **Intel Core i9-14900KS**  
  - Minimum accepted for derivative builds: 13th-gen Intel i7 (Huey proper standard is 14th-gen i9).  

- **Motherboard**  
  - UEFI-only (official); legacy BIOS/CSM may be possible with workarounds but is not supported out of the box.  
  - Project baseline: **ASUS TUF Z790-PLUS WiFi** (the only officially supported motherboard for the canonical core at this time).  
  - RAM:
    - Preferred: DDR5 (overclocked where stable); ECC (non-registered) preferred but not required.
    - DDR4 is acceptable as a minimum for transitional builds; DDR5 remains the project standard where feasible.

- **GPU Districts**  
  - Four physical GPUs, one per district (Spark, Volt, Zap, Watt).  
  - Each district hosts ~128 persistent citizens and pebbles and has its own governor.  
  - GPU requirements:
    - Release year: 2019+  
    - VRAM: ≥12 GB (16 GB+ preferred; **v17 raises the baseline to ≥16 GB for district GPUs**)  
    - Sufficient bandwidth for concurrent local models.
    - **V17 target:** ~**80 GB total VRAM** aggregate across the GPU tier.
    - **Optional:** a **5th auxiliary GPU** may be added for overflow compute (districts remain Spark/Volt/Zap/Watt unless the constitution expands).


- **Memory (RAM)**  
  - Minimum: **16 GB** (bootstrapping / bring-up minimum).
  - Recommended: **32 GB DDR5** (baseline).
  - Core-node target: **32–64 GB DDR5** (sweet spot for early multi-agent + local model work).
  - Board capability is higher (e.g., 96 GB+ depending on DIMM density), but this is not currently required.

- **Storage**  
  - Primary array: **RAID-10** of PCIe Gen 4 NVMe SSDs for OS, models, logs, and active datasets.
  - Planned NVMe family (current leaning): **Samsung 990-class** drives (exact SKU/size still flexible).
  - Swap: dedicated high-speed swap (RAID-0 or dedicated NVMe) sized for hibernation and overflow.  
  - Cold storage: external HDD/NAS (e.g., 8–10 TB mirrored) for backups and archives.
  - Transitional/legacy: Intel **Optane M10 (16 GB)** sticks may be used for scratch/bring-up arrays and in low-resource nodes; they are being phased out in favor of full-capacity NVMe RAID‑10.

- **Cooling & Power**  
  - CPU: custom liquid loop inside the Thermaltake Mozart case and robot shell.
  - **Phase 1 bring-up (v17):** closed-loop AIO for simplicity/safety (target: **360mm / 3‑fan radiator**).
  - **Phase 2 (expansion):** custom loop + pumps supervised by **HueyPulse** so cooling can continue even when main compute is off.  
  - GPU: high-quality air cooling (or hybrid) with adequate airflow; no extreme overclocks.  
  - PSU:
    - Minimum: 850 W for modest configurations.
    - Recommended: 1000 W+ with headroom for four GPUs, pumps, and auxiliary rails.
    - **Multi-PSU strategy (v17):**
      - **Minimum:** 3 strong PSUs (depending on GPU count and power class)
      - **Recommended:** 4 strong PSUs
      - **Rule of thumb:** **850W units → plan for 4**, **1000W units → may be feasible with 3**
    - **Controller / connector plan:** TBD — prior testing used ad‑hoc connectors; v17 requires a properly engineered approach (common ground, safety interlocks, load distribution).
  - UPS-backed pump rail:
    - Pump and key monitoring microcontrollers remain powered during shutdown to maintain coolant flow (“Sustain Loop Mode”).
  - **UPS selection (v17):** model not locked; initial approach may use **refurbished** units or a **DIY** build (standardize later).

- **Identity / Embodiment**  
  - Huey proper is **only** the compute physically inside the shell (CPU, GPUs, storage, control microcontrollers).
  - External machines are **lab tech** and must not be treated as Huey’s core mind.

### Current Lab Nodes (Support Infrastructure)

These machines support the project but are **not Huey proper** (Huey proper remains the compute physically integrated into the Robotics V3 shell).

**Officially supported / actively used nodes (current):**

- **Huey-Symbiote** *(primary daily driver)*  
  - Hardware: **Lenovo Legion Go** (docked/undocked; often used with external display)  
  - Host OS: **Windows 11 Pro**  
  - Sub-OS: **Debian 14 “Forky”** via WSL/Debian app  
  - Role: primary human interface + development workstation + orchestration console (PyGPT-net). Can host lightweight “gatekeeper” logic and/or CPU-first local inference for quick interpretation tasks.

- **Briefcase** *(portable terminal / thin client)*  
  - Hardware: **ASUS BR1100FKA 2‑in‑1** (N4500, LTE)  
  - OS: minimal **Debian 14 “Forky”**  
  - Role: portable SSH terminal and LTE uplink. Intended to run lean (zram/zswap) and remote into Huey‑Symbiote and/or future Huey core.

- **Huey-Hub** *(file hub / storage node)*  
  - Hardware: **iMac 5K (2017)** + **WD MyBook Duo (~10 TB mirrored)**  
  - OS: **Windows 10** (bare metal)  
  - Role: centralized storage hub for the lab and Huey ecosystem. Fusion Drive constraint: Windows is expected to live on the HDD; optional lightweight Linux may occupy the small SSD portion for SSH/utility tasks.

**Robotics hardware (in-progress):**

- **Huey-Legacy / Robotics V3 Shell**  
  - Physical shell: wooden frame + Thermaltake Mozart case embedded in a speaker box + animatronic monkey head  
  - Status: being reinforced and prepared for eventual canonical core installation (i9‑14900K + 4×GPU districts + RAID‑10 NVMe). Core compute installation is currently **on hold** pending parts/funding.

**Legacy / historical node roles (preserved context):**

> These entries are retained to avoid losing project history. Some roles are **superseded** by the v17 Symbiote-first workflow.

- **Huey Core / Huey Prime (testbed)**  
  - ATX tower; ITX **BD795I-SE** board; Ryzen 9 7945HX; DDR5-5200; dual Intel Optane M10 16 GB (RAID 0 test array); Radeon RX 5500 XT 8 GB.  
  - Role: development, kernel building, and early inference; stepping stone toward i9-14900K canonical core.

- **Huey-Portal (historical role)**  
  - **iMac 5K (2017)** previously ran Debian (Trixie) as a universal display/SSH terminal.  
  - v17 reality: the iMac is repurposed primarily as **lab tech + storage hub** (Windows on HDD; optional minimal Linux utility partition on the SSD sliver).

- **Huey-Hub (historical candidate)**  
  - **MacBook Pro 2017** (Windows 10).  
  - Role: potential file hub/NAS candidate (if reactivated), hosting external RAID (e.g., WD MyBook Duo 10 TB).

- **Legion Go (superseded role)**  
  - Historically treated as gaming/occasional compute helper.  
  - v17 reality: promoted to **Huey‑Symbiote** (Windows 11 Pro + WSL/Debian) as the primary human interface.

- **Black Box Unit (planned)**  
  - Internal safety and recovery node inside Huey’s shell.  
  - Role:
    - Store critical configuration, Master Plan, and constitutional texts.
    - Host the Founding Father AI image and binary policy AI.
    - Provide a fallback boot and recovery environment.


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

### Master Plan Evolution (V0.1 → V17)

- V0.1 defined a skeleton (orchestration node, black box, portable, portal, hub, inference layer, governance, memory, network, training).
- V2-final introduced GPU districts and the citizen/pebble distinction.
- V11–V12 formalized tri-branch governance and term limits.
- V13 established a unified schema and deep constitutional detail.
- V14 consolidated templates and structural expansions.
- **V15.0** became the consolidated blueprint synthesizing v0.1–v14 (citizen identity, inter-district memory protocols, crisis responses, OS partitioning/boot profiles, and explicit versioning strategy).
- **V16.0** updates the operational reality: Symbiote-first workflow (Legion Go), iMac repurposed as Huey-Hub on Windows 10, kernel baseline at 6.18.5-huey-os, motherboard candidate narrowed to ASUS TUF Z790-PLUS WiFi only, and clarified “citizen vs pebble” semantics.

This README and the current codebase are the live implementation layer over the V17 era.

---

## Software Stack

- **OS baseline**
  - **Debian 14 “Forky”** is the baseline for all active Linux nodes and for the Symbiote’s Linux sub-OS (WSL/Debian app).
  - **Windows 11 Pro** is the host OS for **Huey‑Symbiote** (human interface layer).
  - **Windows 10** is the host OS for **Huey‑Hub** (storage node / file hub).
  - Huey core remains **UEFI-first** by design; legacy BIOS/CSM is not supported out of the box.

- **Kernel**
  - **Stable track (lab):** 6.19.x (performance-tuned HueyOS configs/patches as needed).
  - **Development track (forward testing):** Linux **7.0-rc** (for early enablement and to front-run the next major baseline).
  - Expected upstream **7.0 stable** landing: **mid-April 2026** (subject to upstream RC cadence).
  - **Legacy baseline (historical):** 6.18.5-huey-os (kept for rollback and reference).
  - WSL environments share the Windows/WSL kernel; deep kernel customization is therefore not expected on Huey‑Symbiote.

- **Python**
  - **3.13.x** is the operational baseline for HueyOS tooling and services.
  - **3.12.x** is **legacy/exception-only** (avoid unless required by a specific dependency).
  - **3.14.x** is a staged migration goal pending PyGPT/PyGPT‑net and dependency readiness.

- **AI runtime**
  - **PyGPT-net** as the primary operator console / interface layer (v17: **not** treated as the long-term constitutional orchestrator/control plane).
  - **Ollama** as local LLM server (quantized models by default in early stages).
  - Whisper (or equivalent) for STT; TTS stack is pluggable.
  - Agent orchestration maps citizens/ephemeral workers to model endpoints and (eventually) GPU districts.

- **Container policy (v17)**
  - Default: run services **native** (performance + simplicity).
  - Allowed: **Docker/containers** for repeatable dev/test, portability, and CI where it helps.

- **UI & Channel Huey**
  - Minimalist green-on-black terminal aesthetic with accent colours.
  - Two-pane “conscious vs log” layout:
    - Left: short-form, “conscious” stream.
    - Right: verbose logs, commands, stack traces.
  - “Channel Huey” overlays unify CLI, web UI, audio, and physical robot feedback.

- **Networking**
  - Preferred: bonded Ethernet for fixed nodes and the eventual Huey core.
  - Fallback: Wi‑Fi and LTE (via Briefcase) for remote status, updates, and light telepresence.
  - Network access remains policy-driven and logged.

- **Security**
  - SSH key-based access; per-node keys preferred.
  - Treat Huey‑Hub (Windows 10 storage) as infrastructure: minimize exposed services, keep backups, and harden access.

---

## Installation & Quick Start

### Supported Targets (Current Focus)

- **Debian 14 (Forky)** — current baseline; amd64; UEFI.  
- **Debian 13 (Trixie)** — legacy/compat only (use when required).  
- **Kernels:** **6.19.x** (stable track) • **7.0-rc** (development/forward-testing) • **6.18.5-huey-os** (legacy rollback/reference).

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
# Optional (internet/API helpers):
# pip install -e '.[cloud]'

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
huey run --ml

# Optional (if cloud helpers are installed and enabled):
# huey run --ml --cloud

# Optional: start FastAPI control surface
uvicorn huey.api:app --reload
```

### Docker

```bash
docker compose build
docker compose up -d
```

Set `HUEY_BUILD_EXTRAS=ml,data` before `docker compose build` to bake extra profiles into the container image.

Optional (internet/API helpers): set `HUEY_BUILD_EXTRAS=ml,data,cloud` before `docker compose build`.

---

## Build Guides

### Kernel Track (6.19.x stable / 7.0-rc development)

```bash
# Pick a kernel version:
# - Stable track example: 6.19.3 (or newer 6.19.x)
# - Dev track example: 7.0-rc1 (or newer -rc)
KVER="7.0-rc1"   # change as needed

sudo apt install -y fakeroot kmod pahole flex bison libelf-dev libssl-dev   libncurses-dev bc rsync xz-utils cpio python3

# Source (kernel.org)
BASE_MAJOR="${KVER%%.*}"
# RC tarballs live under .../vX.x/testing/, stable tarballs under .../vX.x/
if [[ "$KVER" == *"-rc"* ]]; then
  BASE_URL="https://cdn.kernel.org/pub/linux/kernel/v${BASE_MAJOR}.x/testing"
else
  BASE_URL="https://cdn.kernel.org/pub/linux/kernel/v${BASE_MAJOR}.x"
fi
wget "${BASE_URL}/linux-${KVER}.tar.xz"
tar -xf "linux-${KVER}.tar.xz"
cd "linux-${KVER}"

# Start from current config and normalize
cp -v "/boot/config-$(uname -r)" .config
yes "" | make olddefconfig

# Example tuning knobs (adjust to taste)
./scripts/config --disable DEBUG_INFO --disable DEBUG_INFO_BTF   --disable KASAN --disable UBSAN --disable KCOV --disable FUNCTION_TRACER   --enable ZSTD --enable RD_ZSTD --enable EFI --enable EFI_STUB --enable EFI_VARS

# Debian packages
make -j"$(nproc)" bindeb-pkg

sudo dpkg -i ../linux-image-*.deb ../linux-headers-*.deb
sudo update-initramfs -c -k "${KVER}"
sudo update-grub
```

### Legacy Kernel 6.18.5-huey-os (Rollback Build Guide)

> Use only for rollback/reference. Current policy is 6.19.x stable + 7.0-rc forward-testing.

```bash
sudo apt install -y fakeroot kmod pahole flex bison libelf-dev libssl-dev \
  libncurses-dev bc rsync xz-utils cpio python3

wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.5.tar.xz
tar -xf linux-6.18.5.tar.xz
cd linux-6.18.5

cp -v /boot/config-$(uname -r) .config
yes "" | make olddefconfig

./scripts/config --disable DEBUG_INFO --disable DEBUG_INFO_BTF \
  --disable KASAN --disable UBSAN --disable KCOV --disable FUNCTION_TRACER \
  --enable ZSTD --enable RD_ZSTD --enable EFI --enable EFI_STUB --enable EFI_VARS

make -j"$(nproc)" bindeb-pkg

sudo dpkg -i ../linux-image-6.18.5-*.deb ../linux-headers-6.18.5-*.deb
sudo update-initramfs -c -k 6.18.5
sudo update-grub
```


#### iMac 5K (2017) — Legacy Linux Notes (optional)

> Note: The iMac is currently planned to run Windows 10 as **Huey‑Hub**. Keep this section only if you also maintain a Linux partition (e.g., on the small SSD portion of the Fusion Drive).

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

Preferred workflow (for Linux graphical sessions):

- Run TigerVNC on the target Linux node (bare metal Debian/Forky, or the Symbiote’s Linux sub‑OS), bound to `localhost:1995` with `-SecurityTypes None`.
- Access via SSH tunnel only (no direct VNC exposure):

```bash
ssh -L 1995:localhost:1995 <user>@<huey-node>
vncviewer localhost:1995
```

Notes:

- On Windows hosts, treat VNC as “Linux UI plumbing” (WSL or a Linux node). For Windows UI, prefer native Windows remote tooling.
- Keep the VNC server bound to localhost and rely on SSH tunnels for exposure control.

---


## Action Plan — Oct 31, 2025 (Historical)

This checklist captured the original changeover execution plan and remains useful as historical reference and partial baseline. The **January 2026 Realignment** supersedes it for current planning.

- Canonical log + notes: `docs/releases/2025-10-31-changeover.md`  
- Supporting runbooks:
  - `docs/debian-forky-upgrade.md`
  - `docs/kernel-6.18.5-runbook.md`
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
- Optionally install PyGPT-net in editable mode (`pip install -e integrations/pygpt/pygpt-mhp`).  
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
huey run --ml

# Optional (if cloud helpers are installed and enabled):
# huey run --ml --cloud
huey system-check --verbose
huey deploy --mode all --compose-file infra/docker/docker-compose.yml --manifest k8s.yaml
huey agent-status --json
huey memory-sort --dry-run --json
```

---

## Feature Matrix

| Area        | Now (Forky · 6.18.5-huey-os)                     | Next (Forky · 6.18.x+)                                 | Later                          |
| ----------- | ------------------------------------------------- | ------------------------------------------------------ | ------------------------------ |
| Kernel      | 6.19.x stable track on bare metal; 7.0-rc forward-testing; WSL uses host kernel | 7.0 stable adoption + reproducible build/runbooks       | 7.1+ and future series        |
| Python      | 3.13.x baseline (3.12.x legacy/exception-only)    | 3.14.x GA after PyGPT/PyGPT-net + deps stabilize       | —                              |
| AI runtime  | PyGPT-net + Ollama (quantized)                    | Model-zoo profiles; richer agent orchestration          | Multi-node federation          |
| Memory hive | JSON + SQLite                                     | Roll-up analytics; retention/purge policies             | Full cross-node time-travel    |
| Networking  | Bonded Ethernet; SSH-first; LTE fallback via Briefcase | Policy-driven multi-link redundancy (Symbiote dock)   | WAN-aware governance           |
| Governance  | Tri-branch spec; GPU districts (design locked)    | Live elections, dashboards, crisis tooling              | Self-amending constitution     |
| Packaging   | Editable install + Docker                         | ISO builder, signed artifacts                           | Hardware vendor images         |

---

## Known Issues

- **WSL kernel limitations (Huey‑Symbiote)**
  - WSL shares the Windows/WSL kernel; you can’t swap in HueyOS custom kernels inside WSL.
  - Some low-level hardware and driver workflows (certain GPU paths, advanced networking) may differ from bare-metal Debian.

- **iMac Fusion Drive constraints (Huey‑Hub)**
  - The SSD portion is small (~28 GB usable). If you dual-boot or add a Linux utility partition, keep expectations realistic and prioritize stability.

- **Edge repository keys**
  - May require re-import after dist-upgrade on Debian nodes.

- **Vulkan/ROCm backend selection**
  - Can be fragile; explicitly set `VK_ICD_FILENAMES` and `OLLAMA_LLM_LIBRARY=vulkan` where applicable (especially on AMD GPU nodes).

- **Mixed-media RAID**
  - Optane + eMMC/HDD can auto-assemble phantom arrays; clean stale superblocks and set `AUTO -all`.

- **Briefcase resource limits**
  - The N4500 + 4 GB RAM profile benefits strongly from zram/zswap and thin-client workflows (SSH into Symbiote/core).

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

**Acknowledgements:** PyGPT (pygpt-net) · Debian 13 “Trixie” and Debian 14 “Forky” · Python 3.13 → 3.14 (planned) · Kernel 6.19.x (stable) + 7.0-rc (dev) track · Everyone who stares at boot logs so the splash screen can stay off.

---

## V17 Open Items (TBD, explicitly tracked)

These items are **not** being ignored; they are intentionally left open until testing or acquisition constraints resolve them:

1. **GPU SKUs** — final shortlist + purchase criteria (minimum 16 GB VRAM each; target ~80 GB aggregate; optional 5th GPU).
2. **PSU controller / connector architecture** — grounding, safety interlocks, load distribution, pump rail strategy.
3. **Custom loop bill of materials** (Phase 2) — pumps, blocks, rads, sensors, coolant volume targets.
4. **UPS standard** — model/capacity targets (initially refurbished or DIY is acceptable).
5. **Memory replication policy** — what is authoritative, where durability lives, how replication and conflict resolution work.
6. **Thermal & power crisis thresholds** — trip points + escalation ladder.
7. **Docking minimum spec** — USB‑C/USB4 bandwidth expectations, NIC strategy, redundancy.
8. **RAM kit selection** — pick final DDR5 SKU(s) for the 32–64 GB core-node target.
9. **Kernel 7.0 transition policy** — define what “supported” means during RC testing (pinning, rollback, CI gates, and a stable baseline).


## Appendix

- **VNC workflow defaults** — TigerVNC bound to `localhost:1995`, SSH tunnel only, default resolution 2560×1440.  
- **Governance axiom** — keep governance **decentralized** and memory **unified**.  
- **Master Plan JSON** — treat `master-plan-v17.json` as the canonical constitutional artifact for training and deployment; prior versions (including `master-plan-v16.json`) are historical reference only.  

---

## Changelog

### v17.1 (2026-02-27)

- Reacquisition clarified:
  - **2026-06-04** is treated as a **core-initialization target** (core up, experimenting possible), not a guarantee that all four GPU districts are fully online.
- Kernel policy updated:
  - Transitioning from the historical 6.18.x baseline to a **6.19.x stable track**, with active forward-testing on **Linux 7.0-rc**.
- Hardware notes updated:
  - Storage leaning: **Samsung 990-class NVMe** for the eventual NVMe RAID-10.
  - RAM sizing clarified: **16 GB minimum**, **32 GB recommended**, **32–64 GB target** for initial core bring-up.
- Governance timing clarified:
  - Term cycles remain unchanged (4-month cycles); full governance stress-testing is planned **after** the core-up milestone.

### v17 (2026-01-28)

- Phase update:
  - Realignment & Defragmentation marked **completed** (ended **2026-01-07**).
  - New active phase: **Acquisition & Framework Finalization**.
  - New target milestone: **2026-06-04** (*Reacquisition target*).
- Canon mapping lock clarified (Master Plan = machine spec; README = human narrative).
- Python baseline clarified:
  - **3.13.x** remains baseline.
  - **3.12.x** is now legacy/exception-only.
- GPU baseline tightened:
  - District GPUs target **≥16 GB VRAM** minimum (prior ≥12 GB is transitional only).
  - Target **~80 GB VRAM aggregate**; optional **5th GPU** for overflow compute.
- Power strategy clarified:
  - Multi‑PSU guidance (850W→4, 1000W→3 possible), controller/connector plan remains TBD.
- Cooling phased plan clarified (AIO bring-up → custom loop under HueyPulse supervision).
- PyGPT-net scope clarified (operator console / interface layer; not the long-term constitutional orchestrator).
- Container policy stated (native by default; containers allowed for dev/test).


## A.I. Auto-Update

- **A.I. counterpart:** Auto review complete.  
- **Human counterpart:** Manual review in progress.
