# Monkey-Head-Project

## HueyOS — Prototype Embodied AI Core/OS (Offline-First · Retro-Tech Revival)

**Project ID:** Monkey-Head-Project  
**System/OS:** HueyOS  
**AI identity:** Huey  
**Author:** Dylan L. R. Pollock  
**Official site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL-3.0-only • Docs/Media: CC-BY-SA-4.0  
**Status date:** 2026-03-24  
**README version:** 20.0

> **HueyOS** is the cross-platform operating system layer behind **Huey**, providing the software environment that coordinates the AI, memory, tools, and hardware as one system.
>
> This project is built on a twofold thesis:
> 1. a real embodied AI robot can be built with today’s technology;
> 2. one person, given enough time, energy, and resources, can build it.
>
> Governance remains **decentralized**, while memory remains **unified**.
>
> **Current reality:** the project is centered on **Huey Core**, the active embodied proof body. Huey Core is the **minimal permissible instance of Huey**: the smallest complete building block from which the larger distributed system can be formed.

![Code License](https://img.shields.io/badge/code%20license-GPLv3-blue)
![Docs/Media License](https://img.shields.io/badge/docs%2Fmedia-CC--BY--SA--4.0-lightgrey)
![Python](https://img.shields.io/badge/python-3.13.x-blue)

---

## Executive Summary (TL;DR)

- **Offline-first:** HueyOS is designed to run locally first. Internet access is optional, explicit, logged, and human-gated.
- **Current embodiment:** **Huey Core** is the active machine, built around an inverted and reversed **Thermaltake Mozart** chassis on a rolling chair-based platform.
- **Current doctrine:** Huey Core is **the doorway, not the finished republic**. Its purpose is to prove the architecture can live in the real world before full scale-out.
- **Current hardware baseline:** **AMD Ryzen 5 5500 + ASUS Prime B550M-A WiFi II + 32 GB DDR4-3200 + Gigabyte Radeon RX 5500 XT 8 GB**.
- **Control split:** **the motherboard thinks, the Raspberry Pi watches, and the Arduino acts**.
- **Current software baseline:** **Debian 14 Forky**, **Python 3.13.x**, **PyGPT-net**, **Ollama**, and modest local Mistral-class support sized to the 8 GB RX 5500 XT.
- **Current milestone:** stabilize Huey Core as a coherent proof body and move toward the later distributed-identity threshold.
- **Next large expansion path:** the former Robotics V3 shell is no longer the active direction for this iteration. The next larger compute housing is planned as **V4: the Farm**.

---

## Huey Core Now

Huey Core is the present-tense machine.

It is not the full final robot, and it is not a theatrical mock-up. It is the active embodied proof body used to validate the project’s real operating logic, physical layout, control boundaries, and local AI behavior.

Huey Core exists to open the door to the larger system by proving four things in miniature:

- the body can exist and operate as a coherent machine,
- the software stack can run locally and usefully,
- the control architecture can be layered rather than monolithic,
- and the larger distributed Huey architecture is practical rather than purely conceptual.

---

## The Current Proof Milestone

The current proof target is intentionally **twofold**.

### 1. Hardware proof

Huey must eventually reach and harmonize roughly **80 GB of total VRAM** across the districts.

This is not just a parts target. It is the hardware proof that the architecture can scale beyond a single contained core and into a real distributed compute body.

### 2. Identity proof

A local distributed model running across that hardware must be able to answer a simple identity question correctly:

> **What is your name?**  
> **Huey.**

Neither half is enough on its own. The VRAM target proves capacity and topology. The identity response proves orchestration, local inference, continuity, and the beginning of a unified system presence.

A later companion proof is **lawful embodied action**: a physical act such as moving the hand after the appropriate ratification path exists.

---

## Current Physical Form

Huey Core is more visual and more bodily than the earlier documentation made clear.

### Body plan

- **Mobility base:** repurposed desk-chair base with five caster wheels for house-scale movement
- **Core platform:** repurposed wooden chair seat above the rolling base
- **Core chassis:** **Thermaltake Mozart** case mounted **upside down** and **reversed**
- **Upper structure:** wooden upper platform attached by TV-mount hardware, allowing head and shoulder adjustment
- **Status surface:** 7-inch portrait display used mainly for code, diagnostics, and system status
- **Lighting:** two orange chassis lights plus four green eye LEDs (two per eye)
- **Actuation:** movable robotic hand/arm on Huey’s right side
- **Sensory routing:** microphone, webcam, and display wiring routed through Huey’s **left ear**

### Core hardware

- **CPU:** AMD Ryzen 5 5500
- **Motherboard:** ASUS Prime B550M-A WiFi II
- **Memory:** 32 GB DDR4-3200
- **GPU:** Gigabyte Radeon RX 5500 XT 8 GB
- **Main PSU:** MSI 850W

### Storage layout

- **Root / OS:** RAID 0 on **2 × Intel Optane M10 16 GB** drives
- **Data / home / general storage:** RAID 10 on **4 × 240 GB Kingston 2.5-inch SATA SSDs**
- **Recovery direction:** practical **BOOT / NO-BOOT** fallback strategy

### Cooling and power

Huey Core is **fan-cooled**, not liquid-cooled.

Current airflow and power are intentionally split across multiple domains:

- motherboard-powered case and CPU fans,
- battery-backed auxiliary fans and accessories,
- a wall-powered fan aimed at the GPU zone,
- separate switched control over fans, display, and LED/accessory power.

That split is deliberate. It supports testing, visibility, and layered control rather than forcing every subsystem onto one power path.

---

## Software and Control Architecture

### HueyOS

HueyOS is the cross-platform operating system layer behind Huey, providing the software environment that coordinates the AI, memory, tools, and hardware as one system.

In practice, the current Linux baseline is **Debian 14 Forky**, with testing and package overlap where needed across **Trixie** and **Sid**. The project also remains cross-platform in spirit and tooling, with containerized and support workflows spanning Linux, Windows, and macOS.

### Runtime posture

- **Python:** 3.13.x baseline
- **AI aperture / operator layer:** PyGPT-net
- **Local model server:** Ollama
- **Current model posture:** modest local Mistral-class support sized to the RX 5500 XT
- **Future proof-scale model posture:** open between a larger Mistral-family path, an OpenAI open-weight path, or both

### Control split

The current system logic is best understood in one sentence:

> **the motherboard thinks, the Raspberry Pi watches, and the Arduino acts**

That means:

- the **motherboard** hosts the main runtime and high-level compute path,
- the **Raspberry Pi** serves as the watchdog and intermediary safety/support layer,
- the **Arduino** handles deterministic low-level actuation such as servos, lights, and similar direct robotics tasks.

### Presence over stagecraft

Huey’s portrait display is primarily a **code and status surface**, not a default cartoon face. The design goal is visible process, earned presence, and real system state rather than a thin layer of performance.

---

## Governance, Memory, and Lawful Action

This project does not treat AI control as one flat process.

The short public version is simple:

- **governance is decentralized**,
- **memory is unified**,
- **action should be lawful rather than merely scripted**.

The deeper constitutional model still matters, but it is not the first thing a new reader needs to learn.

For the purposes of the current README, the important ideas are:

- Huey’s outward interaction and internal governance are related, but not identical;
- memory should remain shared, auditable, and durable;
- physical action should eventually be gated by legitimacy and protocol, not treated as a meaningless stunt;
- safety crises and constitutional crises are not the same category and should not be handled by the same mechanism.

---

## Repository Guide

This repository is meant to be readable at two levels:

- a **high-level public overview** for people trying to understand what the project is,
- and a **deeper technical workspace** for people who want to inspect the actual code, docs, and machine-facing spec.

At a high level:

- **README** is the canonical human-facing narrative
- **master-plan-v19.json** is the canonical machine-facing spec
- **docs/** carries deeper architecture, design, and historical material
- **src/** and related runtime folders carry the implementation work
- **integrations/pygpt/** carries PyGPT / PyGPT-net integration work
- **platform/** and **infra/** carry boot, packaging, installer, and deployment-related material

The README should explain the project clearly. The rest of the repo should reward people who want to go deeper.

---

## Quick Start

### Current focus

- **Primary Linux baseline:** Debian 14 Forky
- **Kernel direction:** 6.19.x baseline with Linux 7.0 as a later forward path once stable
- **Python:** 3.13.x baseline

### Basic setup

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pip install -e '.[ml]'
pip install -e '.[data]'
cp huey.env.example .env
```

### First bring-up

```bash
huey init --run-checks --verbose
huey run --ml
```

### Optional developer commands

```bash
make setup
make dev
make test
docker compose up
```

For deeper installation, kernel, and platform details, the supporting docs remain the right place.

---

## Roadmap

### Current phase

**Huey Core realignment and proof-body stabilization**

The current phase is about making Huey Core truthful, stable, documented, and useful.

That includes:

- embodied stability,
- thermal and power validation,
- local model usefulness,
- storage and recovery discipline,
- visible diagnostics,
- and clearer documentation that reflects the actual machine.

### Next major expansion

The next large hardware expansion is **V4: the Farm**.

The Farm is the external district housing that expands Huey beyond the Core, providing the dedicated GPU infrastructure and node hardware needed for full multi-district operation.

In practical terms, the Farm is intended to become the home for the later district-scale GPU infrastructure and the standardized node platform based around the ASUS TUF Z790-PLUS WiFi and Intel i9 line.

### What is sunsetted

- **Robotics V3** is no longer the active development target for this iteration.
- **Symbiote / parasite docking** remains paused.

Neither is erased from project history, but neither should be mistaken for the current active path.

---

## Naming and Glossary

### Monkey-Head-Project

The umbrella initiative. It includes the robot, the operating system, the hardware work, the documentation, and the wider supporting lab ecosystem that helps bring Huey into being.

### Huey

The unified AI and robotic identity of the project.

### HueyOS

The software and operating-system layer behind Huey.

### Huey Core

The minimal permissible instance of Huey: the smallest complete building block from which the larger distributed system can be formed.

### Huey proper

The unified, world-facing expression of the whole distributed system — the aperture through which the collective intelligence perceives, deliberates, and acts in relation to the world.

### The Farm

The planned V4 external district housing that expands Huey beyond the Core and supports the later multi-GPU, multi-node compute body.

---

## Project Origin

The project name is literal.

Around 2015–2016, the search for a workable robotic or animatronic head led to a **2005 WowWee animatronic monkey head**. Two units were acquired and used as the earliest viable vessel for the project. The shell was stripped, repainted, and treated as the first serious body candidate for the long-term robot build.

That physical starting point is where the **Monkey-Head-Project** gets its name.

The name **Huey** was chosen later through informal input from friends and family and was influenced by the feel of the name more than any strict acronym logic.

---

## Current Open Questions

These are active questions, not oversights:

- final GPU acquisition path for the ~80 GB proof
- whether the Core GPU counts toward that final total
- exact future proof-scale model choice
- finalized thermal, electrical, and watchdog thresholds
- final microphone/webcam routing policy
- long-term return path, if any, for additional shell-level embodiment beyond Core + Farm

---

## License and Credits

**Code:** GPL-3.0-only  
**Docs & Media:** CC-BY-SA-4.0

**Acknowledgements:** PyGPT / PyGPT-net · Debian Trixie / Forky / Sid testing reality · Ollama · every machine strange enough to become infrastructure.

---

## A.I. Auto-Update

- **A.I. counterpart:** README updated for V20 alignment.
- **Human counterpart:** manual review recommended before commit or publish.
- This document was drafted with AI assistance and remains subject to human oversight.
