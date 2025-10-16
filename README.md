# 🐒 Monkey Head Project – HueyOS

**Author:** Dylan L. R. Pollock  
**Status date:** 05-10-2025
**Official site:** [www.dlrp.ca](https://www.dlrp.ca)
**Contact:** [admin@dlrp.ca](mailto:admin@dlrp.ca)

> **HueyOS** is a prototype robotic AI/OS that marries retro computing legacies with modern, modular hardware and a living constitutional framework. Huey is transparent by design, modular by necessity, and governed—not merely programmed—by the **Cloud Pyramid**.

(UEFI-only - amd64 - Kernel 6.16.12 → staging 6.17.x - Debian 13.0.0 Trixie / Debian 14 “Forky” pilots)

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.12–3.14-blue)
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
- [Documentation portal](docs/index.md)
- [Official website](https://www.dlrp.ca)

---

## Overview

HueyOS targets **Debian 13 “Trixie”** with a custom low‑latency kernel series **6.16.12‑huey** while the next milestone actively migrates the stack to **Debian “Forky”** with kernel **6.17.x**. It unifies modern AI agents, a codified constitutional framework, and retro hardware support in a single modular platform. Headless and GUI modes are supported.

**Highlights (as of 2025‑10‑05):**

- **OS baseline:** Debian 13.0.0 (Trixie), custom kernel **6.16.12‑huey** → transitioning to **Debian 14 “Forky”** with kernel **6.17.x-huey** (certification window opened **2025‑10‑31**)
- **Python:** current pin **3.13.5** with **3.14.x** staged for general availability after **2025‑10‑31** (upgrade path validated in Docker + installer; PyGPT‑net + bridge wheels verified for 3.14 markers)
- **Desktop:** **MATE** + **LightDM**; preferred lightweight browser: **qutebrowser**; full browser: **Edge Dev**
- **AI runtime:** **PyGPT‑net** (desktop orchestrator), **Ollama** (local LLMs), ROCm/AMDGPU where available
- **Memory:** unified long‑term store via JSON logs + SQLite; reproducible telemetry; VNC via TigerVNC tunneled over SSH
- **Networking:** prefer bonded Ethernet; Wi‑Fi only as fallback

> **Lifecycle notice (2025‑11‑15):** Upstream kernel **6.16.x** has entered end‑of‑life. HueyOS is actively switching its baseline to **kernel 6.17.x** on **Debian “Forky”**, keeping **6.16.12/Trixie** builds online only until migration certification completes. Python **3.14.x** replaces the interim **3.13.x** builds following the same certification gate.

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
| `Dockerfile`              | Container image definition for HueyOS services          |
| `docker-compose.yml`      | Docker Compose stack (API, worker, optional Redis)      |
| `docker/`                 | Legacy orchestrator assets and experimental builds      |
| `docs/`                   | Constitution, governance, architecture                  |
| `huey/`                   | Core runtime and service modules                        |
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
- **Python 3.12–3.14** (3.14 binaries roll out after the 2025‑10‑31 gate)

### Source installation
```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .              # core runtime
# Optional extras
pip install -e '.[ml]'       # machine-learning toolchain
pip install -e '.[data]'     # vector DB integrations
pip install -e '.[cloud]'    # Azure/AWS helpers

# Configure environment secrets if needed
cp huey.env.example .env
```

### First boot
```bash
# Prepare the memory hive and confirm compatibility
huey init --run-checks --verbose

# Launch the multi-agent runtime (CLI fallback enabled by default)
huey run --ml --cloud

# Start the FastAPI control surface on http://127.0.0.1:8000
uvicorn huey.api:app --reload
```

### Docker
```bash
# Build with the default ML, data, and cloud profiles baked into the image
docker compose build
# Launch the API and (optionally) enable additional profiles via --profile
docker compose up -d
```

Set `HUEY_BUILD_EXTRAS` (for example, `HUEY_BUILD_EXTRAS=ml`) before running
`docker compose build` to tailor which optional dependency groups are installed
into the container image. Runtime-only tweaks can be made with Compose profiles
(`docker compose --profile worker up`) without rebuilding the image.

### ISO / Kernel builder
```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project && make iso
```

**Post-install hardening:** update packages, enable AMDGPU/Broadcom firmware, create a non-root SSH user, bind TigerVNC to localhost and tunnel via SSH.

**Local models:** install **Ollama**, pull quantized models sized to your GPU’s VRAM, connect PyGPT-net tools to local endpoints (ROCm recommended on AMD).
---

## Development Setup

```bash
make setup                       # Editable install of the core package
make setup SETUP_EXTRAS=dev      # Install with dev tooling extras
make ml                          # Install ML profile extras and run a smoke test
make data                        # Install data profile extras and run a smoke test
make cloud                       # Install cloud profile extras and run a smoke test
make dev                         # Install dev extras, format, lint, and test
make dev DEV_OPTIONAL_PROFILES=ml,data  # Include optional profiles in dev setup
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
docker compose up
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

### API quick start

Use `uvicorn huey.api:app --reload` to expose the FastAPI control surface on `http://127.0.0.1:8000`. The [API reference](docs/api-reference.md) includes `curl` recipes for every endpoint, covering task scheduling, sensor telemetry, honeycomb reports, governance workflows, and crash recovery tooling.

### Sensor plugin development

To extend HueyOS with custom telemetry, follow the workflow described in [`docs/sensor-plugins.md`](docs/sensor-plugins.md). The sensor manager persists readings into the honeycomb store automatically, making them available through the `/sensors/*` API family.

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

**Acknowledgements:** PyGPT (pygpt‑net) | Debian trixie 13.0.0 → Debian forky pilots | Python 3.13 → 3.14 staging | Kernel 6.16.12 → 6.17.x

---

## Appendix

- Keep governance decentralized & memory unified
