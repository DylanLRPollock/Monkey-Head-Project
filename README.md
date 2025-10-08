# 🐒 Monkey Head Project – HueyOS

**Author:** Dylan L. R. Pollock  
**Status date:** 05-10-2025

> **HueyOS** is a prototype robotic AI/OS that marries retro computing legacies with modern, modular hardware and a living constitutional framework. Huey is transparent by design, modular by necessity, and governed—not merely programmed—by the **Cloud Pyramid**.

(UEFI-only - amd64 - Kernel 6.16.4 - Debian 13.0.0 Trixie)

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.12–3.13-blue)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📌 Quick Links

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Architecture](#hueyos-architecture)
- [Governance](#cloud-pyramid-governance)
- [Hardware Topology](#hardware-topology)
- [Installation](#installation--quick-start)
- [Development Setup](#development-setup)
- [Usage](#usage)
- [Contributing](#contributing)
- [Feature Matrix](#feature-matrix)
- [Roadmap](#roadmap)
- [License & Credits](#license--credits)

---

## Overview

HueyOS targets **Debian 13 “Trixie”** with a custom low‑latency kernel series **6.16.0‑huey**. It unifies modern AI agents, a codified constitutional framework, and retro hardware support in a single modular platform. Headless and GUI modes are supported.

**Highlights (as of 2025‑10‑05):**

- **OS baseline:** Debian 13.0.0 (Trixie), custom kernel **6.16.0‑huey**
- **Python:** initial pin **3.13.5** (user‑upgradable post‑install)
- **Desktop:** **MATE** + **LightDM**; preferred lightweight browser: **qutebrowser**; full browser: **Edge Dev**
- **AI runtime:** **PyGPT‑net** (desktop orchestrator), **Ollama** (local LLMs), ROCm/AMDGPU where available
- **Memory:** unified long‑term store via JSON logs + SQLite; reproducible telemetry; VNC via TigerVNC tunneled over SSH
- **Networking:** prefer bonded Ethernet; Wi‑Fi only as fallback

**Core Principles**

| Principle        | Operational intent                                           |
|------------------|--------------------------------------------------------------|
| **Autonomy**     | Every action must trace to a ratified clause.                |
| **Modularity**   | Swap hardware/software without refactoring.                  |
| **Expandability**| Ready for GPU packs, future accelerators and new agents.     |
| **Open Ethos**   | Source, schematics and votes are public.                     |

---

## Repository Structure

| Path                      | Description                                             |
|---------------------------|---------------------------------------------------------|
| `.github/`                | CI workflows, CODEOWNERS, issue templates               |
| `docker/`                 | Compose/build files for HueyOS services                 |
| `docs/`                   | Constitution, governance, architecture                  |
| `huey/`                   | Core runtime and service modules                        |
| `requirements/`           | Split dependency profiles (core, ml, data, cloud, dev)  |
| `setup/`                  | Installer scripts, ISO builder, provisioning configs    |
| `src/`                    | Python package source                                   |
| `tests/`                  | Unit & integration tests                                |
| `repo/pygpt-MHP`          | Submodule: PyGPT‑net integration                        |
| `Makefile`                | Common developer commands                               |
| `pyproject.toml`          | Project metadata & dependencies                         |
| `requirements.txt`        | Aggregate Python dependencies                           |
| `.pre-commit-config.yaml` | Pre‑commit hooks                                        |
| `huey.env.example`        | Example environment variables                           |
| `LICENSE`                 | GPL‑3.0‑only (code), CC‑BY‑SA‑4.0 (docs/media)          |

> Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch `repo/pygpt-MHP`.

---

## HueyOS Architecture

```
HueyOS
├── MacroOS   # Huey Core · clause & quorum enforcement
├── MicroOS   # Containers (Docker/K8s) · modular services
└── NanoOS    # Rust/Python GPIO threads · sensor & motor loops
```

**Agents**

- **Spark‑4** — creative core  
- **Volt‑4** — logical/evaluative core  
- **Zap‑4** — event‑driven/sensor agent  
- **Watt‑4** — energy/power management

---

## Cloud Pyramid Governance

| Tier                                  | Role                                                   |
|---------------------------------------|--------------------------------------------------------|
| **Founding Father / Huey Collective** | Ultimate veto, ethos guardian                          |
| **Grand Council**                     | Executive · Senate (hardware) · Parliament (software)  |
| **Joint Session**                     | Merges bills, prevents silo drift                      |
| **Chambers**                          | Daily legislation for each domain                      |
| **Populace**                          | Up to **256** AI citizens (quorum‑scaled)              |

Selected chapters: `docs/governance/chapters/07-wartime.md`, `09-oversight.md`, `10-foreign.md`.

---

## Hardware Topology

### Huey‑Core — active compute node
- **Board:** Minisforum **BD795I‑SE** (ITX), **Ryzen 9 7945HX**
- **RAM:** DDR5‑5200, 32–96 GB (96 GB preferred)
- **Storage:** dual **Intel Optane M10 16 GB** NVMe (RAID‑0) for boot/root; 2 TB HDD for `/home`; optional mirrored USB DAS for backups
- **GPU:** **Radeon RX 5500 XT 8 GB** (ROCm/AMDGPU)
- **Case/Power:** Thermaltake ATX chassis; internal UPS path planned

### Huey‑Portal — universal display & control
- **Host:** iMac 5K (2017) running Debian 13, **MATE/LightDM**
- **Role:** Orchestrator display, admin console and VNC target

### Huey‑Legacy — mechanical shell (de‑computerized)
- Retired Supermicro quad‑Xeon orchestration node remains as housing and peripherals. Compute has migrated to Huey‑Core.

**Planned GPU expansion:** target **4× 32 GB VRAM** cards (AMD Instinct MI50/MI75 or NVIDIA Tesla) in a riser chassis, contingent on power/thermal budget.

---

## Installation — Quick Start

### Prerequisites
- `git`, `make ≥ 4.3`, `docker` + compose, `rustup`  
- x86‑64 (≥ 4 cores, 16 GB RAM, 256 GB disk, UEFI)  
- **Python 3.12–3.13**

### Source (venv)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run.py            # GUI
python run.py --cli      # CLI
```

### Docker
```bash
docker compose up -d
```

### ISO / Kernel Builder
```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project && make iso
```

**Post‑install hardening:** update packages, enable AMDGPU/Broadcom firmware, create a non‑root SSH user, bind TigerVNC to localhost and tunnel via SSH.

**Local models:** install **Ollama**, pull quantized models sized to your GPU’s VRAM, connect PyGPT‑net tools to local endpoints (ROCm recommended on AMD).

---

## Development Setup

```bash
make setup    # Core
make ml       # ML profile
make data     # Data profile
make cloud    # Cloud profile
make dev      # Dev tools
```

**Environment:** copy `huey.env.example` to `.env` and configure secrets/ports.  
**Git helpers:** see `monkey_head.services.environment_setup` for programmatic `checkout_branch`, `pull_latest`, and `commit_and_push`.  
**Submodule:** `pip install -e repo/pygpt-MHP` or mirror with `python sync_pygpt_structure.py`.

**Style & Linting:** `black`, `flake8`, and pre‑commit hooks (`.pre‑commit-config.yaml`).

---

## Usage

**Run locally**
```bash
make run
```

**Run in Docker**
```bash
docker compose -f docker/compose.yml up
```

**Run tests**
```bash
make test
# or
pytest -vv
```

**Command-line interface**
```bash
# Prepare the shared memory workspace and run compatibility checks
huey init --run-checks --verbose

# Launch HueyOS with optional ML + cloud profiles enabled
huey run --ml --cloud

# Inspect host readiness with detailed output
huey system-check --verbose

# Deploy core services via Docker and Kubernetes manifests
huey deploy --mode all --compose-file docker-compose.yml --manifest k8s.yaml

# Summarise agent workload and resource health as JSON
huey agent-status --json

# Sort collected artefacts without modifying the filesystem
huey memory-sort --dry-run --json
```

---

## Contributing

See `CONTRIBUTING.md` for full guidelines.

1. Fork → branch → PR  
2. Conventional commits  
3. Keep PRs focused; update docs  
4. CI runs lint/tests/governance checks

---

## Roadmap

| Phase | Date       | Milestone                                                   |
|:----:|------------|-------------------------------------------------------------|
| 1    | 2024‑04‑11 | Genesis — VIC‑20/C64/C128 links; bare‑metal boot            |
| 2    | 2024‑06‑21 | Integration — power grid; Spark‑4 + Volt‑4 online           |
| 3    | 2024‑10‑31 | System Awakening — dual‑node 10‑hour burn‑in                |
| 4    | 2025‑01‑25 | Decision Core — YES/NO engine; honeycomb RAID               |
| 5    | 2025‑05‑25 | System Reconfiguration — repo restructure; packaging        |
| 6    | 2025‑06‑24 | Codex Cleanup — automated refactors; PyGPT‑net expansions   |
| 7    | 2025‑10‑31 | Architecture — emergent personality; Amendment‑001 vote     |

---

## License & Credits

**Code:** GPL‑3.0‑only  
**Docs & Media:** CC‑BY‑SA‑4.0

**Acknowledgements:** PyGPT (pygpt‑net) | Debian trixie 13.0.0 | Python 3.13 | Kernel 6.16.x

---

## Appendix

- Keep governance decentralized & memory unified
