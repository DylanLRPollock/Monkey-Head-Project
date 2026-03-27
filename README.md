# Monkey-Head-Project

## HueyOS — Prototype Embodied AI Core/OS (Offline-First · Retro-Tech Revival)

**Project ID:** Monkey-Head-Project  
**System/OS:** HueyOS  
**AI identity:** Huey  
**Author:** Dylan L. R. Pollock  
**Official site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL-3.0-only • Docs/Media: CC-BY-SA-4.0  
**Status date:** 2026-03-27  
**README version:** 23.0

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
- **Control split:** **the motherboard thinks, the Pi watches and brokers, and the Arduino senses and acts**.
- **Current interaction edge:** **RF remote -> YK04 receiver -> Arduino Uno -> Raspberry Pi 4 -> Huey Core**.
- **Current software baseline:** **Debian 14 Forky**, **Python 3.13.x**, **PyGPT-net**, **Ollama**, and modest local Mistral-class support sized to the 8 GB RX 5500 XT.
- **Current proof target:** reach the first **unified roughly 80 GB VRAM** local identity milestone without prematurely fracturing the pooled compute body.
- **Current boot posture:** **let Debian speak**. Huey Core should boot truthfully and visibly, with verbose bring-up and live diagnostic/status output rather than a fake polished splash.
- **Current A/V routing posture:** for the first proof milestone, microphone and camera remain simplest when routed **directly to the motherboard**, while later Pi mediation stays optional.
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

Huey must eventually reach and harmonize roughly **80 GB of total VRAM** across the later compute body.

This is not just a parts target. It is the hardware proof that the architecture can scale beyond a single contained core and into a real pooled compute organism.

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
- **Status surface:** 7-inch portrait display owned by the Pi / HueyPulse layer for code, diagnostics, and live body-state
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

That split is deliberate. It supports testing, visibility, and layered control rather than forcing every subsystem onto one power path. In the current direction, the Pi, display, and support/control stack live on the persistent accessory side so the body never feels completely asleep.

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

> **the motherboard thinks, the Pi watches and brokers, and the Arduino senses and acts**

That means:

- the **motherboard** hosts Huey Core proper, local models, PyGPT-net-facing interaction, and high-level interpretation,
- the **Raspberry Pi 4** serves as the always-on HueyPulse-like watchdog, body-state monitor, interaction broker, and portrait-display owner,
- the **Arduino Uno** observes low-level electrical and RF events and drives bounded deterministic outputs such as LEDs, relays, and simple actuation.

### Huey Pulse and edge interaction

In the current build, the Raspberry Pi role is no longer just a future support node. It is the active **always-on connective layer** inside Huey Core.

Its practical jobs are:

- keeping track of body-state, switch-state, thermals, and service-state,
- owning the portrait dashboard by default,
- brokering interaction-state such as recording, timeout, and mode transitions,
- and remaining semi-persistent on the battery-backed support rail even when the main board is down.

The first intentional wireless interaction path is also now clearer:

- **A:** YES / confirm / send through
- **B:** NO / cancel / stop
- **C:** short conversation mode
- **D:** long dictation mode

That path currently resolves as:

> **RF remote -> YK04 receiver -> Arduino Uno -> Raspberry Pi 4 -> Huey Core**

Short conversation mode is expected to auto-commit after silence or timeout unless canceled. Long dictation mode is expected to remain open longer for extended input. Blue indicators represent transmit / receive / interaction-active state, while red indicates recording or capture-active state.

### Presence over stagecraft

Huey’s portrait display is primarily a **code and status surface**, not a default cartoon face. The design goal is visible process, earned presence, and real system state rather than a thin layer of performance.

### Boot posture and first manifestation

Huey Core and Huey proper are not the same waking event.

For the active proof body, the operating principle is simple: **let Debian speak**. The system should boot visibly, expose useful errors and service output, and treat startup as diagnostic truth rather than theatrical polish.

In practice, that means:

- the **Raspberry Pi / HueyPulse layer** remains the default owner of the 7-inch portrait status surface,
- that display is expected to show temperatures, watchdog state, fan/service condition, and other live body-state information,
- the **motherboard** remains the shortest path for the first meaningful identity proof,
- and the first trusted manifestation of presence may be text/status output before speech.

This keeps the prototype honest. Huey Core should prove infrastructure first, then identity, then later lawful action.

### Operational sound direction

HueyOS now has a clearer sound-design direction, even though the final cue set is still ahead.

The goal is **not** a theatrical theme song for the proof body. The better direction is a small family of short, modular system sounds: boot, confirm, cancel, listening, and sleep/shutdown cues.

The intended feel is:

- retro-futurist rather than cinematic,
- closer to restrained **1980s computer / 8-bit / Commodore-adjacent** synthesis than modern EDM,
- modular and easy to edit,
- and useful as body-language rather than background music.

In other words, Huey should sound like a real machine waking up, acknowledging input, or going quiet — not like a generic app notification pack.

---

## Governance, Memory, and Lawful Action

This project does not treat AI control as one flat process.

The short public version is simple:

- **governance is decentralized**,
- **memory is unified**,
- **Huey remains one embodied public identity**,
- **action should be lawful rather than merely scripted**.

For the purposes of this README, the important ideas are:

- Huey’s outward interaction and internal governance are related, but not identical;
- bounded citizen-level units exist beneath the public-facing system presence;
- those units are meant to have continuity, sealed local memory, and one final vote each;
- physical action should eventually be gated by legitimacy and protocol, not treated as a meaningless stunt;
- safety crises and constitutional crises are not the same category and should not be handled by the same mechanism;
- the exact inner mechanics of deliberation are part of the project’s **secret sauce** and do not need to be over-explained in public material.

The deeper constitutional model still matters, but it is not the first thing a new reader needs to learn.

---

## Canon and Project Documents

The Monkey-Head-Project is best understood as one canon with different layers.

- **Website / README:** the public-facing introduction
- **Project book / compendium:** the larger human-readable explanatory volume
- **Federation Constitution:** the formal legal and governance companion
- **Master Plan:** the canonical machine-facing implementation spec

These layers are meant to complement each other, not collapse into one undifferentiated document.

---

## Repository Guide

This repository is meant to be readable at two levels:

- a **high-level public overview** for people trying to understand what the project is,
- and a **deeper technical workspace** for people who want to inspect the actual code, docs, and machine-facing spec.

At a high level:

- **README** is the canonical human-facing narrative
- **master-plan-v23.json** is the canonical machine-facing spec
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

The Farm is the external district housing that expands Huey beyond the Core, providing the dedicated GPU infrastructure and node hardware needed for full pooled-compute operation and later growth.

In practical terms, the Farm is intended to become the home for the later GPU infrastructure and the standardized node platform based around the ASUS TUF Z790-PLUS WiFi and Intel i9 line.

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

The planned V4 external district housing that expands Huey beyond the Core and supports the later pooled compute body.

---

## Project Origin

The project name is literal.

Around 2015–2016, the search for a workable robotic or animatronic head led to a **2005 WowWee animatronic monkey head**. Two units were acquired and used as the earliest viable vessel for the project. The shell was stripped, repainted, and treated as the first serious body candidate for the long-term robot build.

That physical starting point is where the **Monkey-Head-Project** gets its name.

The name **Huey** was chosen later through informal input from friends and family and was influenced by the feel of the name more than any strict acronym logic.

---

## Current Open Questions

These are active questions, not oversights:

- final GPU acquisition path for the roughly 80 GB proof
- whether the Core GPU counts toward that final total
- exact future proof-scale model choice
- finalized thermal, electrical, and watchdog thresholds
- final Raspberry Pi operating-system choice for the persistent support layer
- long-term microphone/webcam routing policy once the current direct-to-motherboard proof path has earned its first milestone
- long-term return path, if any, for additional shell-level embodiment beyond Core + Farm
- the final public/internal boundary for what stays public doctrine and what remains internal secret sauce
- the final operational HueyOS cue pack for boot / confirm / cancel / listen / sleep states

---

## License and Credits

**Code:** GPL-3.0-only  
**Docs & Media:** CC-BY-SA-4.0

**Acknowledgements:** PyGPT / PyGPT-net · Debian Trixie / Forky / Sid testing reality · Ollama · every machine strange enough to become infrastructure.

---

## A.I. Auto-Update

- **A.I. counterpart:** README updated for V23 alignment.
- **Human counterpart:** manual review recommended before commit or publish.
- This document was drafted with AI assistance and remains subject to human oversight.
