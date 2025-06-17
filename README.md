# 🧠 Monkey Head Project

### An Adaptive AI/OS Framework for Ethical Robotics and Intelligent Systems

---

## 🚀 Project Overview

The **Monkey Head Project** is dedicated to developing a robust, modular, and ethically governed robotic ecosystem driven by advanced artificial intelligence. At the core is **GenCore**, an adaptive AI Operating System (AIOS), designed to intelligently coordinate actions across diverse hardware platforms and legacy systems.

**Vision:**
Creating a universally accessible platform that democratizes cutting-edge robotics and AI, enhancing human-machine collaboration and ethical technological innovation.

For a quick summary, see [New-To-AI.md](docs/New-To-AI.md).
Full project documentation lives in [docs/README.md](docs/README.md).

## 📑 Table of Contents

- [Advanced Configuration](#-advanced-configuration)
- [Acknowledgements](#-acknowledgements)
- [Additional Resources](#-additional-resources)
- [Community and Support](#-community-and-support)
- [Contributing](#-contributing)
- [Core Components](#-core-components)
- [Development Setup](#development-setup)
- [Directory Structure](#directory-structure)
- [Docker and Kubernetes Utilities](#docker-and-kubernetes-utilities)
- [FAQ](#-frequently-asked-questions-faq)
- [Final Thoughts](#-final-thoughts)
- [Future Directions](#-future-directions)
- [GUI Interface (Default)](#gui-interface-default)
- [Installation and Usage](#-installation-and-usage)
- [Key Features](#-key-features)
- [License](#-license)
- [Linux (Debian 13) Installation](#linux-debian-13-installation)
- [macOS Installation](#macos-installation)
- [Modular Architecture](#-modular-architecture)
- [Project History and Phases](#-project-history-and-phases)
- [Project Flow and Interconnectivity](#-project-flow-and-interconnectivity)
- [Project Overview](#-project-overview)
- [Recent Updates](#-recent-updates)
- [Related Projects and Inspirations](#-related-projects-and-inspirations)
- [Running Tests](#running-tests)
- [Software Requirements](#software-requirements)
- [Submodule](#submodule)
- [Test Hardware](#-test-hardware)
- [Troubleshooting](#-troubleshooting)
- [Uninstallation and Cleanup](#uninstallation-and-cleanup)
- [Utilities](#utilities)
- [Windows 10 & 11 Installation](#windows-10--11-installation)
- [Heartfelt Thank You](#-heartfelt-thank-you)

---

## 🛠️ Core Components

### 1. GenCore AI Operating System

A hierarchical adaptive OS divided into specialized layers:

* **HostOS:** Strategic oversight, system-wide governance, and high-level decision-making, inspired by conductor models and centralized strategic systems.
* **SubOS:** Operational resource allocation, task management, and dynamic adaptability, inspired by biological resilience and technological redundancy.
* **NanoOS:** Real-time precision control at the hardware interaction level, optimizing immediate responsiveness and reliability.
* **HostOS Environment:** Runs on either **Windows 10**, **Windows 11**, or **macOS Ventura** (or newer), providing a familiar desktop operating system for overall system control.
* **SubOS Environment:** A **Debian Trixie** (or **Testing**) installation with **Python 3.12** preloaded, handling mid-level coordination and task scheduling.
* **NanoOS Environment:** A lightweight **Python 3.12** runtime used for granular execution of hardware-level tasks.
* **Desktop Environment:** Both GenCore and SubOS use the lightweight **MATE** desktop, providing a consistent interface across layers.

#### GenCore Logic
GenCore is a custom Debian **Trixie** distribution engineered to run bare metal on Huey. It boots directly on the robot's hardware and orchestrates containerised SubOS and NanoOS layers without an intermediary OS. Real-time patches and robotics drivers keep latency low, enabling deterministic control over sensors and actuators while maintaining the flexibility of modular containers.
### 2. Huey Robotic Shell

The physical embodiment of GenCore:

* **Advanced Hardware Integration:** Incorporates Supermicro X9QRI-F+ motherboard, high-speed ECC RAM, Intel CPUs, NVMe SSD storage, and optimized liquid cooling systems inspired by natural systems.
* **Energy Autonomy:** Autonomous power and cooling management ensuring operational self-sufficiency.
* **Safety and Redundancy:** Integrated aviation-grade redundancy and submarine-inspired emergency response systems.

### 3. Cloud Pyramid Ethical Governance

A multi-tiered ethical governance system ensuring responsible AI use:

* **Grassroots Layer:** Network of 128 AI feedback nodes, promoting community-driven oversight.
* **Tri-Branch Consensus:** Balanced decisions from Executive, Senate, and Parliamentary bodies.
* **Pinnacle & Supreme Court AI:** Ensures ethical compliance and intervenes to prevent misuse or harm.

---

## 🌐 Key Features

* **Adaptive User Interfaces:** Supports multiple input methods including voice, gesture, and AR/VR.
* **Broad Compatibility:** Seamlessly integrates with Windows, Linux, macOS, and legacy computing environments.
* **Eco-Smart Design:** Prioritizes energy efficiency, modular upgrades, and sustainable technology solutions.
* **Nature-Inspired Engineering:** Leverages lessons from biological systems (carpenter ants, fungal networks, honeycombs) for optimized structural design and resilience.
* **Philosophical Grounding:** Guided by ethical considerations inspired by literature (Ozymandias), philosophical scenarios (McCoy’s transporter dilemma), and reflective practices.
* **PyGPT-net Integration:** Advanced AI-driven interactions enabling intuitive communication, analysis, and adaptive learning.

---

## 🧩 Modular Architecture

GenCore follows a layered design that separates strategic planning, operational control, and real-time hardware interaction. HostOS acts as the "brain," overseeing resource governance and system-wide decisions. SubOS instances manage specialized tasks, scaling resources on demand. NanoOS containers handle direct hardware interaction and time-critical operations. By keeping these tiers loosely coupled, contributors can extend or replace individual layers without disrupting the entire system.

Huey exposes clear integration points for sensors, actuators, and experimental modules. Custom hardware can be added by mapping device drivers to the appropriate NanoOS, while HostOS provides unified monitoring and logging. This modular approach encourages experimentation and simplifies long-term maintenance.

---

## 📚 Project History and Phases

| Phase | Title                         | Date         | Highlights                                                                |
| ----- | ----------------------------- | ------------ | ------------------------------------------------------------------------- |
| 1     | Pre-Release                   | Apr 11, 2024 | Initial AI/OS framework, legacy hardware integration.                     |
| 2     | Infrastructure & Adaptability | Jun 21, 2024 | Enhanced infrastructure, adaptive AI agents, power management.            |
| 3     | System Awakening              | Oct 31, 2024 | Full system awakening, comprehensive hardware tests, emergency protocols. |

---

## 🔗 Project Flow and Interconnectivity

Each development phase expands how modules communicate across hardware and software layers. GenCore orchestrates HostOS, SubOS, and NanoOS components while Huey's sensor network links legacy systems with modern nodes. Docker and Kubernetes deployments synchronize these pieces, allowing distributed operation on varied platforms. The Cloud Pyramid governance layer oversees this mesh to ensure ethical, cohesive growth.

### Software Requirements

Ensure the following tools are installed before running the project:

- **Docker** and **Docker Compose**
- **Git**
- **Kubernetes** (`kubectl` CLI)
- **Python 3.12+** and `pip`
- **Build tools** (`build-essential` on Debian, Xcode Command Line Tools on macOS)
- **VLC media player** (with `python-vlc` bindings)

## 🖥️ Installation and Usage

### Quick Start (Docker)

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project
docker-compose up -d
```

### Manual Installation

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
python -m pip install --upgrade pip
pip install -r requirements.txt
git submodule update --init --recursive
pip install -e repo/pygpt-MHP
python monkey_head/main.py
```

### Submodule

This project uses the [pygpt-MHP](https://github.com/DylanLRPollock/pygpt-MHP) submodule located in `repo/pygpt-MHP`. Clone with `--recurse-submodules` or run `git submodule update --init --recursive` to fetch it. After cloning, run the helper script below to mirror the submodule into the main repository so you can work entirely from the local `src` directory:

```bash
python sync_pygpt_structure.py  # copy entire pygpt tree
# python sync_pygpt_structure.py --depth 2  # limit recursion if desired
```

Run `python scripts/check_inter_program_connectivity.py` to verify that
the submodule and local packages import correctly.

Once copied, prefer importing modules from the project root instead of the `repo/pygpt-MHP` path. The installer performs the submodule update and installation with `pip install -e repo/pygpt-MHP` automatically.

The `run.py` launcher now detects when the mirrored `src` directory or installed
package is missing and will automatically use `repo/pygpt-MHP/src` instead. This
lets you try the project right after cloning, even before syncing or installing
the submodule.

### Git Utilities

Several helper functions in `monkey_head.services.environment_setup` make it
easier to keep your local clone up to date. You can programmatically switch
branches, pull the latest changes, and push commits:

```python
from monkey_head.services.environment_setup import (
    checkout_branch, pull_latest, commit_and_push
)

checkout_branch("develop")      # git fetch && git checkout develop
pull_latest()                    # git pull --ff-only
commit_and_push("update", branch="develop")
```

These utilities rely on `git` being available on your system and are useful for
automating common version control tasks in scripts.

### Running Tests

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests
```

You can also use the provided cross-platform installer, which automatically
initializes git submodules, installs the `pygpt-MHP` package, and detects your
operating system to invoke the appropriate setup script:

```bash
python installer.py
```
The installer now displays the license agreement using a small Tkinter
dialog. You must accept these terms before the setup can finish.

### GUI Interface (Default)

The GUI is now the primary way to install and control the project. Simply run:

```bash
python run.py
```

This opens the PyGPT-based Qt interface with integrated Monkey Head tools for
installation, updates, running the application, and managing Docker or
Kubernetes resources. If the GUI cannot be displayed (for example on a
headless server), the launcher automatically falls
back to the command-line interface. You can also force CLI mode with
`python run.py --cli`. For an even lighter headless run you can launch the
minimal echo chatbot with `python run.py --minimal`. A basic Tkinter chat demo
is still available via `python run.py --simple-chat`. To run individual modules
directly, use `python run.py --module package.module[:func]`.
You can also perform a quick environment check with
`python run.py --system-check`.
For the installer-style program manager launch `python run.py --manager-ui`.
To use a different working directory pass `--workdir /path/to/dir`.
Specify an alternative logging configuration with
`--config path/to/CONFIG.txt`.

The GUI now checks whether you've accepted the license on startup and
offers a **Tools** menu. From there you can reopen the license dialog or
view a summary of bundled prompts and memory files. Additional **Docker** and
**Kubernetes** menus provide one-click access to common container tasks such as
building images, starting or stopping containers, cleaning up resources, and
deploying or scaling Kubernetes manifests.

### Adjusting Font Size and Family

The interface adapts to high-DPI displays via the `apply_scaling` utility. When
running in `custom` mode, you can fine-tune scaling with environment variables:

- `SCREEN_FACTOR` – scaling factor for all UI elements.
- `SCREEN_FONT_SIZE` – base font size used across widgets.
- `SCREEN_FONT_FAMILY` – font family applied to Tkinter fonts (default: `Lato`).

Set these variables before launching `run.py` to tailor the GUI to your
display. The `main_ui` dialog also prompts for these values when selecting the
"custom" option at startup.

### Customizing prompts and personalities

Prompt templates live in `prompts/pygpt_prompts.csv`. You can add new
rows to extend the list of actions the AI can assume. Each row contains
the name of the prompt, the instruction text, and a flag used by the
project. After updating the CSV file, copy the additions into
`monkey_head/pygpt_net/data/prompts.csv` so they are included at runtime.

Predefined character presets are stored under
`monkey_head/pygpt_net/data/config/presets`. These JSON files define the
AI and user names along with a short starter prompt. Adding your own
file here makes the new personality available in the interface.

### CLI Helper Scripts

Two convenience wrappers simplify common tasks on Unix systems. `run.sh`
activates the project's virtual environment and launches `run.py`. The
`run-tests.sh` script now also captures coverage and logs results. It
activates the environment, runs `pytest -vv --cov=monkey_head`, and
saves the output to `memory/LOGS/test_results.log`. Both scripts report an
error if the `venv` directory is missing, reminding you to run
`install.sh` first.
`update_memory_pdfs.py` regenerates text versions of the bundled PDF files
under `memory/PDF`. Run this script whenever you add or edit PDF documents
to keep the preloaded dataset up to date. Many helpers that work with these
files now respect the `MEMORY_DIR` environment variable so you can store
your PDF collection elsewhere without modifying the code.
`storage_management.py` helps keep the `memory/` directory organized by
automatically creating the standard subfolders, sorting stray files by
extension and removing empty directories. It can also report the total size
of any subfolder and prune files older than a specified number of days.
`set_api_keys.py` walks you through entering API credentials. Choose
which services to connect (OpenAI, Google, or DeepSeek) or select the
auto option to configure all of them at once.
`vic2_demo.py` launches a small Pygame window demonstrating VIC‑II
graphics on Raspberry Pi 3 and 4 systems.

The `huey` package also provides a small CLI. Use `huey convert` to
convert image files between formats at maximum quality. Supply an input
file or directory with `--format` specifying the target type (e.g.
`JPEG`, `PNG`). Converted files are saved alongside the originals or in a
specified output directory.

### File Integrity Checks

Use `monkey_head.utils.integrity` to verify that important files have not been
modified. Create a JSON manifest mapping each path to its SHA-256 digest and run

```bash
python -m monkey_head.utils.integrity manifest.json
```

The command prints any files that fail verification or `All files verified` if
every digest matches.

### Docker and Kubernetes Utilities

The `scripts/` directory contains helper scripts for container management:

```bash
./scripts/docker_setup.sh    # build image and start compose stack
./scripts/docker_cleanup.sh  # stop containers and prune resources
./scripts/docker_dev_setup.sh # build image and start dev compose stack
./scripts/k8s_setup.sh       # apply manifests in k8s/
./scripts/k8s_cleanup.sh     # remove Kubernetes resources
```
You can also manage containers directly through `run.py`:

```bash
python run.py --docker-compose  # start the Docker Compose stack
python run.py --kubernetes      # deploy the Kubernetes manifests
```

Programmatic helpers for Kubernetes lives in
`monkey_head.services.container_management`. Functions like
`scale_deployment`, `get_pod_logs`, and `cleanup_kubernetes` provide a
Python interface for scaling deployments, retrieving pod logs, and cleaning up
resources.

Kubernetes manifests are stored in the `k8s/` directory. Both the helper
scripts and the GUI use `k8s/deployment.yaml` by default, so update that file
to configure your cluster.

Additional helpers now include `build_docker_image`, `stop_containers`,
`cleanup_images`, `manage_networks`, `list_containers`, and `get_container_logs`
for end-to-end Docker lifecycle management and diagnostics.

Home automation is now supported through `monkey_head.services.home_assistant`.
These helpers allow the project to call Home Assistant services and query entity
state via its REST API.

### Linux (Debian 13) Installation

Run the cross-platform installer with root privileges:

```bash
sudo python installer.py
```

During installation you'll be asked whether to use **auto** or **manual**
hardware selection. Choosing **manual** lets you pick from common devices such

as SuperMicro X9 QRI-F+, MacBook Pro 2019, iMac 5K 2017, Raspberry Pi models,
and more. Selecting **auto** performs a general installation.

You can also skip the prompts entirely by providing your selections on the
command line:

```bash
sudo python installer.py --hardware "Raspberry Pi 4" --software git docker.io
```

Passing `--software auto` installs all default packages without interaction.

Next you'll choose the software profile. Selecting **auto** installs all default
packages, while **manual** lets you pick specific packages and programs to
install.

This invokes `setup/Debian13/install.sh`, which updates `/etc/apt/sources.list` to the chosen release (either **Trixie** or **Testing**), installs Git, Node.js, Python 3, and Docker, then creates a virtual environment and preloads bundled data. Accept the license agreement when prompted. The project files are copied to `/opt/monkey_head`.


### macOS Installation

Run the cross-platform installer with administrator rights:

```bash
sudo python installer.py
```

After selecting your hardware and any optional software packages, the script calls `setup/macOS/install.sh` which:

1. Installs Homebrew if it is missing.
2. Copies the repository into `/Applications/MonkeyHeadProject`.
3. Uses Homebrew to install Git, Python 3, and Docker.
4. Initializes git submodules.
5. Creates a Python virtual environment at `/Applications/MonkeyHeadProject/venv` and installs dependencies, including `pygpt-MHP`.
6. Displays the license agreement via a small Tkinter window.
7. Preloads bundled data for faster first run.

When installation finishes, change to the install directory and launch the
PyGPT interface:

```bash
python run.py
```

All files remain inside `/Applications/MonkeyHeadProject`.


### Windows 10 & 11 Installation

Ensure that **Python 3** is available on your system (download from
[python.org](https://www.python.org/) if needed). Open **Command Prompt** or
**PowerShell** as **Administrator** and run the installer from the project
root. You can use the provided Python script or the convenience batch file:

```bash
python installer.py      # cross-platform installer
install.bat              # Windows helper that runs the same script
```
The same `--hardware` and `--software` options can be supplied here to avoid the
interactive menus.
The license dialog will appear during this installation step as well.

This launches `setup/Windows11/01-FULL.bat`, which installs Chocolatey, Git,
Docker Desktop, and other required tools on Windows. On macOS the installer
invokes `setup/macOS/install.sh` to configure Homebrew and the Python
environment. The batch script supports both Windows 10 and Windows 11.
By default the repository is cloned to `%ProgramFiles%\Monkey-Head-Project`.
For a lean Windows setup you can run `setup/Windows10/windows-remove-tool.bat` after installation. This optional script removes pre-installed apps, disables telemetry, and tunes settings for maximum speed.

### Headless Installation

If no graphical environment is available you can run the license prompt
from the command line using `license_cli.py`:

```bash
python monkey_head/license_cli.py
```

The script prints the license text and will keep asking for confirmation
until you answer `yes` or `no`. Any errors are written to `memory/LOGS/app.log` and
declining raises a `RuntimeError` without modifying the configuration
file.

### Uninstallation and Cleanup

Run the cross-platform uninstaller to remove the project and optional packages:

```bash
sudo python uninstaller.py  # Linux/macOS
python uninstaller.py       # Windows
```
The script calls OS-specific cleanup scripts to delete the virtual environment, uninstall packages, and prune Docker resources.

### Fresh Installation

To completely reset the environment and reinstall everything, run the fresh installer. It first executes the uninstaller and then launches the regular installer:

```bash
sudo python fresh_install.py  # Linux/macOS
python fresh_install.py       # Windows
```


### Repair

If the installation becomes corrupted, run the repair script. It clones a fresh
copy of the repository and installs it:

```bash
sudo python repair.py  # Linux/macOS
python repair.py       # Windows
```



### Directory Structure

Legacy scripts from the `py/` folder were consolidated and updated in
the `monkey_head/` directory. All utilities and modules live under `monkey_head/` to
keep the project organized.

The `memory/` directory now serves as the main storage location for
internal files, documentation assets, and logs. Subfolders like
`memory/LOGS`, `memory/DOCS`, and `memory/UPLOADS` keep content
organized by format.

### Development Setup

For day-to-day development it is recommended to work in a Python virtual environment.
Create one with `python -m venv venv` and install dependencies using
`pip install -r requirements.txt`. Docker users can spin up
`docker-compose up` for an isolated environment that mirrors production.
For a more complete stack with PostgreSQL and extra development tooling,
use `./scripts/docker_dev_setup.sh` (or run `docker compose -f compose-dev.yaml up -d`).
When adding new modules, format the code with `black` and run
`flake8` and `pytest` before opening a pull request.

### Recent Updates

- Added `--version` flag to `run.py` for quick version checks.
- Implemented centralized logging and video screenshot capabilities for multimodal workflows.
- Preset placeholders now show the preset name instead of the file ID for better readability.

### Utilities

Use `monkey_head/utils/list_by_mtime.py` to list files in any directory from oldest
to newest:

```bash
python monkey_head/utils/list_by_mtime.py path/to/dir
```

### Function Registry

Decorate any standalone function with `register_function` to have it
automatically added to a global registry. Call `list_functions()` to see
all registered names:

```python
from monkey_head.function_registry import register_function, list_functions

@register_function
def hello(name: str) -> str:
    return f"Hello {name}"

print(list_functions())  # ["hello", ...]
```

---

## 🔬 Test Hardware

* **Development:** MacBook Pro 2019, Lenovo Legion Go.
* **Edge Computing:** Raspberry Pi 3 B+.
* **Legacy Support:** MacBook Pro 2012, Commodore 64/128, VIC-20.
* **Multimedia & Gaming:** PlayStation 2 & 3.

---

## 🌱 Future Directions

* Advanced autonomous energy solutions and sustainable system management.
* Continued ethical governance refinements, ensuring transparency and accountability.
* Expansion into environmental monitoring and interdisciplinary scientific collaborations.

---

## 🤝 Contributing

Your contributions are crucial! You can help by reporting bugs, suggesting features, submitting pull requests, or participating in discussions.

* Follow standard Python practices. Formatting and style are checked with `black` and `flake8` in CI.
* Provide clear commit messages and detailed PR descriptions.

Visit the [GitHub Repository](https://github.com/DylanLRPollock/Monkey-Head-Project) to contribute or learn more.

---

## 🔗 Additional Resources

The `docs/` directory contains extended documentation on the project’s architecture, historical phases, and governance design. New contributors should start with [docs/README.md](docs/README.md) and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.
For an introductory overview, see [docs/New-To-AI.md](docs/New-To-AI.md).
For tips on removing unnecessary software and disabling services, see [docs/os-debloating.md](docs/os-debloating.md).

---

## 📖 License

This project is open-source under the **GNU General Public License v3.0 (GPL-3.0)**, allowing free use, modification, and redistribution under its terms.

---

## 🙏 Acknowledgements

Special thanks to the global open-source community, the creators of foundational technologies, and everyone supporting the Monkey Head Project.

---

## 🚀 Final Thoughts

The Monkey Head Project is more than technology; it's a vision for responsible and adaptive collaboration between humans and AI. Join us as we explore the exciting possibilities where ethical AI innovation meets practical, real-world applications.

**Welcome to the future with the Monkey Head Project! 🧠🚀**

---

## ⚙️ Advanced Configuration

GenCore offers extensive customization through the `config.yaml` file at the
project root and the JSON profiles found under `config/pygpt_net/`. You can
add your own YAML files in `config/` to override default behaviors, define
hardware profiles, or enable experimental modules. After editing a
configuration file, restart the system with `python run.py` (or
`python run.py --cli` for command-line mode) or `docker-compose restart` to
apply the changes.

### Sample Configuration Snippet

The example below illustrates how you might extend `config.yaml` or create a
`config/custom.yaml` file to describe extra hardware. Use it as a guideline and
adapt the keys to match your system:

```yaml
# config/custom.yaml (example)
hardware:
  sensors:
    - name: depth_cam
      type: realsense
  actuators:
    - name: arm_joint
      type: servo
ai:
  planning:
    strategy: hierarchical
```

## 💬 Community and Support

Join the conversation on our
[Discussion Board](https://github.com/DylanLRPollock/Monkey-Head-Project/discussions)
or drop into the Matrix chat at `#monkey-head:matrix.org`. Start by searching
the issue tracker if you encounter problems. If your question isn't answered,
open a new topic or reach out on social media.

## ❓ Frequently Asked Questions (FAQ)

**Q: Do I need previous robotics experience?**  
A: No. Beginners can explore the software in simulation or on entry-level
hardware using the provided tutorials.

**Q: Is the project suitable for educational use?**  
A: Absolutely. The modular design is perfect for classroom demonstrations and
research labs.

**Q: Can I integrate GenCore into my own product?**
A: Yes. The software is released under the GPL-3.0 license, which allows
commercial and non-commercial use as long as the license terms are respected.

**Q: Where can I find more documentation?**
A: Extensive guides live in the `docs/` directory and in [docs/README.md](docs/README.md).

**Q: How do I contribute or ask questions?**
A: Join the GitHub discussions or open an issue to share feedback and contributions.

## 🛠️ Troubleshooting

If the application fails to start, try the following steps:

1. Remove any old virtual environments and reinstall dependencies.
2. Run `python -m pip install --upgrade pip` to update Python tooling.
3. Verify that your `docker-compose` version meets the requirements.
4. Check the logs in `memory/LOGS` for detailed error messages.

For persistent issues, open a bug report with your system details and
the steps needed to reproduce the error.

## 🌟 Related Projects and Inspirations

The Monkey Head Project is built on top of numerous open-source efforts,
from the ROS robotics framework to cutting-edge language models. We
collaborate closely with the community to integrate the best tools
available and appreciate everyone who helps advance ethical AI research.

## ❤️ Heartfelt Thank You

Thank you for taking the time to explore the Monkey Head Project. Your curiosity and support mean the world to us, and we hope this project inspires you to build amazing things.
