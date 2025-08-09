# 🐒 Monkey Head Project – HueyOS
**Author:** Dylan L. R. Pollock

> **HueyOS** is a prototype robotic AI/OS — a one-person, open-source odyssey that revives legacy hardware, fuses it with modern compute, and binds the result to a living constitution. Huey is transparent by design, modular by necessity, and governed—never merely programmed—by the **Cloud Pyramid**.

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.12–3.13-blue)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📌 Quick Links

* [Overview](#overview)
* [Repository Structure](#repository-structure)
* [Architecture](#huey-os-architecture)
* [Governance](#cloud-pyramid-governance)
* [Hardware Fleet](#hardware-fleet)
* [Installation](#installation--quick-start)
* [Development Setup](#development-setup)
* [Usage](#usage)
* [Contributing](#contributing)
* [Feature Matrix](#feature-matrix)
* [Roadmap](#roadmap)
* [License & Credits](#license--credits)

---

## Overview

HueyOS is a **Debian Trixie** real-time kernel system with **Macro**, **Micro**, and **Nano OS layers** for AI governance.
It merges modern AI agents, a codified constitutional framework, and retro hardware support into a single modular platform.

**Core Principles:**

| Principle         | Operational Intent                                          |
| ----------------- | ----------------------------------------------------------- |
| **Autonomy**      | Every action must trace to a ratified clause.               |
| **Modularity**    | Swap hardware or software components with no refactoring.   |
| **Expandability** | Ready for GPU packs, quantum PCIe cards, and future agents. |
| **Open Ethos**    | All source, schematics, and votes are public.               |

📜 Full origin story → [`docs/preamble.md`](docs/preamble.md)

---

## Repository Structure

| Path                      | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| `.github/`                | CI workflows, CODEOWNERS, issue templates.              |
| `docker/`                 | Docker Compose and build files for HueyOS services.     |
| `docs/`                   | Constitution, governance chapters, architecture specs.  |
| `huey/`                   | Core HueyOS runtime and service modules.                |
| `pygpt/`                  | PyGPT integration for AI/LLM capabilities.              |
| `requirements/`           | Split dependency profiles (core, ml, data, cloud, dev). |
| `setup/`                  | Installer scripts, ISO builder, provisioning configs.   |
| `src/`                    | Python package source code.                             |
| `tests/`                  | Unit and integration tests.                             |
| `.editorconfig`           | Editor formatting rules.                                |
| `.gitattributes`          | Git line ending & binary rules.                         |
| `.gitignore`              | Ignored files/directories.                              |
| `.gitmodules`             | Git submodules (e.g., pygpt-MHP).                       |
| `.pre-commit-config.yaml` | Pre-commit hook definitions.                            |
| `CONTRIBUTING.md`         | Contribution guidelines.                                |
| `huey.env.example`        | Example environment variables.                          |
| `LICENSE`                 | GPL-3.0-only for code, CC-BY-SA-4.0 for docs/media.     |
| `Makefile`                | Common developer commands.                              |
| `pyproject.toml`          | Project metadata & dependencies.                        |
| `requirements.txt`        | All-in-one Python dependencies.                         |

---

## Huey OS Architecture

```
HueyOS
├── MacroOS   # Huey Core · clause & quorum enforcement
├── MicroOS   # Docker/K8s SubOS · modular services
└── NanoOS    # Rust/Python GPIO threads · sensor loops
```

**Agents:**

* **Spark-4** — Creative AI core
* **Volt-4** — Logical/evaluative AI core
* **Zap-4** — Event-driven/sensor agent
* **Watt-4** — Energy/power management

📄 More details → [`docs/architecture/huey-os.md`](docs/architecture/huey-os.md)

---

## Cloud Pyramid Governance

| Tier                                  | Role                                                   |
| ------------------------------------- | ------------------------------------------------------ |
| **Founding Father / Huey Collective** | Ultimate veto, ethos guardian.                         |
| **Grand Council**                     | Executive · Senate (hardware) · Parliament (software). |
| **Joint Session**                     | Merges bills, prevents silo drift.                     |
| **Chambers**                          | Daily legislation for each domain.                     |
| **Populace**                          | 128 AI citizens, scaled with civic age/resources.      |

📄 Governance chapters:

* [Ch. 7 – Wartime Protocols](docs/governance/chapters/07-wartime.md)
* [Ch. 9 – Oversight & Audits](docs/governance/chapters/09-oversight.md)
* [Ch. 10 – External Relations](docs/governance/chapters/10-foreign.md)

---

## Hardware Fleet

**Primary Orchestration Node ("Legacy Node")**

| Component  | Specification                                                                |
| ---------- | ---------------------------------------------------------------------------- |
| Boards     | Supermicro X9QRI-F+ (4 × Xeon E5-4627 v2) + Supermicro C9X299-PGF (i7-7820X) |
| Memory     | 128 GB ECC (64 GB quorum zone)                                               |
| Storage    | 1 TB NVMe OS · 8 × 2 TB SAS RAID-10 · 10 TB mirrored USB-C cold tier         |
| Cooling    | Phase-change + PWM fallback                                                  |
| Power      | Dell R710 redundant PSUs + 550 W consumer rails                              |
| Networking | Dual 10 GbE Areion · Z-Wave I/O mesh                                         |

**Lab Companions**

* MBP 2019 “Daily Driver” — i9 · 32 GB RAM · dual-boot dev box.
* iMac 5K 2017 “Universal Display” — retina HUD & IDE.
* MBP 2012 “Transmitter” — FireWire/Ethernet bridge.
* ThreadRipper 1950X “RAID” — stress-test node.
* Retro Stack — VIC-20 · C64 · C128.

---

## Installation & Quick Start

### Prerequisites

* `git`
* `make ≥ 4.3`
* `docker` + compose
* `rustup`
* x86-64 (4 cores, 16 GB RAM, 256 GB disk, UEFI)
* **Python 3.12–3.13**

### User Setup (ISO)

```bash
git clone --recurse-submodules https://github.com/your-fork/MonkeyHeadProject.git
cd huey_os && make iso
```

---

## Development Setup

```bash
make setup               # Core
make ml                  # ML profile
make data                # Data profile
make cloud               # Cloud profile
make dev                 # Dev tools
```

### Environment Variables

Copy `huey.env.example` to `.env` and configure.

---

## Usage

Run locally:

```bash
make run
```

Run in Docker:

```bash
docker compose -f docker/compose.yml up
```

Run tests:

```bash
make test
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

**Summary:**

1. Fork → branch → PR
2. Use conventional commits
3. Keep PRs focused; update docs
4. CI runs lint/tests/governance checks

---

## Feature Matrix

| Feature           | Core | ML | Data | Cloud | Dev |
| ----------------- | ---- | -- | ---- | ----- | --- |
| FastAPI API       | ✅    | ✅  | ✅    | ✅     | ✅   |
| LlamaIndex/Ollama |      | ✅  | ✅    | ✅     | ✅   |
| Chroma/Pinecone   |      |    | ✅    | ✅     | ✅   |
| Azure/AWS SDKs    |      |    |      | ✅     | ✅   |
| Dev Tools         |      |    |      |       | ✅   |

---

## Roadmap

| Phase | Date       | Milestone                                                |
| ----- | ---------- | -------------------------------------------------------- |
| 1     | 2024-04-11 | Genesis — VIC-20/C64/C128 links; bare-metal boot.        |
| 2     | 2024-06-21 | Integration — power grid, Spark-4 + Volt-4 online.       |
| 3     | 2024-10-31 | System Awakening — dual-node 10-hour burn-in.            |
| 4     | 2025-01-25 | Decision Core — YES/NO engine; honeycomb RAID.           |
| 6     | 2025-08-04 | Reconciliation — taxonomy locked; issue tracker live.    |
| 7     | 2025-10-15 | Architecture — emergent personality; Amendment-001 vote. |

---

## License & Credits

**Code:** GPL-3.0-only
**Docs & Media:** CC-BY-SA-4.0

**Acknowledgements:** AutoGPT · PyTorch · RetroArch · ShellGPT · bmc64 · midnight tinkerers