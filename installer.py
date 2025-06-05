import os
import platform
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LINUX_INSTALL = os.path.join(SCRIPT_DIR, "setup", "Debian13", "install.sh")
MAC_INSTALL = os.path.join(SCRIPT_DIR, "setup", "macOS", "install.sh")
WINDOWS_INSTALL = os.path.join(SCRIPT_DIR, "setup", "Windows11", "01-FULL.bat")


def update_submodules() -> None:
    """Ensure git submodules are initialized."""
    try:
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to update submodules: {exc.returncode}")
        raise


def run_installer():
    system = platform.system()
    try:
        update_submodules()
        if system == "Linux":
            subprocess.run(["bash", LINUX_INSTALL], check=True)
        elif system == "Darwin":
            subprocess.run(["bash", MAC_INSTALL], check=True)
        elif system == "Windows":
            subprocess.run(["cmd", "/c", WINDOWS_INSTALL], check=True)
        else:
            print(f"Unsupported operating system: {system}")
            return 1
    except subprocess.CalledProcessError as exc:
        print(f"Installer failed with return code {exc.returncode}")
        return exc.returncode
    return 0


if __name__ == "__main__":
    sys.exit(run_installer())
