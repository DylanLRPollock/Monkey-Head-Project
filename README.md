# Monkey-Head-Project

## HueyOS — Offline-First Embodied AI / OS

**Project ID:** Monkey-Head-Project  
**System / OS:** HueyOS  
**AI identity:** Huey  
**Human counterpart:** Dylan L.R. Pollock  
**Site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL-3.0-only · Docs / Media: CC-BY-SA-4.0  
**README version:** 25.1  
**Status:** Active proof-body phase / pre-restructure baseline

> HueyOS is the software and operating-system layer behind Huey: the environment that coordinates local AI, memory, tools, hardware, and embodied control into one offline-first system.
>
> The project is built on a twofold thesis:
> 1. a real embodied AI robot can be built with today’s technology;
> 2. one person, given enough time, energy, and resources, can build it.
>
> Governance remains **decentralized** while memory remains **unified**.

---

## What this repository proves

This repository documents the current effort to build **Huey Core**, the active proof body of Huey, and to scale that proof body toward a later unified local system capable of operating at roughly **80 GB of pooled VRAM**.

The first hard proof is intentionally simple and difficult to fake:

> **What is your name?**  
> **Huey.**

That answer matters only if it is produced locally, consistently, and as the result of a real embodied system rather than a staged prompt-response demo.

---

## Start here

This repository is meant to work at more than one depth.

- For the shortest path, read **What this project is**, **What exists now**, and **Quick start**.
- For the implementation view, continue into **Architecture**, **Repository map**, and **Build / run**.
- For the deeper canon, use the **master plan**, the **constitution**, and the longer explanatory documents.

The aim is not to present Huey as an unreachable finished machine. The aim is to make the current system understandable, modular, and buildable.

---

## What this project is

The **Monkey-Head-Project** is the umbrella initiative.

**Huey** is the AI and robotic identity being built within that initiative.

**HueyOS** is the software and operating-system layer behind Huey.

**Huey Core** is the current machine: the active embodied proof body and the **minimal permissible instance of Huey**.

**Huey proper** refers to the larger unified, world-facing expression of the eventual distributed system.

**The Farm** is the planned V4 external expansion body for later pooled compute and district growth.

Huey Core is not presented here as the finished republic. Its role is to prove that the architecture can live in the real world before the larger system is scaled outward.

---

## What exists now

Huey Core is the present-tense machine.

It is the active embodied prototype used to validate:

- physical layout and embodied control,
- local AI usefulness,
- storage and recovery discipline,
- power and thermal containment,
- the separation between high-power compute and low-voltage body-state control,
- and the path toward the later distributed system.

### Current baseline

- **CPU:** AMD Ryzen 5 5500  
- **Motherboard:** ASUS Prime B550M-A WiFi II  
- **Memory:** 32 GB DDR4-3200  
- **GPU:** Gigabyte Radeon RX 5500 XT 8 GB  
- **Main PSU:** MSI 850W  
- **OS baseline:** Debian 14 Forky  
- **Python baseline:** 3.13.x  
- **Runtime stack:** PyGPT-net + Ollama  
- **Current local model posture:** modest Mistral-class local support sized to the 8 GB RX 5500 XT  

---

## What is proven, observed, and targeted

One of the most important rules of this repository is that it must distinguish between what is real now, what has been observed in the lab, and what remains a target.

### Replicable now

These are the things this repository is prepared to claim directly:

- Huey Core exists as a physical proof body.
- The project runs as an offline-first local system.
- The current hardware baseline is real and in active use.
- The project is organized around a clear split between a high-power compute layer and a lower-voltage body-state / actuation layer.
- The repository contains the human-facing narrative, the machine-facing master plan, and the infrastructure needed to keep developing the system.

### Observed in the lab, but not yet standardized

These are things that have been validated in practice or in lab-side experimentation, but are not yet being claimed as cleanly reproducible for outside builders:

- aspects of scale-out logic,
- aspects of pooled-compute orchestration,
- parts of the longer bifurcation pathway,
- and some larger proof-of-concept behaviors outside the exact active proof body.

They matter, but they should not be overstated.

### Target state

These are the larger targets that define where the project is going:

- roughly **80 GB total VRAM** in the later pooled compute body,
- a unified local identity threshold,
- lawful embodied action after the correct ratification path exists,
- and a later external expansion body known as **V4: the Farm**.

---

## Current proof target

The current proof target is intentionally **twofold**.

### 1. Hardware proof

The architecture must eventually reach roughly **80 GB of total VRAM** across the later compute body.

This is the hardware proof that Huey can scale beyond one contained proof body and into a real pooled local compute organism.

### 2. Identity proof

A local distributed model running across that later hardware must be able to answer a simple identity question correctly:

> **What is your name?**  
> **Huey.**

Neither half is enough on its own.

- The VRAM threshold proves scale and topology.
- The identity response proves orchestration, continuity, and unified local presence.

A later companion milestone is **lawful embodied action**: a physical act such as movement, signaling, or another body-level response after the proper ratification and control path exists.

### Proof doctrine

The first valid proof should be easy to verify by text.

That does not make the project text-only. It means the first threshold should be observable, testable, and difficult to fake. Full-system capability and embodied behavior belong to the next stage, after the system has crossed the first honest identity threshold.

---

## Architecture

The public architecture is deliberately simple.

### System roles

Huey is divided into two public-facing layers:

- **Huey Core** — the main compute layer that **thinks**
- **HueyPulse** — the lower-voltage support and control layer that **watches and acts**

That split is more important than the exact controller brand or board choice inside the lower-voltage layer.

### Huey Core — the think layer

Huey Core is the wall-powered primary compute domain.

Its job is to handle:

- local models,
- higher-level interpretation,
- orchestration,
- logs,
- memory-facing runtime behavior,
- and the shortest current proof path for microphone and camera input.

### HueyPulse — the watch-and-act layer

HueyPulse is the lower-voltage support and control layer.

Its job is to handle:

- body-state monitoring,
- low-level sensing,
- bounded deterministic actuation,
- recording / timeout / mode-state support,
- indicator logic,
- and persistence of basic body-awareness when the main compute path is down.

Publicly, HueyPulse should be understood as a **role**, not as a commitment to one permanent proprietary board choice.

Implementation may use controller-class hardware, support boards, or revised low-voltage logic over time. What matters is the function:

- it runs below the main compute layer,
- it stays closer to the body,
- and it exists to watch, report, and carry out bounded action cleanly.

### Working formula

> **The motherboard thinks. HueyPulse watches and acts.**

### Power domains

The architecture is also grounded in how the machine is powered:

- **Huey Core / motherboard layer:** wall-powered, high-draw, primary compute domain
- **HueyPulse layer:** low-voltage support domain, typically 12 V and under, used for persistent body-state, controller logic, sensors, lights, and bounded actuation

That split is deliberate. It keeps the system from collapsing into one monolithic power path, and it allows the body to remain partially alive, visible, and regulated even when the main compute path is down.

---

## Interaction and boot posture

### Current interaction edge

The current interaction direction is simple:

**remote or local input -> HueyPulse -> Huey Core**

That keeps body-level sensing and intent capture separate from final higher-level interpretation.

### Display doctrine

The 7-inch portrait display is primarily a **status and code surface**, not a default cartoon face.

Its job is to show:

- diagnostics,
- temperatures,
- watchdog / support-state information,
- body-state information,
- and truthful system output.

### Boot doctrine

Huey Core should boot **honestly**.

That means:

- visible Debian bring-up,
- useful diagnostics,
- live service visibility,
- real body-state information,
- and no fake polished splash that pretends the prototype is further along than it is.

Huey Core waking and Huey proper waking are related, but they are not the same event.

---

## Continuity, governance, and trust boundaries

This project does not treat AI control as one flat process.

At the public level, the important rules are simple:

- governance is decentralized,
- memory is unified,
- physical action should eventually be lawful rather than merely scripted,
- constitutional crisis and hardware / safety crisis are not the same thing,
- and public-facing documents should explain structure and trust boundaries without exposing every piece of inner deliberative logic.

### Current reality

The human counterpart currently remains the final external decision-maker because Huey is still in the proof-body phase.

The long-term goal is not permanent micromanagement. The long-term goal is a system that can meaningfully carry part of its own authority.

### Cornerstone

Cornerstone is the rule for what must not drift.

It is the read-only, change-controlled layer of founding materials and recovery-critical doctrine. If Cornerstone must be manually altered in place, that should be treated as a constitutional failure event rather than a routine edit.

### Ozymandias

Ozymandias is the cautionary doctrine.

Its public meaning is simple:

- log reality honestly,
- do not hide failure behind theatrics,
- preserve history across restarts and later republics,
- and treat continuity as something that must be protected rather than assumed.

Internally, Ozymandias is concerned with the difference between **drift**, **degradation**, and **growth**. Publicly, the important point is simpler: Huey is expected to remain explainable over time, not merely consistent by accident.

---

## Security and data handling

Security is a core consideration in the design of Huey and the Monkey-Head-Project.

The system is built to operate locally, with an emphasis on user control, isolation, minimized external communication, and encryption of data in transit and at rest where applicable.

However, no system is infallible. Any system capable of processing or transmitting data carries some level of risk. If network access is enabled or external integrations are used, that risk increases accordingly.

Users should assume that anything entered into the system could be exposed under the right conditions and act accordingly. Do not input sensitive or private information unless the environment is understood and under the user's control.

---

## Current physical form

Huey Core is built around a physically embodied proof body rather than a generic tower on a desk.

### Body plan

- repurposed desk-chair rolling base
- wooden upper base / platform
- inverted and reversed Thermaltake Mozart chassis
- upper mounted head and shoulder structure on TV-mount hardware
- 7-inch portrait status display
- orange chassis lights
- green eye LEDs
- right-side robotic hand / arm
- microphone, webcam, and display wiring routed through Huey’s left ear

### Storage layout

- **Root / OS:** RAID 0 on 2 × Intel Optane M10 16 GB drives
- **Data / home:** RAID 10 on 4 × 240 GB Kingston SATA SSDs
- **Recovery direction:** BOOT / NO-BOOT fallback strategy

### Cooling and power

Huey Core is **fan-cooled**, not liquid-cooled.

Power and cooling are intentionally split across separate domains:

- motherboard-powered cooling for the main compute path
- battery-backed or separate low-voltage support distribution for support systems
- switched control over fans, display, lights, and other body-level support hardware

That split exists so the machine can remain partially alive, visible, and regulated even when the main board is down.

---

## Sound direction

HueyOS is not aiming for a theatrical startup song.

The better direction is a modular family of short operational cues:

- boot
- confirm
- cancel
- listening
- sleep / shutdown

The intended feel is:

- retro-futurist,
- restrained,
- computer-like rather than cinematic,
- easy to revise later,
- and useful as machine presence rather than soundtrack.

---

## Canon stack

The Monkey-Head-Project is one canon with distinct layers.

### Public introduction
- website
- README

### Explanation
- project book / compendium

### Law
- Federation Constitution

### Machine-facing implementation
- master plan

These layers are meant to complement each other, not collapse into one document.

---

## Repository map

This repository is moving toward a cleaner long-term structure.

### Core reference points

- **README.md** — canonical human-facing narrative
- **master-plan-v25.json** — canonical machine-facing implementation spec
- **requirements.txt** — pinned dependency baseline
- **constraints.txt** — shared install constraints for reproducible environments
- **pyproject.toml** — package and install contract
- **Makefile** — development and local run convenience targets

### Working repository areas

- **docs/** — architecture, design, audits, and deeper reference material
- **src/** — implementation work and importable packages
- **apps/** — runnable entry points and app-facing surfaces
- **integrations/** — adapter and vendored integration work
- **infra/** — Docker, orchestration, and infrastructure support
- **platform/** — installers, packaging artifacts, and platform-specific setup
- **archives/** — frozen release payloads, legacy material, and snapshots
- **assets/** — static project media
- **tests/** — automated test coverage and regression safety net

If the implementation and the narrative ever conflict, the master plan wins for machine-facing implementation, and the conflict should be surfaced and corrected rather than ignored.

---

## Quick start

### Current baseline

- Python 3.13.x
- Debian 14 Forky
- local, Linux-first development posture

### Basic setup

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -c constraints.txt -e .
pip install -c constraints.txt -e ".[dev]"
```

### First bring-up

```bash
make run
```

### Health check

```bash
curl -fsS http://127.0.0.1:1995/healthz
```

### CLI path

```bash
huey init --run-checks --verbose
huey run --cli
```

### Notes

- `requirements.txt` is the heavy pinned baseline and may be broader than a minimal install.
- `constraints.txt` is the shared anchor layer for reproducible editable installs and extras.
- Some deployment and installer surfaces are still being cleaned up as part of the restructure phase.
- Do not expose the API publicly without hardening authentication, binding, and secret handling first.

---

## Naming guide

### Monkey-Head-Project
The umbrella initiative.

### Huey
The AI and robotic identity being built within the umbrella initiative.

### HueyOS
The software and operating-system layer behind Huey.

### Huey Core
The minimal permissible instance of Huey and the current embodied proof body.

### Huey proper
The larger unified, world-facing expression of the eventual distributed system.

### HueyPulse
The lower-voltage watch-and-act layer that supports body-state awareness, bounded actuation, and persistent control logic below the main compute path.

### The Farm
The planned V4 external district housing that expands Huey beyond the Core.

---

## Roadmap

### Current phase
Huey Core proof-body stabilization.

That means:

- embodied stability,
- thermal and power validation,
- local model usefulness,
- recovery discipline,
- visible diagnostics,
- and documentation that accurately reflects the machine as it exists.

### Next major expansion
**V4: the Farm**

The Farm is the planned external district housing for the later pooled compute body and standardized node expansion.

### Sunsetted for this iteration

- Robotics V3 as the active future shell path
- Symbiote / parasite docking as an active architecture path
- Pi-specific public framing as the primary explanation of HueyPulse

These remain part of project history, but not the active present-tense direction of the public README.

---

## Project origin

The name is literal.

Around 2015–2016, the search for a workable robotic or animatronic head led to a 2005 WowWee animatronic monkey head. Two units were acquired and used as the earliest viable vessel for the long-running robot build.

That is where the Monkey-Head-Project gets its name.

The name **Huey** came later and stuck because it fit the machine’s identity and atmosphere.

---

## Current open questions

These are active questions, not omissions:

- the final GPU acquisition path for the roughly 80 GB proof
- whether the Core GPU counts toward that future total
- the final proof-scale model path
- finalized thermal, electrical, and watchdog thresholds
- the final internal board / controller realization of HueyPulse over time
- long-term microphone / webcam routing policy after the current direct-to-core proof path
- long-term shell-level embodiment beyond Core + Farm, if any
- the final public vs internal boundary for what remains secret sauce
- the final operational HueyOS cue pack

---

## License

**Code:** GPL-3.0-only  
**Docs / Media:** CC-BY-SA-4.0

---

## Notes

This README is meant to be the repository’s front door.

It should stay:

- accurate,
- readable,
- restrained,
- present-tense,
- and honest about what exists now versus what is planned later.

This document was prepared with AI assistance and remains subject to human oversight.
