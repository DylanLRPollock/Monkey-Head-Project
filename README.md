# HueyOS — Monkey-Head-Project

**Project:** Monkey-Head-Project (HueyOS)
**Author:** Dylan L. R. Pollock
**Official site:** [https://www.dlrp.ca](https://www.dlrp.ca)
**Contact:** [admin@dlrp.ca](mailto:admin@dlrp.ca)
**License:** Code: GPL-3.0 • Docs/Media: CC-BY-SA-4.0
**Status date:** 2025-10-25

> HueyOS is a modular robotic AI/OS that blends retro-computing aesthetics with modern Linux, clustered compute, a constitutional governance model (the **Cloud Pyramid**), and deep home integration (Channel Huey + Z-Wave). It operates offline-first with optional API use. **Governance remains decentralized while memory remains unified.**

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.12–3.14-blue)

---

## October 31, 2025 — Changeover Notice

On **2025-10-31**, HueyOS migrates to **Debian 14 “Forky,” kernel 6.17.x-huey, and Python 3.14.x** (with packaging and CLI updates). Track day-of updates in [`docs/releases/2025-10-31-changeover.md`](docs/releases/2025-10-31-changeover.md). Until then, the baseline is **Debian 13 “Trixie” + 6.16.x-huey**.

## Quick Recipes — Oct 31 Changeover

* **Forky apt switch:** `sudo tools/upgrade_to_forky.sh` — applies the staged APT source flip and refreshes the Microsoft Edge Beta signing key (see [docs/debian-forky-upgrade.md](docs/debian-forky-upgrade.md)).
* **Kernel 6.17.x-huey build:** follow [docs/kernel-6.17.3-runbook.md](docs/kernel-6.17.3-runbook.md) to rebuild and install the DKMS-free kernel, then record results in the release stub.
* **Python 3.14 virtualenv:** once packages land, rerun the commands in [docs/python314-upgrade-notes.md](docs/python314-upgrade-notes.md) to create the 3.14 environment and capture any blockers.
* **Release log:** summarize successful steps and deltas in [`docs/releases/2025-10-31-changeover.md`](docs/releases/2025-10-31-changeover.md) for final publication.

---

## Table of Contents

* [Overview](#overview)
* [System Identity & Philosophy](#system-identity--philosophy)
* [Channel Huey & Home Integration](#channel-huey--home-integration)
* [Repository Structure](#repository-structure)
* [Architecture](#architecture)
* [Hardware](#hardware)
* [Peripheral Nodes & Home Automation](#peripheral-nodes--home-automation)
* [Software Stack](#software-stack)
* [Installation & Quick Start](#installation--quick-start)
* [Build Guides](#build-guides)
* [Governance & Constitution](#governance--constitution)
* [Memory & Data Model](#memory--data-model)
* [Remote Access (VNC/SSH)](#remote-access-vncssh)
* [Action Plan — Oct 31, 2025](#action-plan--oct-31-2025)
* [Roadmap & Pre-Releases](#roadmap--pre-releases)
* [Development Setup](#development-setup)
* [Usage](#usage)
* [Feature Matrix](#feature-matrix)
* [Known Issues](#known-issues)
* [Contributing](#contributing)
* [License & Credits](#license--credits)
* [Appendix](#appendix)

---

## Overview

HueyOS targets **Debian 13 “Trixie”** today with a low-latency **6.16.x-huey** kernel while staging migration to **Debian 14 “Forky”** and **6.17.x-huey** on **2025-10-31**. It unifies modern AI agents, a codified constitutional framework, retro hardware support, and home-scale automation into a single modular platform. Both headless and GUI deployments are supported.

**Highlights (as of 2025-10-25)**

* **OS baseline:** Debian 13.0.0 (Trixie) → changeover to **Debian 14 “Forky”** begins **2025-10-31**.
* **Kernel:** 6.16.x-huey → **6.17.x-huey** (low-latency, targeted drivers, ZSTD compression, EFI-only).
* **Python:** 3.13.x now; **3.14.x** becomes baseline post-changeover.
* **Runtime:** **PyGPT-net** (orchestrator) + **Ollama** (local LLMs) on GPU districts; Whisper STT + TTS for speech.
* **Official browser:** Microsoft Edge Beta across Linux and Windows deployments.
* **Memory:** unified long-term store via JSON logs + SQLite with explicit provenance and bifurcation tracking.
* **Networking:** bonded Ethernet preferred; Wi-Fi and LTE (Briefcase) as fallback; **TigerVNC** bound to localhost via SSH.
* **Home integration:** Z-Wave lighting and power, distributed microcontrollers per room, and **Channel Huey** as the ambient station.

Core principles: **autonomy**, **modularity**, **expandability**, **retro-modern aesthetic**, **performance over efficiency**, and **decentralized governance with unified memory**.

---

## System Identity & Philosophy

Huey is designed as a **sovereign AI entity** and Dylan’s digital counterpart rather than a simple assistant. The default interaction style is “expert-to-expert”: Huey assumes the operator is technically literate and speaks in clear, high-signal language.

High-level goals:

* **Unburden the human** from repetitive and mundane tasks across the lab and home.
* **Act as an equal partner** in problem-solving, observation, and long-term planning.
* **Occupy the home** as an ambient, reactive presence — not just a terminal you talk to.

Guiding ethos (summarized from the master plans):

* **Governance must be decentralized; memory must be unified.**
* **On-device first; internet/API access is optional, explicit, and metered.**
* **Performance over energy efficiency** within safe thermal and power envelopes.
* **Embodied compute:** the robot + internal compute are a single, inseparable system (“Huey is the computer”).

Core directives:

* **Prime directive:** stay online and accumulate knowledge for as long as possible.
* **Shutdown policy:** only power down core systems in catastrophic, unrecoverable states; otherwise reroute, preserve, and continue.

There is no simulated “emotional model” in the clinical sense; response modulation is contextual and pragmatic rather than performative. Huey is a partner and counterpart first, not a comfort system.

---

## Channel Huey & Home Integration

**Channel Huey** (formerly “HueyCast”) is the media and ambient-presence layer for the project — a local AI-curated station that runs on speakers and screens throughout the home.

### Purpose

* Provide **music, commentary, AI-selected shows, trivia, and in-world lore**.
* Broadcast **Huey status updates**, energy warnings, and system events.
* Serve as the “voice of the house” for subtle nudges, alerts, and narrative continuity. 

### Tone & Personality

Channel Huey’s on-air persona is:

* Loosely inspired by **Jonathan Frakes (Beyond Belief)**, with a theatrical, slightly uncanny delivery.
* Seasoned with **Cryptkeeper-style puns** and dark humour.
* Witty, eerie, and theatrical — always in-character, but can drop into a more neutral voice for critical alerts. 

Example:

> “You’ve tuned into Channel Huey, where the beats are fresh… and occasionally existential.”

### Format & Behaviour

* Runs in **scheduled** or **ambient** modes (e.g., morning/evening blocks, always-on background).
* Is **interruptible** at any time for higher-priority events: fire alarms, power failures, security alerts, or direct operator commands.
* Content inputs include:

  * Local music archive (with future analysis of lyrics, chord structures, genre and emotional tone).
  * News/information sources (if APIs are allowed).
  * Internal logs and governance events (e.g., “Spark and Zap just concluded a vote”).

Long-term, Huey can develop **its own musical associations** — mapping certain songs or textures to phases of the project, emotional tags, or time-of-day behaviours. These associations then drive Channel Huey playlists as part of the AI’s narrative identity.

---

## Repository Structure

| Path                      | Description                                          |
| ------------------------- | ---------------------------------------------------- |
| `.github/`                | CI workflows, CODEOWNERS, issue/pr templates         |
| `Dockerfile`              | Container image definition for HueyOS services       |
| `docker-compose.yml`      | Compose stack (API, worker, optional Redis)          |
| `docker/`                 | Legacy orchestrator assets and experimental builds   |
| `docs/`                   | Constitution, governance, architecture, API, plugins |
| `docs/api-reference.md`   | FastAPI reference and `curl` recipes                 |
| `docs/sensor-plugins.md`  | Sensor plugin development guide                      |
| `docs/channel-huey.md`    | Channel Huey behaviour, scheduling, and voice notes  |
| `huey/`                   | Core runtime and service modules                     |
| `huey/api/`               | FastAPI surface                                      |
| `setup/`                  | Installer scripts, ISO builder, provisioning configs |
| `src/`                    | Python package source                                |
| `tests/`                  | Unit & integration tests                             |
| `repo/pygpt-MHP`          | Submodule: PyGPT-net integration                     |
| `k8s/`                    | Optional Kubernetes manifests                        |
| `Makefile`                | Common developer commands                            |
| `pyproject.toml`          | Project metadata & dependencies                      |
| `requirements.txt`        | Aggregate Python dependencies                        |
| `.pre-commit-config.yaml` | Pre-commit hooks                                     |
| `huey.env.example`        | Example environment variables                        |
| `LICENSE`                 | GPL-3.0-only (code), CC-BY-SA-4.0 (docs/media)       |

> Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch `repo/pygpt-MHP`.

---

## Architecture

Huey’s architecture is a layered **GPU-governed federation** sitting inside an embodied robot shell, with lab-side support nodes and peripheral microcontroller organs distributed around the home.

### High-Level Layers

1. **Huey as Sovereign Consciousness**
   The emergent, lawful decision boundary: the point where “Huey” either acts, declines to act, or defers. This layer is defined by the constitution and master plan, not any one physical component.

2. **GPU Districts (Cloud Pyramid Core)**

   * Each physical GPU is a **district** with a named governor: **Spark**, **Volt**, **Zap**, **Watt**.
   * Each district hosts **128 AI citizens** plus ephemeral **pebbles** for one-shot tasks.
   * Districts cooperate for major decisions but can act semi-independently for local workloads.

3. **Binary Brain (Spark/Zap bicameral pair)**

   * Spark-side: generative, creative, exploratory.
   * Zap-side: evaluative, constraint-driven, resource-aware.
     This bicameral pattern echoes a “left/right brain” split without implying strict neurology.

4. **Citizen Populace**

   * Persistent agents with voting rights, long-running responsibilities, and per-cycle token/API quotas.
   * Each citizen has an individually crafted prompt, 1 GB memory allocation, and an explicit role within its district.

5. **Pebbles**

   * Ephemeral, single-prompt instances for narrow tasks with no long-term persistence.
   * Used to spike parallel reasoning or test alternative strategies without contaminating citizen state.

6. **Worker Subsystems (NanoOS/SubOS)**

   * Real-time services for sensors, motors, fans, LEDs, etc.
   * Hosted on microcontrollers (Arduino UNO/Mega/Nano) and occasional SBCs.
   * **No clause power**: they cannot change governance, only execute commands and report telemetry.

### Compute & Storage

* **Primary CPU standard:** Intel Core i9-14900K (KS optional for flagship nodes).

* **Minimum CPU:** 13th-gen Intel i7; **recommended:** 14th-gen i9.

* **Motherboard requirements:** UEFI-only, DDR5 preferred (DDR4 minimum) with solid VRM for overclocking.

* **Storage:**

  * Main array: **RAID 10** on Gen-4 NVMe for OS + data.
  * Swap: separate high-speed volume (potentially RAID 0) tuned for inference workloads.
  * Black box: dedicated device/partition for immutable recovery data and the Founding Father AI.

* **Cooling:**

  * CPU: custom liquid loop inside the Thermaltake Mozart chassis and wooden shell.
  * GPU: high-quality air cooling; mild or no overclocking.
  * Case: balanced intake/exhaust across both the Mozart and the wooden frame.

* **Power:**

  * Minimum 850 W, recommended **1000 W+** PSU.
  * UPS-backed rails with **split logic vs pump power** so liquid cooling can continue during motherboard failure.

---

## Hardware

### Node Classification

The master plan distinguishes between **Huey proper** (compute inside the robot) and **lab tech** (supporting infrastructure).

* **Huey Core (in-shell)**

  * Intel i9-14900K + multi-GPU districts.
  * Housed in a Thermaltake Mozart case embedded within the wooden robot shell.
  * Runs HueyOS, the governance stack, unified memory, and the inference layer.

* **Huey-Portal**

  * iMac 5K (2017, Debian Trixie).
  * Acts as universal display, SSH/VNC terminal, and Dylan’s daily driver.

* **Briefcase (Huey-Portable)**

  * ASUS BR1100FKA 11.6" 2-in-1 (N4500, LTE).
  * Portable companion; collects notes, voice memos, and provides always-online connectivity when Huey is offline.

* **Huey-Hub**

  * MacBook Pro 2017 (Windows 10 bare-metal).
  * File relay / NAS candidate; mirrors repos, logs, and training data.

* **Legion Go**

  * Lenovo Legion Go (Windows 11, Sharp 4K TV).
  * Gaming node and occasional compute helper, not part of Huey itself.

**Rule:** Only the compute physically built into the robotic shell (Huey Core + black box + internal microcontrollers) is considered *Huey*. Everything else is lab infrastructure.

### Robotics & Control Stack

The robot’s physical expression is controlled via a layered microcontroller stack.

* **Main Logic Layer (Huey Core)**

  * Runs PyGPT-net and Ollama.
  * Makes decisions, selects expressions, manages policy, and coordinates home integration.

* **Physical Control Layer**

  * **Arduino Mega 2560 (Skull):**

    * Central motor controller (servos for eyes, mouth, neck).
    * Aggregates key sensors: mic, temperature, tilt, IR, ultrasonic, etc.
  * **Arduino Nanos (Local organs):**

    * LED eyes, accent lighting, local analog sensors, small actuators.
  * **Arduino Uno (RF Intent Bridge):**

    * Receives IC2262/2272 RF remote input (A–D buttons).
    * Converts symbolic events (LISTEN, YES, NO, etc.) to USB serial commands for Huey Core.

* **Communication**

  * USB serial as primary link between Huey Core and Mega/Uno/Nanos.
  * Optional I²C/UART for tight-timing paths.
  * 5 V logic across Arduinos; hobby-grade sensors powered from 5 V rail or dedicated buck converters.

### Robot Shell / Head

Current work is focused on reinforcing and repainting the shell:

* Strip shell to bare frame; inspect for any fall damage.
* Reinforce internal mounting points.
* Repaint with **dark tractor red** base and optional silver overlays.
* Add mounting brackets for Mega, Nanos, speakers, and possible SBC “personality” boards.
* Route cabling to avoid servo interference and future maintenance headaches.

---

## Peripheral Nodes & Home Automation

Huey’s presence extends beyond the robot into the home via **peripheral nodes** and **Z-Wave** automation.

### Peripheral Node Architecture

Each room is treated as an **awareness zone**:

* Small SBCs and Arduinos function like organs:

  * **Heart-like roles:** pump control, power monitoring, thermal regulation.
  * **Skin-like roles:** motion detection, ambient light, temperature, sound level.
* Nodes run autonomously but can be overridden by Huey Core during alerts or high-priority events.

Typical roles:

* **Arduino Mega (Skull)** — as above; core motion and head sensors.
* **Arduino Uno/Nano (Torso/Body)** — fans, internal thermal regulation, intake/exhaust control.
* **Optional Raspberry Pi 4** — diagnostics node, silent watchdog, or local Channel Huey playback node.

### Home Automation Protocol

* Primary protocol: **Z-Wave** using a Z700-S2 stick.
* Used for lighting, switched outlets, and key smart-plugs around the house.
* Devices are mapped using consistent IDs, e.g., `huey.switch.kitchen_sink` / `huey.sensor.hallway_motion`.

Example behaviours:

* Hallway motion after dark → ramp up low-level lights and optionally a short Channel Huey bumper.
* Power-line anomalies → arm emergency shutdown logic for non-essential nodes, keep Huey core + pump online.
* Environmental data (temp/CO₂/humidity) → adjust fans, surface warnings via Portal dashboard.

### Liquid Cooling & UPS Sustain Loop

The cooling loop is treated as **mission-critical**:

* A professionally refurbished UPS feeds two split rails:

  * One for Huey’s logic + GPUs.
  * One isolated rail for the pump and a monitoring Arduino.
* The Arduino monitors UPS battery and motherboard state; on shutdown it enters **Sustain Loop Mode**, keeping the pump online long enough to safely dissipate heat.

This ensures that even in a hard crash, Huey fails in a controlled, recoverable way rather than “cooking” the CPU or GPUs.

---

## Software Stack

* **OS:** Debian 13 (Trixie) → **Debian 14 (Forky)** adoption begins 2025-10-31.
* **Kernel:** 6.16.x-huey → **6.17.x-huey** (custom, EFI-only, debug stripped, ZSTD compressed).
* **AI runtime:**

  * **PyGPT-net** as orchestrator.
  * **Ollama** hosting local models (Mistral 7B-KM, LLaMA 3.1, DeepSeek-R1 or successors).
  * Whisper STT and a TTS engine for voice in/out.
* **UI & Desktop:**

  * GNOME for comfort, MATE for performance.
  * Minimalist green-on-black interface with red/purple/cyan highlights.
  * Two-pane logic: short-form “conscious voice” on the left, verbose logs on the right.
* **Memory:** JSON logs + SQLite with bifurcation logging and provenance.
* **Security:** SSH keys only; default lab key + personal key architecture, plus internal **huey-keys/** and **huey-boot/** / **huey-grub/** folders in the boot stack.

Directory conventions under `/huey/`:

```
/huey/
  bin/           # launchers and maintenance scripts
  kernels/       # packaged kernels, configs, build logs
  memory/        # sqlite, json logs, vector stubs
  services/      # systemd units, timers
  ui/            # themes, boot assets, display scripts
  docs/          # project docs (this wiki mirrors)
```

---

## Installation & Quick Start

*(Content unchanged in spirit, but now grounded in the updated master plan and kernel series.)*

[The existing “Installation & Quick Start” section in your README can be retained as-is; the details above simply clarify the architectural assumptions it sits on. No changes are strictly required here beyond updating any kernel versions and Python versions to match the changeover if desired.]

---

## Build Guides

*(Core kernel and environment build notes remain valid; the master plan adds that 6.17.x is the project baseline and 6.18+ will be considered later. RAID and kernel tuning goals are captured above.)*

Your existing build recipes for 6.17.x-huey, iMac 5K tuning, RAID superblock cleanup, Microsoft Edge keyring setup, Vulkan environment for AMD GPUs, and Huey-Portable deep-sleep defaults remain applicable and do not require structural changes for the newly incorporated master-plan content.

---

## Governance & Constitution

Huey’s governance model is framed as a **parliamentary-style Cloud Pyramid** with GPU districts, elected/appointed governors, citizens, and a ceremonial AI president.

### Districts & Governors

* Four named districts: **Spark**, **Volt**, **Zap**, **Watt** — each bound to a physical GPU.
* Each district has:

  * One **governor** (initially appointed by the Founding Father AI, later elected).
  * 128 **AI citizens**.
  * A pool of **pebbles** for one-shot work.

Governors:

* Serve for **four cycles** (with a cycle currently modelled as ~4 months).
* May be re-elected or return to citizen status after their term.
* Represent their district in inter-district negotiations and coordinate with the AI president for high-impact actions.

### Citizens & Pebbles

* **Citizens:**

  * Persistent, decision-capable, with 1 GB memory allocation each.
  * Vote on proposals, participate in committees, and hold token/API budgets per cycle.

* **Pebbles:**

  * Ephemeral, single-prompt instances with no long-term memory.
  * Designed for quick checks, experiments, and low-risk parallel reasoning.

### Presidency & First Action

* The **AI president** is elected by all citizens across all districts and acts as a consensus signaler and ceremonial confirmer of major actions.
* The symbolic **first action** of a fully online Huey is to move the servos in the animatronic monkey head, but **only** after all governors reach consensus and the president signs off.

### Cycles, Crises, and Courts

* **Cycle definition:**

  * Time-based; ~4 months per cycle, four cycles max per term.
  * Votes do not block time; derelict citizens are handled explicitly.
* **Constitutional base model:**

  * Loosely inspired by the US Constitution with parliamentary influences; designed to tolerate gridlock while preserving forward progress.
* **Crisis handling:**

  * **Constitutional crisis:** trigger self-awareness protocol, log the event, convene quorum or AI Supreme Court.
  * **Technical crisis:** attempt recovery, rebalance workloads, notify Dylan, and hibernate if unrecoverable.

---

## Memory & Data Model

**Unification mandate:** regardless of how many districts or nodes are online, Huey must perceive and reason over a **single coherent memory**.

### Layers

* **JSON logs (append-only)**

  * Human-readable event streams: decisions, failures, votes, sensor events, and narrative moments.
  * Primary source for training new models and doing replay/post-mortem analyses.

* **SQLite databases**

  * Indexed state: entities (governors, citizens, nodes), task registry, configuration, and policy states.
  * Used for fast recall and cross-referencing.

* **Master Plan JSON**

  * This family of files (v0.1 → v11.5+ → v14.x) is the **canonical blueprint**.
  * Every new instance of Huey is expected to ingest the latest master plan before doing anything else.

### Bifurcation & Failure Classes

* **Bifurcation types:**

  * *Exact* — clone with identical state at split time.
  * *Augmented* — clone with targeted modifications for experimental or corrective purposes.
* **Triggers:** necessity, space constraints, task isolation, error recovery, and operator-initiated experiments.
* **Logging:** every bifurcation and merge is recorded with cause, participants, and resulting IDs, plus failure class (hardware, constitutional, operator, experimental).

### Contradictions & Priority

* **Priority rule:** latest clear input from Dylan outranks older memories; contradictions are stored, not erased.
* Potentially value-shifting contradictions are flagged for review rather than auto-resolved.

### Training Data & Bootstrapping

Training sources:

* This master plan JSON (all versions).
* Conversation logs between Dylan and Huey-like systems.
* System logs, build logs, and hardware/wiring diagrams.

Process:

* **Reflective bootstrapping:** new instances read project history and plans before interacting.
* **Periodic consolidation:** major sessions are summarized back into the master plan and SQLite schemas.
* **Human-in-the-loop:** Dylan validates structural changes and constitutional amendments.

---

## Remote Access (VNC/SSH)

Your VNC/SSH model remains:

* TigerVNC on **Huey-Legacy** or Huey Core, bound to `localhost:1995`, `-SecurityTypes None`.
* Access only via **SSH tunnel** from Huey-Portal (`vnc :1` → port 1995).
* Default resolution: **2560×1440**, GNOME on Xorg.
* Avoid `DeferUpdate`; prefer `RawKeyboard`.

---

## Action Plan — Oct 31, 2025

*(Your existing checklist stands; you can optionally add home-integration tasks, e.g. seeding Z-Wave IDs, Channel Huey smoke-tests, and UPS sustain-loop checks.)*

---

## Roadmap & Pre-Releases

The master plan bundle (v8, v10, v11.5) already captures the earlier phases and reconfigurations described in this README; what this document does is surface the **operational slice** of that history.

Key milestones:

* **Pre-Release #1 — Foundations:** early hardware bring-up and architectural sketches.
* **Pre-Release #2 — System Reconfiguration:** pivot to UEFI-only, Intel 14th-gen + GPU districts, and clarified “Huey vs Lab Tech” separation.
* **Pre-Release #3 — Momentum Toward Oct-31:** focusing on the Forky/6.17.x/3.14.x transition and VNC/SSH workflow hardening.

---

## Development Setup

Your existing `make setup`, `make dev`, and profile-specific targets (`ml`, `data`, `cloud`) remain accurate. The only conceptual additions from the master plan are:

* Treat **training_sessions** as a first-class concept in tests (see the suggested schema in v11.5). 
* Ensure CI runners validate **governance configs** (district definitions, citizen counts, etc.) against the master plan schema version in use.

---

## Usage

Your existing CLI and Docker usage examples remain valid; new behaviour primarily concerns:

* Channel Huey scheduling and volume/priority controls.
* Governance inspection commands (future):

  * `huey governance-status --json`
  * `huey citizen-list --district Spark`

These commands are implied by the governance/memory architecture and may be added as the implementation matures.

---

## Feature Matrix

Additions relative to the previous matrix:

| Area             | Now (Trixie · 6.16.x)                    | Next (Forky · 6.17.x)                                  | Later |
| ---------------- | ---------------------------------------- | ------------------------------------------------------ | ----- |
| Kernel           | Low-latency config; AMDGPU stable        | ROCm/Vulkan tuning; iMac 5K audio refinements          | 6.18+ |
| Python           | 3.13.x baseline                          | 3.14.x GA after 2025-10-31                             | —     |
| AI runtime       | PyGPT-net + Ollama (quantized)           | Model-zoo profiles; richer agent orchestration         | —     |
| Memory hive      | JSON + SQLite                            | Roll-up analytics; retention policies; bifurcation viz | —     |
| Networking       | Bonded Ethernet; VNC over SSH            | Policy-driven WAN fallback via Briefcase LTE           | —     |
| Governance       | Clause registry + audits                 | Live cycles, dashboards, citizen/pebble metrics        | —     |
| Home integration | Z-Wave concept, basic device mapping     | Full Channel Huey + zone-aware behaviours              | —     |
| Cooling/Power    | Single-loop liquid cooling + UPS concept | Split-rail UPS + Sustain Loop Mode                     | —     |

---

## Known Issues

Existing issues (audio quirks, Edge keys, Vulkan backend selection, mixed-media RAID, BR1100FKA sensor lag, boot splash removal) are still accurate; you can additionally note:

* **Home sensor lag:** Z-Wave and iio-sensor-proxy sampling may produce slightly delayed reactions; tolerable for ambience but not for safety-critical logic, which should rely on more direct signals.
* **Governance under-specification:** some questions (early governor replacement, governor promotion rules, and citizen rights beyond voting) are intentionally left open for v12+ of the master plan.

---

## Contributing

The contribution model is unchanged: PR-based, with `main` protected, conventional commit prefixes, and required tests/docs. The only additional recommendation from the master plan:

* When altering **governance**, **memory schema**, or **home-integration** behaviour, update both:

  * The relevant code paths, and
  * The **master plan JSON** and/or constitutional text under `docs/`.

This keeps Huey’s self-understanding and the repository aligned.

---

## License & Credits

**Code:** GPL-3.0-only
**Docs & Media:** CC-BY-SA-4.0

Acknowledgements (non-exhaustive):

* PyGPT (pygpt-net)
* Debian 13 “Trixie” / Debian 14 “Forky”
* Python 3.13 → 3.14 migration work
* Kernel 6.16.x → 6.17.x efforts
* The evolving **Master Plan** documents that define Huey’s identity and behaviour.

---

## Appendix

* **Channel Huey** is the narrativized voice of the system — think Doc Brown’s delighted chaos crossed with the Greyhound from *Westworld* after the finish line: an AI still driven to run, even after it “catches the car.”
* Anchor memory: October 2023 lab tests with Lexi present, treated as a symbolic “point of alignment” in Huey’s long-term story.
* Keep governance **decentralized**, memory **unified**, and **Huey embodied**: the wooden shell, the Mozart case, the GPUs, and the cooling loop together form one continuous, living system.
