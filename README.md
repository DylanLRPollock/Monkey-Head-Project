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
python src/main.py
```

### Submodule

This project uses the [pygpt-MHP](https://github.com/DylanLRPollock/pygpt-MHP) submodule located in `repo/pygpt-MHP`. It provides advanced GPT-based capabilities leveraged by GenCore. Clone the repository with `--recurse-submodules` or run `git submodule update --init --recursive` after cloning to ensure it is available.

### Running Tests

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests
```

You can also use the provided cross-platform installer, which automatically
detects your operating system and invokes the appropriate setup script:

```bash
python installer.py
```

### macOS Installation

Running the installer on macOS executes `setup/macOS/install.sh`. This script
ensures Homebrew is available, installs Git, Python 3, Docker, and sets up the
project's Python virtual environment automatically.

### Windows 10 & 11 Installation

Ensure that **Python 3** is available on your system (download from
[python.org](https://www.python.org/) if needed). Open **Command Prompt** or
**PowerShell** as **Administrator** and run the installer from the project
root:

```bash
python installer.py
```

This launches `setup/Windows11/01-FULL.bat`, which installs Chocolatey, Git,
Docker Desktop, and other required tools on Windows. On macOS the installer
invokes `setup/macOS/install.sh` to configure Homebrew and the Python
environment. The batch script supports both Windows 10 and Windows 11.

### Directory Structure

Legacy scripts from the `py/` folder were consolidated and updated in
the `src/` directory. All utilities and modules live under `src/` to
keep the project organized.

### Development Setup

For day-to-day development it is recommended to work in a Python virtual environment.
Create one with `python -m venv venv` and install dependencies using
`pip install -r requirements.txt`. Docker users can spin up
`docker-compose up` for an isolated environment that mirrors production.
When adding new modules, format the code with `black` and run
`flake8` and `pytest` before opening a pull request.

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

This project is open-source under the **MIT License**, allowing free use, modification, and redistribution.

---

## 🙏 Acknowledgements

Special thanks to the global open-source community, the creators of foundational technologies, and everyone supporting the Monkey Head Project.

---

## 🚀 Final Thoughts

The Monkey Head Project is more than technology; it's a vision for responsible and adaptive collaboration between humans and AI. Join us as we explore the exciting possibilities where ethical AI innovation meets practical, real-world applications.

**Welcome to the future with the Monkey Head Project! 🧠🚀**
