# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/pygpt_net/tools/manager

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Dict

from pygpt_net.tools.base import BaseTool
from pygpt_net.utils import trans
from PySide6.QtGui import QAction

from ...services import container_management


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
        root = Path(__file__).resolve().parents[4]
        setup_dir = root / "setup"
        platform_installers = root / "platform" / "installers" / "debian" / "Debian"
        system = platform.system()
        if system == "Linux":
            self.install_path = platform_installers / "install-deb.sh"
            self.update_path = platform_installers / "update-deb.sh"
            self.run_path = root / "run.sh"
        elif system == "Darwin":
            self.install_path = setup_dir / "macOS" / "install.sh"
            self.update_path = platform_installers / "update-deb.sh"
            self.run_path = root / "run.sh"
        elif system == "Windows":
            self.install_path = setup_dir / "Windows11" / "01-FULL.bat"
            self.update_path = setup_dir / "Windows11" / "01-FULL.bat"
            self.run_path = root / "run.bat"

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
        except Exception as exc:  # pragma: no cover - subprocess failures
            print(f"Error running {script}: {exc}")

    def install(self) -> None:
        self._run_script(self.install_path)

    def update(self) -> None:
        self._run_script(self.update_path)

    def run_app(self) -> None:
        self._run_script(self.run_path)

    def setup_menu(self) -> Dict[str, QAction]:
        actions: Dict[str, QAction] = {}
        actions["monkey.install"] = QAction(trans("Monkey Install"), self.window)
        actions["monkey.install"].triggered.connect(self.install)

        actions["monkey.run"] = QAction(trans("Monkey Run"), self.window)
        actions["monkey.run"].triggered.connect(self.run_app)

        actions["monkey.update"] = QAction(trans("Monkey Update"), self.window)
        actions["monkey.update"].triggered.connect(self.update)

        actions["monkey.docker.build"] = QAction(
            trans("Build Docker Image"), self.window
        )
        actions["monkey.docker.build"].triggered.connect(
            container_management.build_docker_image
        )

        actions["monkey.docker.start"] = QAction(trans("Start Containers"), self.window)
        actions["monkey.docker.start"].triggered.connect(
            container_management.manage_containers
        )

        actions["monkey.docker.stop"] = QAction(trans("Stop Containers"), self.window)
        actions["monkey.docker.stop"].triggered.connect(
            container_management.stop_containers
        )

        actions["monkey.docker.clean"] = QAction(trans("Cleanup Images"), self.window)
        actions["monkey.docker.clean"].triggered.connect(
            container_management.cleanup_images
        )

        actions["monkey.docker.volumes"] = QAction(trans("Manage Volumes"), self.window)
        actions["monkey.docker.volumes"].triggered.connect(
            container_management.manage_volumes
        )

        actions["monkey.docker.networks"] = QAction(
            trans("Manage Networks"), self.window
        )
        actions["monkey.docker.networks"].triggered.connect(
            container_management.manage_networks
        )

        actions["monkey.k8s.deploy"] = QAction(trans("Deploy Kubernetes"), self.window)
        actions["monkey.k8s.deploy"].triggered.connect(
            container_management.deploy_kubernetes
        )

        actions["monkey.k8s.cleanup"] = QAction(
            trans("Cleanup Kubernetes"), self.window
        )
        actions["monkey.k8s.cleanup"].triggered.connect(
            container_management.cleanup_kubernetes
        )

        actions["monkey.k8s.scale"] = QAction(trans("Scale Deployment"), self.window)
        actions["monkey.k8s.scale"].triggered.connect(
            lambda: container_management.scale_deployment("deployment", 1)
        )

        return actions
