# 🧠 Monkey Head Project

### An Adaptive AI/OS Framework for Ethical Robotics and Intelligent Systems

---

## 🚀 Project Overview

The **Monkey Head Project** is dedicated to developing a robust, modular, and ethically governed robotic ecosystem driven by advanced artificial intelligence. At the core is **GenCore**, an adaptive AI Operating System (AIOS), designed to intelligently coordinate actions across diverse hardware platforms and legacy systems.

**Vision:**
Creating a universally accessible platform that democratizes cutting-edge robotics and AI, enhancing human-machine collaboration and ethical technological innovation.

For a quick summary, see [New-To-AI.md](docs/New-To-AI.md).

---

## 🛠️ Core Components

### 1. GenCore AI Operating System

A hierarchical adaptive OS divided into specialized layers:

* **HostOS:** Strategic oversight, system-wide governance, and high-level decision-making, inspired by conductor models and centralized strategic systems.
* **SubOS:** Operational resource allocation, task management, and dynamic adaptability, inspired by biological resilience and technological redundancy.
* **NanoOS:** Real-time precision control at the hardware interaction level, optimizing immediate responsiveness and reliability.
* **HostOS Environment:** Runs on either **Windows 10**, **Windows 11**, or **macOS Ventura** (or newer), providing a familiar desktop operating system for overall system control.
* **SubOS Environment:** A **Debian Trixie** installation with **Python 3.12** preloaded, handling mid-level coordination and task scheduling.
* **NanoOS Environment:** A lightweight **Python 3.12** runtime used for granular execution of hardware-level tasks.

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
* **PyGPT-net Integration:** Advanced AI-driven interactions enabling intuitive communication, analysis, and adaptive learning.
* **Broad Compatibility:** Seamlessly integrates with Windows, Linux, macOS, and legacy computing environments.
* **Eco-Smart Design:** Prioritizes energy efficiency, modular upgrades, and sustainable technology solutions.
* **Nature-Inspired Engineering:** Leverages lessons from biological systems (carpenter ants, fungal networks, honeycombs) for optimized structural design and resilience.
* **Philosophical Grounding:** Guided by ethical considerations inspired by literature (Ozymandias), philosophical scenarios (McCoy’s transporter dilemma), and reflective practices.

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

### Software Requirements

Ensure the following tools are installed before running the project:

- **Python 3.12+** and `pip`
- **Git**
- **Docker** and **Docker Compose**
- **Kubernetes** (`kubectl` CLI)

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

Once copied, prefer importing modules from the project root instead of the `repo/pygpt-MHP` path. The installer performs the submodule update and installation with `pip install -e repo/pygpt-MHP` automatically.

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

This launches a Tkinter window where you can install, update, or run the
application. The correct setup script is chosen automatically. A "Run" button
lets you start the program without opening a terminal. If the GUI cannot be
displayed (for example on a headless server), the launcher automatically falls
back to the command-line interface. You can also force CLI mode with
`python run.py --cli`.

The GUI now checks whether you've accepted the license on startup and
offers a **Tools** menu. From there you can reopen the license dialog or
view a summary of bundled prompts and memory files.

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
`run-tests.sh` script performs the same activation step before executing
the test suite with `pytest -vv`. Both scripts report an error if the
`venv` directory is missing, reminding you to run `install.sh` first.
`update_memory_pdfs.py` regenerates text versions of the bundled PDF files
under `memory/PDF`. Run this script whenever you add or edit PDF documents
to keep the preloaded dataset up to date.

The `huey` package also provides a small CLI. Use `huey convert` to
convert image files between formats at maximum quality. Supply an input
file or directory with `--format` specifying the target type (e.g.
`JPEG`, `PNG`). Converted files are saved alongside the originals or in a
specified output directory.

### Docker and Kubernetes Utilities

The `scripts/` directory contains helper scripts for container management:

```bash
./scripts/docker_setup.sh    # build image and start compose stack
./scripts/docker_cleanup.sh  # stop containers and prune resources
./scripts/k8s_setup.sh       # apply manifests in k8s/
./scripts/k8s_cleanup.sh     # remove Kubernetes resources
```

Programmatic helpers for Kubernetes lives in
`monkey_head.services.container_management`. Functions like
`scale_deployment`, `get_pod_logs`, and `cleanup_kubernetes` provide a
Python interface for scaling deployments, retrieving pod logs, and cleaning up
resources.

Additional helpers now include `build_docker_image`, `stop_containers`,
`cleanup_images`, and `manage_networks` for end-to-end Docker lifecycle
management.

### Linux (Debian 13) Installation

Run the cross-platform installer with root privileges:

```bash
sudo python installer.py
```

During installation you'll be asked whether to use **auto** or **manual**
hardware selection. Choosing **manual** lets you pick from common devices such

as SuperMicro X9 QRI-F+, MacBook Pro 2019, iMac 5K 2017, Raspberry Pi models,
and more. Selecting **auto** performs a general installation.

Next you'll choose the software profile. Selecting **auto** installs all default
packages, while **manual** lets you pick specific packages and programs to
install.

This invokes `setup/Debian13/install.sh`, which updates `/etc/apt/sources.list` to Debian **Trixie**, installs Git, Node.js, Python 3, and Docker, then creates a virtual environment and preloads bundled data. Accept the license agreement when prompted. The project files are copied to `/opt/monkey_head`.


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

When installation finishes, change to the install directory and launch the GUI:

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
The license dialog will appear during this installation step as well.

This launches `setup/Windows11/01-FULL.bat`, which installs Chocolatey, Git,
Docker Desktop, and other required tools on Windows. On macOS the installer
invokes `setup/macOS/install.sh` to configure Homebrew and the Python
environment. The batch script supports both Windows 10 and Windows 11.
By default the repository is cloned to `%ProgramFiles%\Monkey-Head-Project`.

### Uninstallation and Cleanup

Run the cross-platform uninstaller to remove the project and optional packages:

```bash
sudo python uninstaller.py  # Linux/macOS
python uninstaller.py       # Windows
```
The script calls OS-specific cleanup scripts to delete the virtual environment, uninstall packages, and prune Docker resources.


### Directory Structure

Legacy scripts from the `py/` folder were consolidated and updated in
the `monkey_head/` directory. All utilities and modules live under `monkey_head/` to
keep the project organized.

### Development Setup

For day-to-day development it is recommended to work in a Python virtual environment.
Create one with `python -m venv venv` and install dependencies using
`pip install -r requirements.txt`. Docker users can spin up
`docker-compose up` for an isolated environment that mirrors production.
When adding new modules, format the code with `black` and run
`flake8` and `pytest` before opening a pull request.

### Recent Updates

- Preset placeholders now show the preset name instead of the file ID for better readability.
- Added `--version` flag to `run.py` for quick version checks.
- Implemented centralized logging and video screenshot capabilities for multimodal workflows.

### Utilities

Use `monkey_head/utils/list_by_mtime.py` to list files in any directory from oldest
to newest:

```bash
python monkey_head/utils/list_by_mtime.py path/to/dir
```

---

## 🔬 Test Hardware

* **Development:** MacBook Pro 2019, Lenovo Legion Go.
* **Legacy Support:** MacBook Pro 2012, Commodore 64/128, VIC-20.
* **Edge Computing:** Raspberry Pi 3 B+.
* **Multimedia & Gaming:** PlayStation 2 & 3.

---

## 🌱 Future Directions

* Expansion into environmental monitoring and interdisciplinary scientific collaborations.
* Advanced autonomous energy solutions and sustainable system management.
* Continued ethical governance refinements, ensuring transparency and accountability.

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

## 🛠️ Troubleshooting

If the application fails to start, try the following steps:

1. Remove any old virtual environments and reinstall dependencies.
2. Run `python -m pip install --upgrade pip` to update Python tooling.
3. Verify that your `docker-compose` version meets the requirements.
4. Check the logs in the `logs/` directory for detailed error messages.

For persistent issues, open a bug report with your system details and
the steps needed to reproduce the error.

## 🌟 Related Projects and Inspirations

The Monkey Head Project is built on top of numerous open-source efforts,
from the ROS robotics framework to cutting-edge language models. We
collaborate closely with the community to integrate the best tools
available and appreciate everyone who helps advance ethical AI research.
