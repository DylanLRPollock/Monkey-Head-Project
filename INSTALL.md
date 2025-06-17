# Installation Guide

This document explains how to install the Monkey Head Project on Linux, macOS, and Windows. The project provides cross-platform scripts and a GUI-based installer for convenience.

## Quick Start with Docker

If you have Docker installed, you can clone the repository and start the containers immediately:

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project
docker-compose up -d
```

This spins up the default services defined in `docker-compose.yml`.

## Manual Installation

To set up the project without Docker:

```bash
git clone --recurse-submodules https://github.com/DylanLRPollock/Monkey-Head-Project.git
cd Monkey-Head-Project
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
git submodule update --init --recursive
pip install -e repo/pygpt-MHP
python monkey_head/main.py
```

## Using the Cross‑Platform Installer

The `installer.py` script offers a guided setup that detects your operating system and runs the appropriate installation script. Run it with administrator privileges on Linux and macOS:

```bash
sudo python installer.py  # Linux/macOS
python installer.py       # Windows
```

During installation you can choose automatic or manual hardware and software selection. The script initializes git submodules, installs dependencies, shows the license agreement, and preloads bundled data.

### Graphical Interface

Running `python run.py` launches a Tkinter GUI for installing, updating, and running the application. Use `python run.py --cli` if no graphical environment is available.

## Operating‑System Scripts

Under the `setup/` directory you will find OS-specific scripts used by the installer:

- `setup/Debian13/install.sh`
- `setup/macOS/install.sh`
- `setup/Windows11/01-FULL.bat`

These scripts install required packages (Git, Python, Docker, etc.), create a virtual environment, and copy the project files to the system location (e.g. `/opt/monkey_head` on Linux).

## Headless Installation

On servers without a GUI, run the license prompt from the command line:

```bash
python monkey_head/license_cli.py
```

## Running Tests

Activate the virtual environment and execute:

```bash
./run-tests.sh
```
Results are stored in `memory/LOGS/test_results.log`.

## Next Steps

With the environment ready, you can start the application using the launch
scripts described in [run.md](run.md).

## Uninstallation and Fresh Install

To remove the project, use the cross-platform uninstaller:

```bash
sudo python uninstaller.py  # Linux/macOS
python uninstaller.py       # Windows
```

The `fresh_install.py` script first runs the uninstaller and then reinstalls
everything. Pass `--source github` to clone a new copy from GitHub or omit the
option to reinstall from local files:

```bash
sudo python fresh_install.py --source github  # Linux/macOS from GitHub
sudo python fresh_install.py                  # Linux/macOS from local
python fresh_install.py --source github       # Windows from GitHub
python fresh_install.py                       # Windows from local
```

---

For more details see [README.md](README.md) and the documentation under `docs/`.
