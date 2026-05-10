# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/pygpt_net/tools/manager

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict

try:  # pragma: no cover - exercised when the full PyGPT UI is installed
    from pygpt_net.tools.base import BaseTool
except Exception:  # pragma: no cover - lightweight test/runtime fallback
    class BaseTool:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.window = kwargs.get("window")

try:  # pragma: no cover - exercised when the full PyGPT UI is installed
    from pygpt_net.utils import trans
except Exception:  # pragma: no cover - lightweight test/runtime fallback
    def trans(value: str) -> str:  # type: ignore[no-redef]
        return value

try:  # pragma: no cover - exercised when PySide6 is available
    from PySide6.QtGui import QAction
except Exception:  # pragma: no cover - lightweight test/runtime fallback
    class _Signal:
        def __init__(self) -> None:
            self._callback: Callable[[], None] | None = None

        def connect(self, callback: Callable[[], None]) -> None:
            self._callback = callback

        def emit(self) -> None:
            if self._callback:
                self._callback()

    class QAction:  # type: ignore[no-redef]
        def __init__(self, text: str, parent: object | None = None) -> None:
            self.text = text
            self.parent = parent
            self.triggered = _Signal()

from huey.services import container_management
from huey.pyhuey_integration import pyhuey_status


def _project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path(__file__).resolve().parents[5]


class MonkeyManager(BaseTool):
    """Expose Monkey Head management tasks in the PyGPT UI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = "monkey_manager"
        self.install_path: Path | None = None
        self.update_path: Path | None = None
        self.run_path: Path | None = None
        self._setup_paths()

    def _setup_paths(self) -> None:
        root = _project_root()
        installers = root / "platform" / "installers"
        memory_dir = root / "src" / "huey" / "memory"
        system = platform.system()
        if system == "Linux":
            debian_installers = installers / "debian" / "Debian"
            self.install_path = debian_installers / "install-deb.sh"
            self.update_path = debian_installers / "update-deb.sh"
            self.run_path = memory_dir / "SH" / "run.sh"
        elif system == "Darwin":
            mac_installers = installers / "macos" / "macOS"
            self.install_path = mac_installers / "install-mac.sh"
            self.update_path = mac_installers / "update-mac.sh"
            self.run_path = memory_dir / "SH" / "run.sh"
        elif system == "Windows":
            windows_installers = installers / "windows" / "Windows"
            self.install_path = windows_installers / "install-win.bat"
            self.update_path = windows_installers / "update-win.bat"
            self.run_path = memory_dir / "BAT" / "run.bat"

    def _run_script(self, script: Path | None) -> None:
        if script is None or not script.exists():
            print(f"Script not found: {script}")
            return
        try:
            if script.suffix == ".bat":
                cmd = ["cmd", "/c", str(script)]
            else:
                cmd = ["bash", str(script)]
            subprocess.run(cmd, check=False)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Error running {script}: {exc}")

    def _action(self, label: str, callback: Callable[[], None]) -> QAction:
        action = QAction(trans(label), self.window)
        action.triggered.connect(callback)
        return action

    def install(self) -> None:
        self._run_script(self.install_path)

    def update(self) -> None:
        self._run_script(self.update_path)

    def run_app(self) -> None:
        self._run_script(self.run_path)

    def integration_status(self) -> Dict[str, object]:
        """Return current PyHuey integration discovery details."""

        return pyhuey_status()

    def print_integration_status(self) -> None:
        """Print a readable PyHuey integration status report."""

        status = self.integration_status()
        print("PyHuey integration")
        print(f"prepared: {status['prepared']}")
        print(f"version: {status['version'] or 'unknown'}")
        print(f"module: {status['module_file'] or 'unresolved'}")

    def list_pdfs(self) -> list[str]:
        """Return PDF files visible to the HueyOS runtime."""

        from huey.pdf_utils import list_available_pdfs

        return [str(path) for path in list_available_pdfs()]

    def print_pdfs(self) -> None:
        """Print available PDFs for quick PyHuey-side diagnostics."""

        pdfs = self.list_pdfs()
        if not pdfs:
            print("No PDFs found.")
            return
        print("Available PDFs:")
        for path in pdfs:
            print(f"- {path}")

    def run_system_check(self) -> None:
        """Run HueyOS environment checks from the PyHuey menu."""

        from huey.system_checks import system_check

        system_check()

    def setup_menu(self) -> Dict[str, QAction]:
        actions: Dict[str, QAction] = {}
        actions["monkey.install"] = self._action("Monkey Install", self.install)
        actions["monkey.run"] = self._action("Monkey Run", self.run_app)
        actions["monkey.update"] = self._action("Monkey Update", self.update)
        actions["monkey.pyhuey.status"] = self._action(
            "PyHuey Status", self.print_integration_status
        )
        actions["monkey.pdfs.list"] = self._action("List PDFs", self.print_pdfs)
        actions["monkey.system.check"] = self._action(
            "System Check", self.run_system_check
        )
        actions["monkey.docker.build"] = self._action(
            "Build Docker Image", container_management.build_docker_image
        )
        actions["monkey.docker.start"] = self._action(
            "Start Containers", container_management.manage_containers
        )
        actions["monkey.docker.stop"] = self._action(
            "Stop Containers", container_management.stop_containers
        )
        actions["monkey.docker.clean"] = self._action(
            "Cleanup Images", container_management.cleanup_images
        )
        actions["monkey.docker.volumes"] = self._action(
            "Manage Volumes", container_management.manage_volumes
        )
        actions["monkey.docker.networks"] = self._action(
            "Manage Networks", container_management.manage_networks
        )
        actions["monkey.k8s.deploy"] = self._action(
            "Deploy Kubernetes", container_management.deploy_kubernetes
        )
        actions["monkey.k8s.cleanup"] = self._action(
            "Cleanup Kubernetes", container_management.cleanup_kubernetes
        )
        actions["monkey.k8s.scale"] = self._action(
            "Scale Deployment",
            lambda: container_management.scale_deployment("deployment", 1),
        )

        return actions
