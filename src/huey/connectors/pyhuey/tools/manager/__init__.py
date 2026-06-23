# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/pygpt_net/tools/manager

from __future__ import annotations

from collections import defaultdict
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict

LOGGER = logging.getLogger(__name__)


try:  # pragma: no cover - exercised when the full PyGPT UI is installed
    from pygpt_net.tools.base import BaseTool
except (
    ImportError,
    ModuleNotFoundError,
):  # pragma: no cover - lightweight test/runtime fallback

    class BaseTool:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.window = kwargs.get("window")


try:  # pragma: no cover - exercised when the full PyGPT UI is installed
    from pygpt_net.utils import trans
except (
    ImportError,
    ModuleNotFoundError,
):  # pragma: no cover - lightweight test/runtime fallback

    def trans(value: str) -> str:  # type: ignore[no-redef]
        return value


try:  # pragma: no cover - exercised when PySide6 is available
    from PySide6.QtGui import QAction
except (
    ImportError,
    ModuleNotFoundError,
):  # pragma: no cover - lightweight test/runtime fallback

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


from huey.pyhuey_integration import pyhuey_status
from huey.services import container_management
from huey.function_registry import (
    describe_functions,
    ensure_registered_functions,
    invoke_function,
)
from huey.os.core.platform_support import (
    build_platform_script_command,
    detect_host_platform,
    find_project_root,
    resolve_platform_script_paths,
)


def _project_root() -> Path:
    return find_project_root(Path(__file__).resolve())


class MonkeyManager(BaseTool):
    """Expose Monkey Head management tasks in the PyGPT UI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = "monkey_manager"
        self.install_path: Path | None = None
        self.update_path: Path | None = None
        self.run_path: Path | None = None
        self._setup_paths()
        ensure_registered_functions()

    def _setup_paths(self) -> None:
        paths = resolve_platform_script_paths(_project_root())
        self.install_path = paths.install
        self.update_path = paths.update
        self.run_path = paths.run

    def _run_script(self, script: Path | None) -> None:
        if script is None or not script.exists():
            LOGGER.error("Script not found: %s", script)
            return
        try:
            cmd = build_platform_script_command(script)
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                LOGGER.error(
                    "Script failed with exit code %s: %s", result.returncode, script
                )
        except OSError as exc:
            LOGGER.exception("Error running script %s: %s", script, exc)

    def _destructive_intent_confirmed(self) -> bool:
        return os.getenv(self.DESTRUCTIVE_ENV_FLAG, "").strip() == "1"

    def _run_destructive_action(
        self, action_name: str, callback: Callable[[], None]
    ) -> None:
        if not self._destructive_intent_confirmed():
            LOGGER.warning(
                "Blocked destructive action '%s'; set %s=1 to allow.",
                action_name,
                self.DESTRUCTIVE_ENV_FLAG,
            )
            return
        callback()

    def _action(self, label: str, callback: Callable[[], None]) -> QAction:
        action = QAction(trans(label), self.window)
        action.triggered.connect(callback)
        return action

    @staticmethod
    def _json_ready_path(path: Path | None) -> dict[str, object]:
        return {
            "path": None if path is None else str(path),
            "exists": bool(path and path.exists()),
        }

    @staticmethod
    def _print_json(payload: object) -> None:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))

    def install(self) -> None:
        self._run_script(self.install_path)

    def update(self) -> None:
        self._run_script(self.update_path)

    def run_app(self) -> None:
        self._run_script(self.run_path)

    def integration_status(self) -> Dict[str, object]:
        """Return current PyHuey integration discovery details."""

        return pyhuey_status()

    def path_status(self) -> Dict[str, object]:
        """Return resolved project and launcher paths for the current platform."""

        host = detect_host_platform()
        return {
            "platform": host.display_name,
            "platform_family": host.family,
            "project_root": str(_project_root()),
            "install": self._json_ready_path(self.install_path),
            "update": self._json_ready_path(self.update_path),
            "run": self._json_ready_path(self.run_path),
        }

    def print_path_status(self) -> None:
        """Print the resolved project and launcher paths."""

        self._print_json(self.path_status())

    def print_integration_status(self) -> None:
        """Print a readable PyHuey integration status report."""

        status = self.integration_status()
        print("PyHuey integration")
        print(f"prepared: {status['prepared']}")
        print(f"version: {status['version'] or 'unknown'}")
        print(f"module: {status['module_file'] or 'unresolved'}")
        print(f"custom functions: {status['custom_function_count']}")
        for function in status["custom_functions"]:
            print(f"- {function['name']}{function['signature']}")

    def registered_functions(self) -> list[dict[str, object]]:
        """Return structured metadata for registered custom functions."""

        ensure_registered_functions()
        return describe_functions()

    def print_registered_functions(self) -> None:
        """Print the custom functions available through the PyHuey bridge."""

        functions = self.registered_functions()
        if not functions:
            print("No custom functions registered.")
            return

        print("Custom functions:")
        for function in functions:
            print(
                "  - "
                f"{function['name']}{function['signature']} :: {function['module']}"
            )

    def invoke_registered_function(self, function_name: str, /, **kwargs: object) -> Any:
        """Invoke a registered custom function by name."""

        return invoke_function(function_name, **kwargs)

    def action_catalog(self) -> list[dict[str, object]]:
        """Return structured metadata for the manager menu/actions."""

        return [dict(spec) for spec, _callback in self._action_specs()]

    def gui_payload(self) -> dict[str, object]:
        """Return a structured GUI/dashboard payload for the PyHuey side."""

        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for action in self.action_catalog():
            grouped[str(action["group"])].append(action)

        return {
            "id": self.id,
            "title": "Monkey Manager",
            "paths": self.path_status(),
            "integration": self.integration_status(),
            "custom_functions": self.registered_functions(),
            "action_groups": [
                {"group": group, "actions": actions}
                for group, actions in sorted(grouped.items())
            ],
        }

    def print_gui_payload(self) -> None:
        """Print the full GUI/dashboard payload for the manager."""

        self._print_json(self.gui_payload())

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

    def print_registered_function_result(
        self, function_name: str, /, **kwargs: object
    ) -> None:
        """Invoke and print a registered custom function result."""

        result = self.invoke_registered_function(function_name, **kwargs)
        self._print_json(result)

    def _action_specs(self) -> list[tuple[dict[str, object], Callable[[], None]]]:
        return [
            (
                {
                    "id": "monkey.install",
                    "label": "Monkey Install",
                    "group": "runtime",
                    "available": bool(self.install_path and self.install_path.exists()),
                    "destructive": False,
                    "description": "Run the platform installer for the current OS.",
                },
                self.install,
            ),
            (
                {
                    "id": "monkey.run",
                    "label": "Monkey Run",
                    "group": "runtime",
                    "available": bool(self.run_path and self.run_path.exists()),
                    "destructive": False,
                    "description": "Launch the primary project runtime script.",
                },
                self.run_app,
            ),
            (
                {
                    "id": "monkey.update",
                    "label": "Monkey Update",
                    "group": "runtime",
                    "available": bool(self.update_path and self.update_path.exists()),
                    "destructive": False,
                    "description": "Run the platform update script for the current OS.",
                },
                self.update,
            ),
            (
                {
                    "id": "monkey.pyhuey.status",
                    "label": "PyHuey Status",
                    "group": "integration",
                    "available": True,
                    "destructive": False,
                    "description": "Print the current PyHuey discovery and readiness report.",
                },
                self.print_integration_status,
            ),
            (
                {
                    "id": "monkey.paths.status",
                    "label": "Project Paths",
                    "group": "integration",
                    "available": True,
                    "destructive": False,
                    "description": "Print resolved project, install, update, and run paths.",
                },
                self.print_path_status,
            ),
            (
                {
                    "id": "monkey.gui.snapshot",
                    "label": "GUI Snapshot",
                    "group": "integration",
                    "available": True,
                    "destructive": False,
                    "description": "Print the structured MonkeyManager GUI/dashboard payload.",
                },
                self.print_gui_payload,
            ),
            (
                {
                    "id": "monkey.functions.list",
                    "label": "List Custom Functions",
                    "group": "custom_functions",
                    "available": True,
                    "destructive": False,
                    "description": "List the registered custom functions and their signatures.",
                },
                self.print_registered_functions,
            ),
            (
                {
                    "id": "monkey.pdfs.list",
                    "label": "List PDFs",
                    "group": "memory",
                    "available": True,
                    "destructive": False,
                    "description": "List PDF files visible to the HueyOS runtime.",
                },
                self.print_pdfs,
            ),
            (
                {
                    "id": "monkey.system.check",
                    "label": "System Check",
                    "group": "diagnostics",
                    "available": True,
                    "destructive": False,
                    "description": "Run the HueyOS environment diagnostics.",
                },
                self.run_system_check,
            ),
            (
                {
                    "id": "monkey.docker.build",
                    "label": "Build Docker Image",
                    "group": "docker",
                    "available": True,
                    "destructive": False,
                    "description": "Build the configured project Docker image.",
                },
                container_management.build_docker_image,
            ),
            (
                {
                    "id": "monkey.docker.start",
                    "label": "Start Containers",
                    "group": "docker",
                    "available": True,
                    "destructive": False,
                    "description": "Start the project's container stack.",
                },
                container_management.manage_containers,
            ),
            (
                {
                    "id": "monkey.docker.stop",
                    "label": "Stop Containers",
                    "group": "docker",
                    "available": True,
                    "destructive": True,
                    "description": "Stop running project containers after explicit intent confirmation.",
                },
                lambda: self._run_destructive_action(
                    "stop_containers", container_management.stop_containers
                ),
            ),
            (
                {
                    "id": "monkey.docker.clean",
                    "label": "Cleanup Images",
                    "group": "docker",
                    "available": True,
                    "destructive": True,
                    "description": "Remove stale project container images after explicit intent confirmation.",
                },
                lambda: self._run_destructive_action(
                    "cleanup_images", container_management.cleanup_images
                ),
            ),
            (
                {
                    "id": "monkey.docker.volumes",
                    "label": "Manage Volumes",
                    "group": "docker",
                    "available": True,
                    "destructive": False,
                    "description": "Inspect or manage project container volumes.",
                },
                container_management.manage_volumes,
            ),
            (
                {
                    "id": "monkey.docker.networks",
                    "label": "Manage Networks",
                    "group": "docker",
                    "available": True,
                    "destructive": False,
                    "description": "Inspect or manage project container networks.",
                },
                container_management.manage_networks,
            ),
            (
                {
                    "id": "monkey.k8s.deploy",
                    "label": "Deploy Kubernetes",
                    "group": "kubernetes",
                    "available": True,
                    "destructive": False,
                    "description": "Deploy the project's Kubernetes resources.",
                },
                container_management.deploy_kubernetes,
            ),
            (
                {
                    "id": "monkey.k8s.cleanup",
                    "label": "Cleanup Kubernetes",
                    "group": "kubernetes",
                    "available": True,
                    "destructive": True,
                    "description": "Remove Kubernetes resources after explicit intent confirmation.",
                },
                lambda: self._run_destructive_action(
                    "cleanup_kubernetes", container_management.cleanup_kubernetes
                ),
            ),
            (
                {
                    "id": "monkey.k8s.scale",
                    "label": "Scale Deployment",
                    "group": "kubernetes",
                    "available": True,
                    "destructive": False,
                    "description": "Scale the default project deployment.",
                },
                lambda: container_management.scale_deployment("deployment", 1),
            ),
        ]

    def setup_menu(self) -> Dict[str, QAction]:
        actions: Dict[str, QAction] = {}
        for spec, callback in self._action_specs():
            actions[str(spec["id"])] = self._action(str(spec["label"]), callback)

        return actions

    DESTRUCTIVE_ENV_FLAG = "HUEY_TOOL_ALLOW_DESTRUCTIVE"
