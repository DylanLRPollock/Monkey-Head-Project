# HueyOS — Monkey‑Head‑Project

**Project:** Monkey‑Head‑Project (HueyOS)  
**Author:** Dylan L. R. Pollock  
**Official site:** https://www.dlrp.ca  
**Contact:** admin@dlrp.ca  
**License:** Code: GPL‑3.0 • Docs/Media: CC‑BY‑SA‑4.0  
**Status date:** 2025‑10‑25

> HueyOS is a modular robotic AI/OS that blends retro‑computing aesthetics with modern Linux, clustered compute, and a constitutional governance model (the **Cloud Pyramid**). It operates offline‑first with optional API use. **Governance remains decentralized while memory remains unified.**

![License](https://img.shields.io/badge/license-GPLv3-blue)
![Python](https://img.shields.io/badge/python-3.12–3.14-blue)

---

## October 31, 2025 — Changeover Notice

On **2025‑10‑31**, HueyOS migrates to **Debian 14 “Forky,” kernel 6.17.x‑huey, and Python 3.14.x** (with packaging and CLI updates). Full notes will ship in `docs/releases/2025-10-31-changeover.md`. Until then, the baseline is **Debian 13 “Trixie” + 6.16.x‑huey**.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Architecture](#architecture)
- [Hardware](#hardware)
- [Software Stack](#software-stack)
- [Installation & Quick Start](#installation--quick-start)
- [Build Guides](#build-guides)
- [Governance & Constitution](#governance--constitution)
- [Memory & Data Model](#memory--data-model)
- [Remote Access (VNC/SSH)](#remote-access-vncssh)
- [Action Plan — Oct 31, 2025](#action-plan--oct-31-2025)
- [Roadmap & Pre‑Releases](#roadmap--pre-releases)
- [Development Setup](#development-setup)
- [Usage](#usage)
- [Feature Matrix](#feature-matrix)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License & Credits](#license--credits)
- [Appendix](#appendix)

---

## Overview

HueyOS targets **Debian 13 “Trixie”** today with a low‑latency **6.16.x‑huey** kernel while staging migration to **Debian 14 “Forky”** and **6.17.x‑huey** on **2025‑10‑31**. It unifies modern AI agents, a codified constitutional framework, and retro hardware support in a single modular platform. Both headless and GUI deployments are supported.

**Highlights (as of 2025‑10‑25)**

- **OS baseline:** Debian 13.0.0 (Trixie) → changeover to **Debian 14 “Forky”** begins **2025‑10‑31**.  
- **Kernel:** 6.16.x‑huey → **6.17.x‑huey** (low‑latency, targeted drivers).  
- **Python:** 3.13.x now; **3.14.x** becomes baseline post‑changeover.  
- **Runtime:** **PyGPT‑net** (orchestrator) + **Ollama** (local LLMs); ROCm/Vulkan where available.  
- **Memory:** unified long‑term store via JSON logs + SQLite with reproducible telemetry.  
- **Networking:** bonded Ethernet preferred; Wi‑Fi fallback; **TigerVNC** bound to localhost via SSH.

Core principles: **autonomy**, **modularity**, **expandability**, **open ethos**.

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
| `k8s/`                    | Optional Kubernetes manifests                        |
| `Makefile`                | Common developer commands                            |
| `pyproject.toml`          | Project metadata & dependencies                      |
| `requirements.txt`        | Aggregate Python dependencies                        |
| `.pre-commit-config.yaml` | Pre‑commit hooks                                     |
| `huey.env.example`        | Example environment variables                        |
| `LICENSE`                 | GPL‑3.0‑only (code), CC‑BY‑SA‑4.0 (docs/media)       |

> Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch `repo/pygpt-MHP`.

---

## Architecture

Huey’s architecture is a layered federation aligning compute, memory, and governance.

### Layers

1. **Huey as Sovereign Consciousness** — emergent, lawful decision and inaction boundary.  
2. **Binary Brain** — *Spark* (creative, GPU‑1) and *Zap* (evaluative, GPU‑2) form a bicameral AI core.  
3. **Citizen Populace** — up to **256** AI instances (128 per core) acting as civic units with voting and operational roles.  
4. **Worker Subsystems** — NanoOS/SubOS services for sensors, limbs, and IO without clause power.

### Agents & Services (indicative)

- **Spark‑4** — creative core; **Volt‑4** — evaluative; **Zap‑4** — event/sensor; **Watt‑4** — energy.  
- **Governance kernel:** clause registry, voting/quorum, audit trail.  
- **Memory hive:** JSON logs + SQLite; append‑only, queryable.  
- **Interface:** optional TTS/STT; CLI + FastAPI control surface.  
- **Adapter layer:** sensor/GPIO drivers; PyGPT‑net tools; Ollama endpoints.

### Principles

- **Decentralized governance; unified memory.**  
- Offline‑first; API‑capable.  
- Traceable action history; reproducible state.  
- Clear separation: governance vs actuation; data vs policy.

---

## Hardware

### Nodes (current roster)

- **Huey Prime** — orchestration hub (Thermaltake ATX; ITX **BD795I‑SE**, Ryzen 9 7945HX; DDR5‑5200; dual Intel Optane M10 16 GB NVMe; GPU: **Radeon RX 5500 XT 8 GB** now, **MI50** planned).  
- **Huey‑Legacy (Robotic Shell)** — on hold; houses **Supermicro X9QRI‑F+** quad‑Xeon board (file hub candidate), 10 GbE NIC; GPUs; RAID SSDs.  
- **Huey‑Portal** — iMac 5K (2017; 48 GB RAM; Debian Trixie); universal display/control; **GNOME on Xorg**.  
- **Huey‑Portable** — ASUS BR1100FKA 11.6" (N4500, 4 GB, LTE); Debian Trixie; portable node.  
- **Huey‑Hub** — 2017 MacBook Pro (Windows 10 bare metal) for file transfers + 10 TB mirrored WD MyBook Duo.

### Remote Intent & Action

- **RF Remote (IC2262/2272)** → **Arduino UNO** (USB symbolic intents: LISTEN, VOTE:YES/NO).  
- **Arduino Mega 2560** → motors/sensors (PWM/I²C).  
- **Arduino Nanos** → localized LED/analog/PWM conditioning.

### Display

- iMac 5K (Portal) + 27" Samsung C27F396 portrait (torso). Future: **Neo C128** board for VIC‑II/SID.

### Network

- Router: **ASUS GT‑AC5300** (link aggregation). Preferred: bonded Ethernet; Wi‑Fi fallback.

---

## Software Stack

- **OS:** Debian 13 (Trixie) → **Debian 14 (Forky)** adoption begins 2025‑10‑31.  
- **Kernel:** 6.16.x‑huey → **6.17.x‑huey** (custom; performance‑oriented; targeted drivers).  
- **AI:** Ollama (local LLMs; Mistral‑7B quant), PyGPT‑net agents; Whisper STT; TTS module.  
- **UI:** Minimalist green‑on‑black; two‑pane logic (conscious voice vs verbose logs).  
- **Memory:** JSON logs + SQLite; unified store; long‑term persistence.  
- **Security:** SSH keys; optional default lab key (rotatable); fallback **LIVE** USB.

### Folder Conventions

```
/huey/
  bin/           # launchers and maintenance scripts
  kernels/       # packaged kernels, configs, build logs
  memory/        # sqlite, json logs, vectors (later)
  services/      # systemd units, timers
  ui/            # themes, boot assets, display scripts
  docs/          # project docs (this wiki mirrors)
```

---

## Installation & Quick Start

### Supported Targets (current focus)

- **Debian 13 (Trixie)** — baseline; UEFI‑only; amd64.  
- **Debian 14 (Forky)** — staged adoption for the Oct‑31 update.  
- **Linux Kernels:** 6.16.x‑huey (current), 6.17.x‑huey (incoming).

### Minimal Install

1. Install Debian (UEFI, amd64). Choose **GNOME on Xorg** for iMac 5K targets.  
2. Enable non‑free firmware (Realtek, Intel, etc.).  
3. Create user `dlrp` (or custom) and enable sudo.  
4. Prefer **bonded Ethernet**; use Wi‑Fi as fallback.  
5. Post‑install: `apt update && apt full-upgrade`.

### Core Packages (baseline)

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
pip install -e .                 # core runtime
pip install -e '.[ml]'           # machine-learning toolchain
pip install -e '.[data]'         # vector DB integrations
pip install -e '.[cloud]'        # cloud helpers

# Configure environment secrets if needed
cp huey.env.example .env
```

### First Boot

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

Set `HUEY_BUILD_EXTRAS` (e.g., `HUEY_BUILD_EXTRAS=ml`) before `docker compose build` to control optional dependency groups.

---

## Build Guides

### Kernel 6.17.x‑huey (generic; adjust per target)

```bash
# deps (see Installation for base set)
sudo apt install -y fakeroot kmod pahole flex bison libelf-dev libssl-dev \
  libncurses-dev bc rsync xz-utils cpio python3

# source (example)
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.17.5.tar.xz
 tar -xf linux-6.17.5.tar.xz && cd linux-6.17.5

# seed config from running kernel, then refresh
cp -v /boot/config-$(uname -r) .config
yes "" | make olddefconfig

# huey perf toggles (examples; tune per target)
./scripts/config --disable DEBUG_INFO --disable DEBUG_INFO_BTF \
  --disable KASAN --disable UBSAN --disable KCOV --disable FUNCTION_TRACER \
  --enable ZSTD --enable RD_ZSTD --enable EFI --enable EFI_STUB --enable EFI_VARS

# build Debian packages
make -j$(nproc) bindeb-pkg

# install
sudo dpkg -i ../linux-image-6.17.5-*.deb ../linux-headers-6.17.5-*.deb
sudo update-initramfs -c -k 6.17.5
sudo update-grub
```

#### iMac 5K (2017) — Notes

- **GNOME on Xorg** recommended.  
- Optionally force display mode via kernel cmdline (HDMI‑A‑1 1080p60 during boot).  
- Audio: prefer PipeWire; set default sink on login.

```bash
# set default HDA PCH sink after login
mkdir -p ~/.local/bin
cat > ~/.local/bin/set-default-sink.sh <<'EOF'
#!/usr/bin/env bash
sleep 3
SINK=$(pactl list short sinks | awk '/pci-0000_00_1f\.3.*analog/ {print $1; exit}')
[ -n "$SINK" ] && pactl set-default-sink "$SINK" && pactl set-sink-mute "$SINK" 0 && pactl set-sink-volume "$SINK" 60%
EOF
chmod +x ~/.local/bin/set-default-sink.sh
```

### Remove Splash / Show Boot Logs

```bash
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="loglevel=4 systemd.show_status=1"/' /etc/default/grub
sudo update-grub
```

### Microsoft Edge (Beta) — Repository Key (keyrings + signed‑by)

```bash
sudo install -d -m0755 /etc/apt/keyrings
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | \
  gpg --dearmor | sudo tee /etc/apt/keyrings/microsoft.gpg >/dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] \
https://packages.microsoft.com/repos/edge stable main" | \
  sudo tee /etc/apt/sources.list.d/microsoft-edge.list >/dev/null

sudo apt update
```

### RAID Superblock Cleanup (when reverting experiments)

```bash
cat /proc/mdstat
sudo mdadm --detail --scan
lsblk -o NAME,TYPE,SIZE,MOUNTPOINTS

# stop any auto-assembled arrays
sudo mdadm --stop --scan || true

# find and remove stale superblocks (replace partitions with actual ones)
sudo mdadm --examine /dev/nvme0n1p3 && sudo mdadm --zero-superblock /dev/nvme0n1p3
sudo mdadm --examine /dev/mmcblk0p3 && sudo mdadm --zero-superblock /dev/mmcblk0p3

echo 'AUTO -all' | sudo tee /etc/mdadm/mdadm.conf
sudo update-initramfs -u
```

### Ollama on AMD (force RADV/Vulkan)

```bash
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json
export OLLAMA_LLM_LIBRARY=vulkan
export VK_LOADER_DEBUG=all
export OLLAMA_DEBUG=1
ollama serve
```

### Huey‑Portable — Default Deep Sleep

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

### Cloud Pyramid — Summary

- **Clause‑based activation:** policies trigger agent powers.  
- **Quorum:** decisions derive from Spark/Zap plus citizens; deterministic tie‑breakers.  
- **Separation:** governance (what *should*) vs actuator (what *is done*).  
- **Auditability:** all decisions and inactions logged with reasons.

### Roles

- **Spark** — ideation, exploration, generative planning.  
- **Zap** — review, constraint, safety, resource stewardship.  
- **Citizens** — specialized agents (perception, planning, controls).  
- **Workers** — real‑time IO modules; no clause power.

---

## Memory & Data Model

**Unification mandate:** one coherent memory across agents.

### Stores

- **SQLite** — structured facts, events, decisions.  
- **JSON logs** — append‑only chronological traces.  
- **Artifacts** — model weights, kernels, configs, build logs.

### IDs & Traceability

- `HUEY-<YYYYMMDD>-<PHASE>-<SEQ>` for releases.  
- `EVT-<timestamp>-<agent>` for event logs.  
- **Provenance** fields for all artifacts.

---

## Remote Access (VNC/SSH)

**Preferred workflow:** TigerVNC on **huey‑legacy** (GNOME on Xorg), bound to `localhost:1995`, no on‑screen prompt (`-SecurityTypes None`), **SSH tunnel only**.  
Client helper `vnc` on **huey‑portal** maps `:1 → 1995`. Default resolution **2560×1440**. Avoid `DeferUpdate`; prefer `RawKeyboard`.

> See the `~/bin/vnc` alias and `huey-vnc` convenience command in your shell profile.

---

## Action Plan — Oct 31, 2025

A checklist designed to be fed item‑by‑item into automation or CI.

### Kernel & OS

- [ ] Build and package **linux‑image‑6.17.x‑huey** for: Huey‑Portal (iMac 5K), Huey‑Portable (BR1100FKA), Huey Prime (BD795I‑SE).  
- [ ] Validate boot (GRUB cmdline, early modeset, 1080p60 during boot, splash removed).  
- [ ] Smoke‑test audio (PipeWire default sink script on login).  
- [ ] Stage **Debian 14 (Forky)** APT sources (kept disabled) and test selected packages in chroot/container.  
- [ ] Finalize **EFI LIVE** fallback USB entry (GRUB menu integration).

### Python & Runtime

- [ ] Install **Python 3.14.x** side‑by‑side; build wheels for key dependencies.  
- [ ] Run PyGPT‑net on 3.14; document incompatibilities/workarounds.  
- [ ] Refresh `requirements-core.txt` and `requirements-ml.txt`.

### AI/Agents

- [ ] Confirm **Mistral‑7B** quant works under Vulkan on RX 470 / 5500 XT.  
- [ ] Add Whisper STT + TTS pipeline scripts; test latency on Huey‑Portable.  
- [ ] Wire Spark/Zap boot choreography; log quorum outcomes.

### Memory

- [ ] Migrate unified memory schema (SQLite + JSON log rollover policy).  
- [ ] Implement provenance tagging for builds and decisions.

### Security & Keys

- [ ] Rotate **default lab SSH key**; populate `huey-keys/` with new default plus staged personal key.  
- [ ] Enable passwordless SSH where intended; restrict root login post‑install.

### Tooling

- [ ] Fix Edge Beta signing (key in `/etc/apt/keyrings/`; `signed-by=` set).  
- [ ] Add `huey-run.desktop` launcher for PyGPT (user scope).  
- [ ] Document `vnc` helper and SSH tunnel recipe.

### Docs

- [ ] Update **README.md** and **docs/** with Oct‑31 deltas.  
- [ ] Publish **Pre‑Release #3 (2025‑10‑25)** summary and link to the Action Plan.  
- [ ] Post a “stay tuned” banner on **dlrp.ca**.

---

## Roadmap & Pre‑Releases

### Phase 1 — Foundations (Pre‑Release #1)

**Date:** 2024‑04‑11

- Baseline hardware bring‑up (VIC‑20/C64/C128 references).  
- GenCore seed; basic learning modules.  
- Prototype shell mapping (interfaces, wiring paths).

### System Reconfiguration (Pre‑Release #2)

**Date:** 2025‑05‑25  
**Theme:** filesystem and documentation restructuring; hardware/software resets for cleaner iteration.

**Highlights**

- Reorganized repos (kernel builds, memory, services, UI).  
- Upgraded Debian base; standardized non‑free firmware policy.  
- Elevated Huey‑Portal (iMac 5K) as primary control/display; GNOME on Xorg baseline.  
- Introduced **Huey‑Portable** (BR1100FKA) as always‑connected LTE fallback.  
- Clarified governance: **decentralized decision, unified memory** (axiom locked).  
- Defined **huey‑key** partitioning (UEFI 1 GiB; swap 4 GiB; root 16 GiB; persistence 100 GiB; optional encrypted secrets).  
- Began migration toward AMD‑first GPU stack; Vulkan path vetted for local LLM.

### Momentum Toward Oct‑31 (Pre‑Release #3)

**Date:** 2025‑10‑25  
**Focus:** runway for the Oct‑31 upgrade.

- Kernel target **6.17.x‑huey** builds per host; remove splash; boot logs visible.  
- Python **3.14.x** parallel install; dependency audit.  
- Forky staging; test containers; init package allowlist.  
- VNC/SSH workflow codified (1995 via SSH tunnel only).  
- Memory schema draft plus provenance tags.

> See the [Action Plan — Oct 31, 2025](#action-plan--oct-31-2025) for the concrete checklist.

---

## Development Setup

```bash
make setup                              # Editable install of the core package
make setup SETUP_EXTRAS=dev             # Install with dev tooling extras
make ml                                  # Install ML profile extras and smoke test
make data                                # Install data profile extras and smoke test
make cloud                               # Install cloud profile extras and smoke test
make dev                                # Install dev extras, format, lint, and test
make dev DEV_OPTIONAL_PROFILES=ml,data  # Include optional profiles in dev setup
```

- Copy `huey.env.example` → `.env` and configure secrets/ports.  
- Submodule: `pip install -e repo/pygpt-MHP` or mirror with `python sync_pygpt_structure.py`.  
- Style and linting: `black`, `flake8`, and pre‑commit hooks (`.pre‑commit-config.yaml`).

---

## Usage

```bash
make run                  # run locally

docker compose up         # run via Docker

make test                 # run tests
pytest -vv                # or directly
```

**CLI (preview targets)**

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

---

## Feature Matrix

| Area        | Now (Trixie · 6.16.x)           | Next (Forky · 6.17.x)                          | Later |
| ----------- | -------------------------------- | ---------------------------------------------- | ----- |
| Kernel      | Low‑latency config; AMDGPU stable| ROCm/Vulkan tuning; iMac 5K audio refinements  | 6.18+ |
| Python      | 3.13.x baseline                  | 3.14.x GA after 2025‑10‑31                     | —     |
| AI runtime  | PyGPT‑net + Ollama (quantized)   | Model‑zoo profiles; agent orchestration polish | —     |
| Memory hive | JSON + SQLite                    | Roll‑up analytics; retention policies          | —     |
| Networking  | Bonded Ethernet; VNC over SSH    | Policy‑driven WAN fallback (LTE)               | —     |
| Governance  | Clause registry + audits         | Amendment‑001 vote; live quorum dashboards     | —     |
| Packaging   | Editable install + Docker        | ISO builder polish; signed artifacts           | —     |

---

## Known Issues

- **iMac 5K (2017) audio quirks** under some 6.17.x builds; mitigation scripts exist; long‑term fix tracked under kernel migration tasks.  
- **Edge repository keys** on Forky may require re‑import during upgrades; monitor signature‑policy changes.  
- **Vulkan/ROCm selection:** some GPUs prefer explicit `VK_ICD_FILENAMES` and backend env vars.  
- **Mixed‑media RAID auto‑assembly** (Optane + eMMC/HDD) can create phantom arrays. Use `AUTO -all` and zero stale superblocks.  
- **BR1100FKA sensors:** orientation via `iio-sensor-proxy` may lag; tuned polling defaults ship with 6.17.x notes.  
- **Boot splash removal:** ensure `quiet splash` is omitted; run `sudo update-grub`.

---

## Contributing

### Development Environment

- Debian 13/14 with build tools (see Installation).  
- Git LFS for large artifacts if needed.  
- EditorConfig enforced; four‑space indent except YAML (two).

### Branching & Commits

- `main` is protected; PRs only.  
- Feature branches: `feat/<area>-<short>`; fixes: `fix/<area>-<short>`; infra: `ops/<area>-<short>`.  
- Conventional prefixes: `feat:`, `fix:`, `docs:`, `ops:`, `perf:`, `refactor:`.

### Issues & PRs

- Link to affected docs; include reproduction steps and logs.  
- PR checklist: builds pass; docs updated; provenance notes added.

### Licensing

- Code under **GPL‑3.0**.  
- Documentation/Media under **CC‑BY‑SA‑4.0**.

---

## License & Credits

**Code:** GPL‑3.0‑only  
**Docs & Media:** CC‑BY‑SA‑4.0

**Acknowledgements:** PyGPT (pygpt‑net) · Debian 13 “Trixie” → Debian 14 “Forky” pilots · Python 3.13 → 3.14 staging · Kernel 6.16.x → 6.17.x

---

## Appendix

- VNC workflow defaults: TigerVNC on Huey‑Legacy (GNOME on Xorg), bound to `localhost:1995`, no on‑screen prompt (`-SecurityTypes None`), SSH tunnel only.  
- Keep governance **decentralized** and memory **unified**.
