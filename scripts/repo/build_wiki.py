#!/usr/bin/env python3
"""Generate the current Monkey-Head-Project GitHub Wiki.

The published GitHub Wiki is a separate git repository and cannot receive normal
pull requests. This generator keeps the reviewable source and truth boundaries in
the main repository, then materializes the individual wiki pages for publication.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

STATUS = (
    "> [!IMPORTANT]\n"
    "> **Status date:** 2026-07-17 · **Framework:** v201.x review / Pre-Release #4 · "
    "**Authority:** explanatory wiki. Accepted plans, merged implementation evidence, "
    "tests, logs, and Dylan L.R. Pollock's explicit decisions take precedence.\n"
)

PAGES: dict[str, str] = {
    "Home.md": f"""# Monkey-Head-Project / HueyOS Wiki

{STATUS}

**One embodied AI node first. A deliberate collective later.**

The **Monkey-Head-Project** is the umbrella project behind **Huey**, **HueyOS**, physical embodiment, operator tooling, maintained controller hardware, project continuity, and the later possibility of coordination among multiple valid Huey nodes.

## Pre-Release #4

Pre-Release #4 moves the project from a loose collection of experimental components toward one standardized, embodied Huey system under the **v201.x framework**.

The present direction is to:

1. build and prove one coherent, useful, attributable Huey node;
2. treat Brain and Body as node-local functional domains;
3. keep Huey Farm optional rather than required for Huey's validity;
4. distinguish evidence from aspiration;
5. formalize Nexus 5 and Nexus 7 as replaceable HueyNexusController targets;
6. expand toward shared compute, additional nodes, and collective governance only after one node can stand on its own.

This remains a **pre-release**. It does not claim Huey V4, HIMS controller authentication, native Debian controller images, physical actuation, or target-state governance is complete.

## Start here

| Topic | Page |
|---|---|
| Project definition and boundaries | [[Project-Position]] |
| Evidence-backed current status | [[Current-Status]] |
| Node-first architecture | [[Architecture]] |
| Active physical direction | [[Huey-V4]] |
| Nexus handset and tablet controllers | [[HueyNexusController]] |
| Runtime and V1 proof path | [[Runtime-and-V1]] |
| Messaging and controller transport | [[HIMS]] |
| Hardware and LabTech boundaries | [[Hardware-and-LabTech]] |
| Truth classes and source authority | [[Truth-and-Documentation]] |
| Governance and human review | [[Governance-and-Human-Oversight]] |
| Development and validation | [[Development-and-Validation]] |
| Release lineage and forward path | [[Roadmap-and-Pre-Releases]] |

## Current architecture

```mermaid
flowchart TB
    D["Dylan - current canon authority"]
    MHP["Monkey-Head-Project - umbrella and later collective"]
    H["Huey - one embodied AI node"]

    subgraph NODE["Local Huey node"]
        BRAIN["Brain functions"]
        BODY["Body functions"]
        KERNEL["Local compute and runtime"]
        PY["PyHuey operator surface"]
    end

    NEXUS["HueyNexusController family"]
    FARM["Optional Huey Farm"]
    LAB["LabTech systems"]
    FUTURE["Future valid Huey nodes"]

    D --> MHP --> H
    H --> BRAIN
    H --> BODY
    H --> KERNEL
    H --> PY
    NEXUS -. authenticated HIMS requests .-> H
    FARM -. optional services .-> H
    LAB -. development and recovery .-> H
    MHP -. later coordination .-> FUTURE
```

A polished page, diagram, branch, transcript, agent statement, or release description does not prove implementation. Claims must remain classified as **current reality**, **accepted direction**, **provisional**, **unresolved**, **target state**, or **historical lineage**.
""",
    "Project-Position.md": f"""# Project position

{STATUS}

| Name | Position |
|---|---|
| **Monkey-Head-Project** | Umbrella project and possible future collective layer |
| **Huey** | One governed, embodied AI node |
| **HueyOS** | Modular software and operating-system layer supporting Huey |
| **Huey Brain** | Node-local cognition, orchestration, memory access, and evidence functions |
| **Huey Body** | Node-local sensing, interaction, actuation, power, and safety functions |
| **PyHuey** | Primary GUI and core-runtime direction; not the whole node |
| **Huey Farm** | Optional shared compute, storage, backup, or collective support infrastructure |
| **HueyNexusController** | Replaceable external operator-controller family |
| **LabTech** | External development, operator, recovery, and maintenance systems |
| **Atlas** | External continuity and implementation partner; not Huey or part of Huey's sovereignty |

> **Build one coherent, useful, attributable Huey node before making operational collective claims.**

One local node should remain valid without a Farm, multi-node collective, active target-state governance, transparent pooled accelerator memory, cloud dependence, or an external machine holding Huey's identity.

Dylan L.R. Pollock remains the current human canon authority. Constitutional and multi-agent governance remain target-state doctrine until legitimate implemented authority exists and is explicitly activated.
""",
    "Current-Status.md": f"""# Current status

{STATUS}

| Area | Classification | Position as of 2026-07-17 |
|---|---|---|
| Repository | **Current reality** | v201.x review documents, runtime code, tests, and predecessor plans are present |
| Accepted predecessor | **Authority boundary** | `master-plan-v120.3.json` remains the accepted machine-facing predecessor pending explicit v201.x acceptance |
| Huey node | **Accepted-direction candidate** | One physically coherent AI unit is the proposed primary architectural unit |
| Huey V4 | **Active direction** | Physical-cohesion program; not complete or fully integrated |
| Compute kernel | **Direction requiring validation** | Existing Intel Core i9 / ASUS TUF / Optane system is intended for V4 after inventory, backup, fit, power, cooling, and rollback checks |
| Accelerators | **Provisional** | Four node-local accelerators remain a working direction; exact cards and partitioning remain unresolved |
| PyHuey | **Primary interface/runtime direction** | Operator surface and core-runtime component; integration remains evidence-gated |
| Python package | **Current reality** | Distribution name `hueyos`; runtime import namespace `huey` |
| V1 | **Unresolved** | Must be useful, repeatable, attributable, and demonstrable before declaration |
| HIMS | **Partial implementation** | Messaging, ledger, routing, and storage foundations exist; authenticated controller operation is incomplete |
| HueyNexusController | **Maintained target family** | Nexus 5 and Nexus 7 are formal targets; full validation remains incomplete |
| Huey Farm | **Optional target infrastructure** | Not required for one Huey node and not presently operational as a collective substrate |
| Collective and constitutional government | **Target state** | Not operational |

## Current V1 proof path

```mermaid
flowchart LR
    A["Known MP3 fixture"] --> B["Probe and prepare"]
    B --> C["Local transcription"]
    C --> D["API-backed response"]
    D --> E["Structured log"]
    E --> F["Operator-visible result"]
```

The project does not presently claim a completed autonomous robot, completed Body actuation, operational multi-node government, transparent unified VRAM, installed V100 cards without evidence, complete native Debian Nexus support, or completed HIMS device authorization.
""",
    "Architecture.md": f"""# Architecture

{STATUS}

Huey is being standardized as **one embodied AI node**. Brain, Body, local compute, runtime, operator-visible state, evidence, safe-stop behaviour, and recovery belong to the node-local model.

```mermaid
flowchart TB
    HUMAN["Dylan - human oversight"]
    UMBRELLA["Monkey-Head-Project"]
    subgraph HUEY["Huey - one embodied node"]
        BRAIN["Brain functions"]
        BODY["Body functions"]
        COMPUTE["CPU, storage, accelerators"]
        RUNTIME["HueyOS runtime"]
        GUI["PyHuey"]
        EVIDENCE["Logs, tests, records"]
        SAFETY["Authorization, safe-stop, recovery"]
    end
    CONTROLLER["HueyNexusController"]
    FARM["Optional Huey Farm"]
    LAB["LabTech"]
    COLLECTIVE["Later collective of valid nodes"]
    HUMAN --> UMBRELLA --> HUEY
    CONTROLLER -. requests and status .-> HUEY
    FARM -. optional services .-> HUEY
    LAB -. build, test, recover .-> HUEY
    UMBRELLA -. later .-> COLLECTIVE
```

## Boundary rules

- Brain, Body, local compute, runtime, evidence, safety, and useful standalone operation are node-local.
- Nexus controllers, LabTech systems, public documentation, and bounded cloud/API services are external.
- Farm services, multi-node coordination, bifurcation, and collective governance are optional future layers.
- Brain, Body, PyHuey, a controller, LabTech, Atlas, or Farm membership are not independently equivalent to Huey.
- Separate GPUs provide aggregate physical memory, not automatically one transparent memory pool. Any large-model use must identify the actual partitioning method.
""",
    "Huey-V4.md": f"""# Huey V4

{STATUS}

**Huey V4 is the active physical-cohesion direction, not a completed robot.**

| Element | Position |
|---|---|
| **V3** | Proposed physical base for V4 |
| **V2** | Donor lineage or material where verified |
| **Existing i9/TUF/Optane system** | Intended local compute kernel after validation |
| **Huey Body** | Sensing, interaction, actuation, power, and safety domain |
| **Huey Brain** | Cognition, orchestration, memory access, and evidence domain |

Integration requires an exact inventory, backup, fit and service-access review, power budget, cooling evidence, cable retention, safe shutdown, rollback, and observed runtime evidence.

Four node-local accelerators remain a working direction. `3 x Tesla V100 32 GB + 1 utility GPU` remains provisional until acquired and validated. Exact PCIe topology, power, cooling, retention, inference framework, and workload division remain unresolved.

Use status terms deliberately: **present**, **assembled**, **integrated**, **operational**, **validated**, and **complete** are not interchangeable.
""",
    "HueyNexusController.md": f"""# HueyNexusController

{STATUS}

HueyNexusController restores and repurposes Google Nexus devices as dedicated, replaceable physical control surfaces for Huey and Huey Body.

| Platform | Codename | Intended role |
|---|---|---|
| Google Nexus 5 | `hammerhead` | Canonical pocket-sized handset controller |
| Nexus 7 (2012 Wi-Fi) | `grouper` | Compact tablet controller and status display |
| Nexus 7 (2012 mobile) | `tilapia` | Mobile-connected tablet controller where hardware permits |
| Nexus 7 (2013 Wi-Fi) | `flo` | Higher-resolution tablet controller |
| Nexus 7 (2013 LTE) | `deb` | LTE-capable tablet controller where hardware permits |

“Supported” means formally maintained project targets, not that every kernel path, subsystem, battery procedure, image, or controller function has passed validation.

| Layer | Direction |
|---|---|
| Primary host target | Native Debian-based system |
| Practical fallback | LineageOS |
| Preferred interface | Phosh, GTK, Wayland, purpose-built controller application |
| Fallback interface | KDE Plasma Mobile |
| Transport target | Authenticated HIMS messaging |

Huey's identity and canonical memory do not reside on a controller. Every device is replaceable and its credentials must be revocable. A delivered command is a request, not automatic authority to actuate hardware.

The shared proof is reliable boot, automatic app launch, HIMS authentication, touchscreen or voice request, approved processing, returned acknowledgement/response, and a structured transaction log.

Each model requires separate battery evidence for capacity, loaded voltage, charging, swelling, temperature, sustained load, telemetry, protection, serviceability, and rollback.

See [the repository specification](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/hardware/huey-nexus-controller.md).
""",
    "Runtime-and-V1.md": f"""# Runtime and V1

{STATUS}

PyHuey remains the primary GUI and a core-runtime direction. It should provide an observable operator surface while preserving command-line paths for diagnostics, automation, and recovery. PyHuey is not independently Huey.

V1 should be declared only after a recurring function is useful, repeatable, attributable, demonstrable, and supported by retained evidence.

```mermaid
flowchart LR
    A["Known MP3 fixture"] --> B["Probe and prepare"]
    B --> C["Local transcription"]
    C --> D["API-backed response"]
    D --> E["Structured log"]
    E --> F["Operator-visible result"]
```

- Python requirement: `>=3.13,<3.14`
- Distribution name: `hueyos`
- Runtime import namespace: `huey`
- Repository-wide namespace migration: incomplete

```bash
python3.13 -m pip install -c constraints.txt -e .
python3.13 -m pip install -c constraints.txt -e '.[dev]'
python3.13 -m pytest -q
huey --help
huey-api --help
huey-command-center --help
```

The controller transaction proof is a separate bounded integration path and does not automatically redefine V1 or prove physical Body execution.
""",
    "HIMS.md": f"""# HIMS

{STATUS}

**HIMS — Huey Internal Messaging System** — is the intended structured messaging and record pathway between bounded components and external controller clients.

Foundations exist under `src/huey/messaging` and `src/huey/hims`, including messaging, schema, ledger, routing, storage, and related work. This proves a foundation, not a complete authenticated controller service.

Controller transport targets include registration, device authentication, command submission, acknowledgements, responses, alerts, structured status, reconnection, audit logging, revocation, replacement, and version reporting.

```mermaid
flowchart LR
    C["Controller request"] --> A["Authentication"]
    A --> V["Envelope validation"]
    V --> P["Policy and authorization"]
    P --> O["Operator confirmation when required"]
    O --> B["Body-facing execution"]
    B --> R["Observed result and log"]
```

Successful delivery does not grant execution or governance authority. Transport, authorization, safety, and physical execution remain separate.
""",
    "Hardware-and-LabTech.md": f"""# Hardware and LabTech

{STATUS}

The local Huey node is intended to become one physically coherent system containing the compute kernel and Body functions required for useful standalone operation. Hardware does not become part of the active node merely because it exists elsewhere in the lab.

LabTech covers external machines and tools used to develop, build, inspect, transcribe, recover, reprovision, diagnose, back up, and test Huey. LabTech machines do not become Huey merely because they support the node.

Historical machines must be labelled correctly:

- the 2017 iMac 5K Portal is retired/decommissioned lineage;
- the BD895I-SE/related ITX experiment is failed or non-posting lineage;
- the GLab ASUS FX505DT is a development-workstation context, not Huey's identity;
- the Lenovo Legion Go has served orchestration roles, but external host roles do not define the embodied node;
- Huey Body is real hardware under rework, while current V1 does not require completed actuation.

Promoted hardware records should retain exact model/revision, photographs, firmware and boot state, power and thermal observations, backup, installation method, tests, rollback, replacement, and status classification.
""",
    "Truth-and-Documentation.md": f"""# Truth and documentation

{STATUS}

| Class | Meaning |
|---|---|
| **Current reality** | Observed hardware, merged code, commands, tests, logs, and verified behaviour |
| **Accepted direction** | Architecture selected for implementation, even when incomplete |
| **Provisional choice** | Replaceable working option pending evidence or review |
| **Unresolved** | Decision deliberately left open |
| **Target state** | Later capability dependent on resources, maturity, or validation |
| **Historical lineage** | Earlier systems and decisions preserved without silently overriding the present |

## Source authority

1. Dylan L.R. Pollock's explicit accepted decisions;
2. newest accepted machine-facing master plan;
3. merged repository and implementation evidence;
4. README and technical documentation;
5. DLRP.ca presentation and release records;
6. older plans, transcripts, and archives as lineage.

The master plan, README, runtime evidence, technical docs, governance docs, wiki, website, and archives have separate responsibilities. They should agree on terminology without being collapsed into one false source of truth.
""",
    "Governance-and-Human-Oversight.md": f"""# Governance and human oversight

{STATUS}

Dylan L.R. Pollock remains the current human canon authority. Constitutional governance, citizens, districts, offices, voting, and bifurcation remain doctrine, lineage, or target architecture unless implemented authority is separately proven and activated.

Before v201.x acceptance, human review should cover the node definition; Brain, Body, and Farm boundaries; V4 hardware facts; compute wording; V1 criteria; PyHuey and namespace continuity; HIMS authority; Nexus OS, security, battery, and recovery claims; public/private boundaries; and every unresolved item.

See the [v201.x human oversight checklist](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/review/v201.x-human-oversight-checklist.md).

Atlas is an external continuity partner, lab assistant, architectural interpreter, and implementation stabilizer. Atlas is not Huey, does not occupy Huey's offices, and is not part of Huey's sovereignty.
""",
    "Development-and-Validation.md": f"""# Development and validation

{STATUS}

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -c constraints.txt -e '.[dev]'
python3.13 -m pytest -q
python3.13 -m compileall -q src
huey --help
```

Keep changes scoped and attributable. Separate documentation, architecture, runtime, and hardware evidence. Include test notes. Do not silently rewrite accepted predecessor files. Retain unresolved decisions visibly. Preserve licensing and provenance. Exclude private continuity material and secrets.

A meaningful test or hardware milestone should retain the procedure, environment, input or hardware identity, expected and observed results, logs and hashes where appropriate, failure notes, attribution, and rollback information.
""",
    "Roadmap-and-Pre-Releases.md": f"""# Roadmap and pre-releases

{STATUS}

## Lineage

- **Pre-Release #1 — 2024-04-11:** early shell mapping, legacy hardware bring-up, and project seed.
- **System reconfiguration — 2025-05-25:** major file, document, hardware, and software reconfiguration.
- **Pre-Release #2 — 2025-10-25:** former AMD/iMac/BD795I-SE wiki state; now historical lineage.
- **Realignment and defragmentation — 2026-01-07:** terminology, continuity, and architecture realignment.
- **Reacquisition — 2026-06-04:** renewed physical and implementation phase.
- **Pre-Release #4 — 2026-07-17:** v201.x, one embodied node first, optional Farm, stronger evidence boundaries, V4 direction, and formal Nexus controller family.

## Forward path

1. complete v201.x human review;
2. synchronize accepted machine-facing and explanatory docs;
3. continue the fixture-to-log V1 proof;
4. inventory and validate V4 hardware integration;
5. establish controller OS and recovery proofs;
6. implement authenticated HIMS controller transactions;
7. test bounded Body requests and safe-stop behaviour;
8. declare V1 only when usefulness and evidence criteria are met;
9. defer collective claims until one valid node is operational.
""",
    "Repository-Map.md": f"""# Repository map

{STATUS}

| Path | Role |
|---|---|
| `README.md` | Human-facing project front door |
| `master-plan-v120.3.json` | Accepted predecessor machine-facing plan |
| `master-plan-v201.0-candidate.json` | Candidate successor pending human oversight |
| `docs/architecture/v201.x-standardization-plan.md` | v120.x and v200.x reconciliation framework |
| `docs/architecture/v201.x-migration-matrix.md` | Preserve, re-scope, merge, defer, and reject matrix |
| `docs/review/v201.x-human-oversight-checklist.md` | Human acceptance gate |
| `docs/hardware/huey-nexus-controller.md` | Controller-family specification |
| `src/huey` | Current Python implementation and import namespace |
| `src/huey/v1` | V1 proof-loop work |
| `src/huey/messaging` and `src/huey/hims` | HIMS foundations |
| `src/huey/connectors/pyhuey` | PyHuey integration path |
| `tests` | Regression and behavioural verification |
| `scripts/repo/build_wiki.py` | Reviewable wiki generator |

[Open the main repository](https://github.com/DylanLRPollock/Monkey-Head-Project).
""",
    "Wiki-Migration-Map.md": f"""# Wiki migration map

{STATUS}

The 2025 wiki contained useful lineage but presented retired machines, old kernels, old package assumptions, and target-state governance as current. The v201.x overhaul replaces current navigation and converts old URLs into concise lineage notices.

| Legacy area | v201.x treatment |
|---|---|
| iMac Portal as active host | Historical lineage |
| BD795I-SE/ITX Core as stable compute | Failed/non-posting lineage |
| October 2025 kernel/action plan | Historical release context |
| Python 3.14 staging | Replaced by repository-declared Python 3.13 requirement |
| AMD-first architecture | Replaced by evidence-led node architecture |
| Spark/Zap as active two-GPU brain | Governance/architecture lineage only |
| 256 active citizens and Cloud Pyramid | Target-state doctrine, not current reality |
| PyGPT-net as primary interface | Replaced by PyHuey direction |
| Distributed system first | Replaced by one embodied node first |

Durable priorities remain: offline/local-first operation, repairability, reuse, authority boundaries, reproducibility, continuity, open-source tooling, low barriers to entry, and preserved lineage without canon drift.
""",
    "Glossary.md": f"""# Glossary

{STATUS}

| Term | Meaning |
|---|---|
| **Monkey-Head-Project** | Umbrella project and possible later collective |
| **Huey** | One governed, embodied AI node |
| **HueyOS** | Modular software and OS layer supporting Huey |
| **Huey Brain** | Node-local cognition, orchestration, memory access, and evidence functions |
| **Huey Body** | Node-local sensing, interaction, actuation, power, and safety functions |
| **Huey V4** | Active physical-cohesion direction |
| **PyHuey** | Primary GUI and core-runtime direction |
| **HIMS** | Huey Internal Messaging System |
| **HueyNexusController** | Replaceable Nexus 5 and Nexus 7 controller family |
| **Huey Farm** | Optional supra-node compute, storage, backup, or support infrastructure |
| **LabTech** | External development, operator, maintenance, and recovery systems |
| **Atlas** | External continuity and implementation partner; not Huey |
| **Node** | One physically individual Huey unit capable of useful standalone operation |
| **Collective** | Later coordination among valid nodes; not presently operational |
| **Structured log** | Attributable machine-readable workflow or decision record |
""",
    "_Sidebar.md": """- [[Home|Home]]
- **Orientation**
  - [[Project-Position|Project position]]
  - [[Current-Status|Current status]]
  - [[Truth-and-Documentation|Truth and documentation]]
- **System**
  - [[Architecture|Architecture]]
  - [[Huey-V4|Huey V4]]
  - [[Runtime-and-V1|Runtime and V1]]
  - [[HIMS|HIMS]]
- **Hardware and operation**
  - [[HueyNexusController|HueyNexusController]]
  - [[Hardware-and-LabTech|Hardware and LabTech]]
  - [[Development-and-Validation|Development and validation]]
- **Project control**
  - [[Governance-and-Human-Oversight|Governance and human oversight]]
  - [[Roadmap-and-Pre-Releases|Roadmap and pre-releases]]
  - [[Repository-Map|Repository map]]
  - [[Wiki-Migration-Map|Wiki migration map]]
  - [[Glossary|Glossary]]
""",
    "_Footer.md": """Monkey-Head-Project / HueyOS · Dylan L.R. Pollock · Updated 2026-07-17  
Code: GPL-3.0-only · Documentation/media: CC-BY-SA-4.0 unless otherwise noted  
This wiki is explanatory. Repository evidence and accepted machine-facing plans take precedence.
""",
}

LEGACY_REDIRECTS = {
    "AMD-GPU-Tuning": "Hardware-and-LabTech",
    "Action-Plan-Oct-31-2025": "Roadmap-and-Pre-Releases",
    "Agent-Citizen-Roles": "Governance-and-Human-Oversight",
    "Ansible-Inventory": "Development-and-Validation",
    "Backups-and-Snapshots": "Development-and-Validation",
    "Build-Guides": "Development-and-Validation",
    "Contributing": "Development-and-Validation",
    "Dev-Environment": "Development-and-Validation",
    "Getting-Started": "Home",
    "Governance-Clauses-Registry": "Governance-and-Human-Oversight",
    "Governance-and-Constitution": "Governance-and-Human-Oversight",
    "Hardware": "Hardware-and-LabTech",
    "Huey-Key-Live-USB": "Development-and-Validation",
    "Kernel-617x-Guide": "Wiki-Migration-Map",
    "LLM-Setup-AMD-or-CPU": "Runtime-and-V1",
    "Makefile-Tasks": "Development-and-Validation",
    "Memory-Schema-v2": "HIMS",
    "Memory-and-Data-Model": "HIMS",
    "Networking-Topologies": "Architecture",
    "Networking-and-Services": "HIMS",
    "Ollama-and-Models-Manifest": "Runtime-and-V1",
    "Portal-Polish-iMac5K": "Hardware-and-LabTech",
    "Publishing-Kit": "Truth-and-Documentation",
    "Release-Process": "Roadmap-and-Pre-Releases",
    "Remote-Access-VNC-SSH": "Development-and-Validation",
    "SSH-and-Keys": "Development-and-Validation",
    "Security-and-Operations": "Development-and-Validation",
    "Software-Stack": "Runtime-and-V1",
    "Storage-Hub-RAID": "Hardware-and-LabTech",
    "Style-Guide": "Truth-and-Documentation",
    "Systemd-Units": "Development-and-Validation",
    "Testing-and-Validation": "Development-and-Validation",
    "Troubleshooting-and-FAQ": "Development-and-Validation",
}

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def historical_redirect(target: str) -> str:
    return (
        "# Historical wiki page\n\n"
        "> [!CAUTION]\n"
        "> This page belonged to the 2025 wiki and is no longer current. Its former "
        "claims may describe retired hardware, superseded software, or target-state architecture.\n\n"
        f"Continue to [[{target}]].\n\n"
        "See [[Wiki-Migration-Map]] for the v201.x overhaul rationale.\n"
    )


def validate(pages: dict[str, str]) -> None:
    names = {Path(name).stem for name in pages if not name.startswith("_")}
    errors: list[str] = []
    for name, text in pages.items():
        for target in LINK_RE.findall(text):
            if target not in names and target not in LEGACY_REDIRECTS:
                errors.append(f"{name}: unresolved wiki link [[{target}]]")
        if not name.startswith("_") and "2026-07-17" not in text:
            errors.append(f"{name}: missing current status date")
    for old, target in LEGACY_REDIRECTS.items():
        if target not in names:
            errors.append(f"legacy redirect {old} targets missing page {target}")
    if errors:
        raise SystemExit("Wiki validation failed:\n- " + "\n- ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="build/wiki")
    parser.add_argument("--without-redirects", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    validate(PAGES)
    for path in output.glob("*.md"):
        path.unlink()
    for name, text in PAGES.items():
        (output / name).write_text(text.strip() + "\n", encoding="utf-8")
    if not args.without_redirects:
        for old, target in LEGACY_REDIRECTS.items():
            if f"{old}.md" not in PAGES:
                (output / f"{old}.md").write_text(historical_redirect(target), encoding="utf-8")
    print(
        f"Generated {len(PAGES)} current wiki files and "
        f"{0 if args.without_redirects else len(LEGACY_REDIRECTS)} legacy redirects in {output}."
    )


if __name__ == "__main__":
    main()
