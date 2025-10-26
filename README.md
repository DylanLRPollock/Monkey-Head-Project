# 🐒 Monkey Head Project – HueyOS

**Author:** Dylan L. R. Pollock
**Status date:** 2025‑10‑25
**Official site:** [www.dlrp.ca](https://www.dlrp.ca)
**Contact:** [admin@dlrp.ca](mailto:admin@dlrp.ca)

> **HueyOS** is a prototype robotic AI/OS that marries retro‑computing legacies with modern, modular hardware and a living constitutional framework. Huey is transparent by design, modular by necessity, and governed—not merely programmed—by the **Cloud Pyramid**.

*(UEFI‑only · amd64 · Kernel 6.16.12‑huey → staging 6.17.x · Debian 13.0.0 “Trixie” / Debian 14 “Forky” pilots)*

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.12–3.14-blue)
$1> ### 🚨 October 31, 2025 — Changeover

> On **October 31, 2025**, HueyOS will land major software changes (Forky + 6.17.x + Python 3.14 baseline, plus packaging/CLI updates). **Stay tuned** here and in `docs/releases/2025-10-31-changeover.md` for full details.

---

## 📌 Quick Links

* [Overview](#overview)
* [Repository Structure](#repository-structure)
* [Architecture](#hueyos-architecture)
* [Governance](#cloud-pyramid-governance)
* [Hardware Topology](#hardware-topology)
* [Installation & Quick Start](#installation--quick-start)
* [Development Setup](#development-setup)
* [Usage](#usage)
* [Feature Matrix](#feature-matrix)
* [Known Issues](#known-issues)
* [Roadmap](#roadmap)
* [License & Credits](#license--credits)
* [Documentation portal](docs/index.md)
* [Official website](https://www.dlrp.ca)

---

## Overview

HueyOS targets **Debian 13 “Trixie”** with a custom low‑latency kernel series **6.16.12‑huey**, while the next milestone actively migrates the stack to **Debian 14 “Forky”** with kernel **6.17.x**. It unifies modern AI agents, a codified constitutional framework, and retro hardware support in a single modular platform. Headless and GUI modes are supported.

**Highlights (as of 2025‑10‑25):**

* **OS baseline:** Debian 13.0.0 (Trixie), custom kernel **6.16.12‑huey** → transitioning to **Debian 14 “Forky”** with kernel **6.17.x‑huey** — **changeover on October 31, 2025** *(certification window opens **2025‑10‑31**; rollout details will be posted—stay tuned).*
* **Python:** current pin **3.13.5** with **3.14.x** staged for general availability after **2025‑10‑31** *(upgrade path validated in Docker + installer; PyGPT‑net bridge wheels verified for 3.14 markers).*
* **Desktop:** **MATE** + **LightDM**; preferred lightweight browser: **qutebrowser**; full browser: **Edge Dev**.
* **AI runtime:** **PyGPT‑net** (desktop orchestrator) + **Ollama** (local LLMs), ROCm/AMDGPU where available; Vulkan fallback acceptable.
* **Memory:** unified long‑term store via JSON logs + SQLite; reproducible telemetry; **TigerVNC** bound to localhost and tunneled over SSH.
* **Networking:** prefer bonded Ethernet (LACP or adaptive load‑balancing); Wi‑Fi only as fallback.

> **Lifecycle notice (scheduled: 2025‑11‑15):** Upstream **6.16.x** is expected to enter end‑of‑life. HueyOS is switching its baseline to **6.17.x** on **Debian “Forky.”** The **6.16.12/Trixie** line remains supported only until migration certification completes. Python **3.14.x** replaces the interim **3.13.x** builds following the same certification gate.

**Core Principles**

| Principle         | Operational intent                                              |
| ----------------- | --------------------------------------------------------------- |
| **Autonomy**      | Every action must trace to a ratified clause.                   |
| **Modularity**    | Swap hardware/software without refactoring.                     |
| **Expandability** | Ready for GPU packs, future accelerators, and new agents.       |
| **Open Ethos**    | Source, schematics, telemetry, and votes are public by default. |

---

## 🗓️ October 31, 2025 — Changeover Plan

**What’s changing**

* Default OS: **Debian 14 “Forky.”**
* Kernel baseline: **6.17.x‑huey** low‑latency series.
* Python baseline: **3.14.x** (new virtualenvs required).
* Packaging: signed `.deb` artifacts + refreshed ISO builder outputs.
* Services: FastAPI control surface hardened; governance dashboards exposed at `/governance/*`.
* Boot visuals: no splash by default; verbose console logs preserved.

**Upgrade path (Trixie/6.16.12 → Forky/6.17.x)**

```bash
# 0) Back up config & env
sudo rsync -aHAX --info=progress2 /etc/ /root/backup/etc-$(date +%F)/
cp -a .env /root/backup/huey-env-$(date +%F) || true

# 1) Update to Forky (example – adapt to your APT style)
# Backup APT lists, then adjust sources to 'forky'
sudo cp -a /etc/apt/sources.list.d /root/apt-backup-$(date +%F)
sudo apt update && sudo apt -y full-upgrade

# 2) Install Huey kernel (either via our signed .deb or distro kernel)
# If you built packages locally:
sudo dpkg -i ~/kernels/linux-image-6.17.*huey_*.deb ~/kernels/linux-headers-6.17.*huey_*.deb || true
# Otherwise, use the distro's 6.17.x and apply Huey tweaks post-boot

# 3) Ensure firmware
sudo apt -y install firmware-linux firmware-amd-graphics firmware-iwlwifi

# 4) Reboot and verify
uname -r
```

**Re-create the Python environment (3.14)**

```bash
deactivate 2>/dev/null || true
rm -rf .venv
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . '.[ml,data,cloud]'
```

**Rollback**

* Keep your previous kernel listed in GRUB.
* Retain `/root/apt-backup-*` to revert sources.
* Your `.env` backup allows immediate downgrade to prior runtime.

> **Stay tuned**: full, version‑locked release notes will publish on **October 31, 2025** in `docs/releases/2025-10-31-changeover.md`.

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
| `huey/`                   | Core runtime and service modules                     |
| `huey/api/`               | FastAPI surface                                      |
| `setup/`                  | Installer scripts, ISO builder, provisioning configs |
| `src/`                    | Python package source                                |
| `tests/`                  | Unit & integration tests                             |
| `repo/pygpt-MHP`          | Submodule: PyGPT‑net integration                     |
| `k8s/`                    | (Optional) Kubernetes manifests                      |
| `Makefile`                | Common developer commands                            |
| `pyproject.toml`          | Project metadata & dependencies                      |
| `requirements.txt`        | Aggregate Python dependencies                        |
| `.pre-commit-config.yaml` | Pre‑commit hooks                                     |
| `huey.env.example`        | Example environment variables                        |
| `LICENSE`                 | GPL‑3.0‑only (code), CC‑BY‑SA‑4.0 (docs/media)       |

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

* **Spark‑4** — creative core
* **Volt‑4** — logical/evaluative core
* **Zap‑4** — event‑driven/sensor agent
* **Watt‑4** — energy/power management

**Services** (indicative)

* **Governance kernel:** clause registry, voting/quorum, audit trail.
* **Memory hive:** JSON logs + SQLite, append‑only, queryable.
* **Interface:** TTS/STT (optional), CLI + FastAPI control surface.
* **Adapter layer:** drivers for sensors, GPIO, and external tools (PyGPT‑net tools, Ollama endpoints, VNC helpers).

---

## Cloud Pyramid Governance

| Tier                                  | Role                                                    |
| ------------------------------------- | ------------------------------------------------------- |
| **Founding Father / Huey Collective** | Ultimate veto; ethos guardian; emergency brakes         |
| **Grand Council**                     | Executive; Senate (hardware) + Parliament (software)    |
| **Joint Session**                     | Merges bills; prevents domain drift                     |
| **Chambers**                          | Daily legislation per domain (IO, Memory, Motion, etc.) |
| **Populace**                          | Up to **256** AI citizens (quorum‑scaled)               |

Selected chapters: `docs/governance/chapters/07-wartime.md`, `09-oversight.md`, `10-foreign.md`.

---

## Hardware Topology

### Huey‑Core — active compute node

* **Board:** Minisforum **BD795I‑SE** (ITX), **Ryzen 9 7945HX**
* **RAM:** DDR5‑5200, 32–96 GB *(96 GB preferred)*
* **Storage:** dual **Intel Optane M10 16 GB** NVMe (RAID‑0) for boot/root; 2 TB HDD for `/home`; optional mirrored USB DAS for backups
* **GPU:** **Radeon RX 5500 XT 8 GB** (AMDGPU; ROCm where supported; Vulkan fallback)
* **Case/Power:** Thermaltake ATX chassis; internal UPS path planned

### Huey‑Portal — universal display & control

* **Host:** iMac 5K (2017), Debian 13, **MATE/LightDM**
* **Role:** Orchestrator display, admin console, **TigerVNC** target (bound to localhost; SSH tunnel only)

### Huey‑Portable — field node *(lightweight)*

* **Device:** ASUS BR1100FKA 11.6" 2‑in‑1, Intel N4500, 4 GB RAM, 128 GB eMMC, LTE
* **OS:** Debian 13; custom kernel in progress
* **Notes:** Always‑online backup path via LTE; planned NVMe upgrade when feasible

### Huey‑Legacy — mechanical shell (de‑computerized)

* Retired Supermicro quad‑Xeon orchestration node remains as housing/peripherals. Compute has migrated to Huey‑Core.

**Planned GPU expansion:** target **4× 32 GB VRAM** cards (AMD Instinct MI50/MI75 or NVIDIA Tesla) in a riser chassis, subject to power/thermals.

---

## Installation & Quick Start

### Prerequisites

* `git`, `make ≥ 4.3`, `docker` + compose, `rustup`
* x86‑64 host (≥ 4 cores, 16 GB RAM, 256 GB disk, UEFI)
* **Python 3.12–3.14** *(3.14 wheels released after the 2025‑10‑31 gate)*

### Source installation

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .                # core runtime
# Optional extras
pip install -e '.[ml]'          # machine-learning toolchain
pip install -e '.[data]'        # vector DB integrations
pip install -e '.[cloud]'       # Azure/AWS helpers

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
# Build with default ML, data, and cloud profiles baked in
docker compose build
# Launch the API and (optionally) enable extra profiles via --profile
docker compose up -d
```

Set `HUEY_BUILD_EXTRAS` (e.g., `HUEY_BUILD_EXTRAS=ml`) before `docker compose build` to control optional dependency groups. Runtime‑only toggles can use Compose profiles (`docker compose --profile worker up`) without rebuilding.

### ISO / Kernel builder

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project && make iso
```

**Post‑install hardening**

* Update packages; enable firmware (AMDGPU, Broadcom/Intel Wi‑Fi if needed).
* Create a non‑root SSH user; disable password SSH; enforce key‑only.
* Bind **TigerVNC** to `localhost` on a fixed port (e.g., `1995`); access via SSH tunnel only.
* Prefer bonded Ethernet (LACP/ALB); keep Wi‑Fi as contingency.

**Local models**

* Install **Ollama**; pull quantized models sized to your GPU VRAM.
* Wire **PyGPT‑net** tools to local endpoints.
* Prefer ROCm on AMD; otherwise use Vulkan backend.

**Quick recipes**

*Bonded Ethernet (NetworkManager)*

```bash
nmcli con add type bond ifname bond0 mode 802.3ad
nmcli con add type ethernet ifname enp193s0f0 master bond0
nmcli con add type ethernet ifname enp193s0f1 master bond0
nmcli con mod bond0 ipv4.method auto
nmcli con up bond0
```

*TigerVNC over SSH*

```bash
ssh -N -L 1995:127.0.0.1:1995 dlrp@huey-legacy
vncviewer 127.0.0.1:1995
```

*Ollama Vulkan on AMD*

```bash
export OLLAMA_LLM_LIBRARY=vulkan
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json
ollama serve
```

---

## Development Setup

```bash
make setup                            # Editable install of the core package
make setup SETUP_EXTRAS=dev           # Install with dev tooling extras
make ml                               # Install ML profile extras and smoke test
make data                             # Install data profile extras and smoke test
make cloud                            # Install cloud profile extras and smoke test
make dev                              # Install dev extras, format, lint, and test
make dev DEV_OPTIONAL_PROFILES=ml,data  # Include optional profiles in dev setup
```

**Environment:** copy `huey.env.example` → `.env` and configure secrets/ports.
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

**Command‑line interface** *(targets under active build; some flags may be preview)*

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

# Sort collected artifacts without modifying the filesystem
huey memory-sort --dry-run --json
```

### API quick start

Use `uvicorn huey.api:app --reload` to expose the FastAPI control surface on `http://127.0.0.1:8000`. See [docs/api-reference.md](docs/api-reference.md) for `curl` recipes covering task scheduling, sensor telemetry, honeycomb reports, governance workflows, and crash‑recovery tooling.

### Sensor plugin development

Follow [`docs/sensor-plugins.md`](docs/sensor-plugins.md). The sensor manager persists readings into the honeycomb store automatically, making them available via the `/sensors/*` API family.

---

## Feature Matrix

| Area        | Now (Trixie · 6.16.12)            | Next (Forky · 6.17.x)                          | Later |
| ----------- | --------------------------------- | ---------------------------------------------- | ----- |
| Kernel      | Low‑latency config; AMDGPU stable | ROCm/Vulkan tuning; iMac 5K audio refinements  | 6.18+ |
| Python      | 3.13.5 baseline                   | 3.14.x GA after 2025‑10‑31                     | —     |
| AI runtime  | PyGPT‑net + Ollama (quantized)    | Model zoo profiles; agent orchestration polish | —     |
| Memory hive | JSON + SQLite                     | Roll‑up analytics; retention policies          | —     |
| Networking  | Bonded Ethernet; VNC over SSH     | Policy‑driven WAN fallback (LTE)               | —     |
| Governance  | Clause registry + audits          | Amendment‑001 vote; live quorum dashboards     | —     |
| Packaging   | Editable install + Docker         | ISO builder polish; signed artifacts           | —     |

---

## Known Issues

* **iMac 5K (2017) audio quirks** under certain 6.17.x builds; mitigation scripts exist, long‑term fix tracked under kernel migration tasks.
* **Edge repo keys** on Debian *Forky* may require re‑import during upgrades; monitor for signature policy changes.
* **Vulkan/ROCm selection**: some GPUs prefer explicit `VK_ICD_FILENAMES`/backend env vars; see notes in `docs/`.
* **Mixed‑media RAID auto‑assembly** (Optane + eMMC/HDD) can create phantom arrays. Workaround: set `AUTO -all` in `/etc/mdadm/mdadm.conf` and zero stale superblocks; see `docs/storage.md`.
* **BR1100FKA sensors**: orientation via `iio-sensor-proxy` may lag; tuned polling defaults are shipping with 6.17.x notes.
* **Boot splash removal**: ensure `GRUB_CMDLINE_LINUX_DEFAULT` omits `quiet splash`; run `sudo update-grub` to keep console logs visible.

---

## Roadmap

| Phase | Date       | Milestone                                                 |
| :---: | ---------- | --------------------------------------------------------- |
|   1   | 2024‑04‑11 | Genesis — VIC‑20/C64/C128 links; bare‑metal boot          |
|   2   | 2024‑06‑21 | Integration — power grid; Spark‑4 + Volt‑4 online         |
|   3   | 2024‑10‑31 | System Awakening — dual‑node 10‑hour burn‑in              |
|   4   | 2025‑01‑25 | Decision Core — YES/NO engine; honeycomb RAID             |
|   5   | 2025‑05‑25 | System Reconfiguration — repo restructure; packaging      |
|   6   | 2025‑06‑24 | Codex Cleanup — automated refactors; PyGPT‑net expansions |
|   7   | 2025‑10‑31 | Architecture — emergent personality; Amendment‑001 vote   |

---

## License & Credits

**Code:** GPL‑3.0‑only
**Docs & Media:** CC‑BY‑SA‑4.0

**Acknowledgements:** PyGPT (pygpt‑net) · Debian 13 “Trixie” → Debian 14 “Forky” pilots · Python 3.13 → 3.14 staging · Kernel 6.16.12 → 6.17.x

---

## Appendix

* VNC workflow defaults: **TigerVNC** on Huey‑Legacy (GNOME on Xorg) bound to `localhost:1995`, no on‑screen prompt (`-SecurityTypes None`), SSH tunnel only.
* Keep governance **decentralized** & memory **unified**.
