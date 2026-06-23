"""Shared catalog of HueyOS GUI workflows, connectors, and windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

GuiLaunchMode = Literal["workflow", "window", "dialog", "browser"]


@dataclass(frozen=True)
class GuiAction:
    """Describe a user-facing action exposed by the unified GUI shell."""

    id: str
    label: str
    description: str
    source: str
    launch_mode: GuiLaunchMode
    module_name: str | None = None
    function_name: str | None = None
    entry_point: str = ""


@dataclass(frozen=True)
class GuiActionSection:
    """Describe a launcher section and the action ids it should render."""

    id: str
    tab_id: str
    tab_title: str
    title: str
    description: str
    action_ids: tuple[str, ...]


def default_gui_actions() -> tuple[GuiAction, ...]:
    """Return the canonical set of unified GUI actions."""

    return (
        GuiAction(
            id="install",
            label="Install",
            description="Prepare the local platform scripts.",
            source="launch-pad",
            launch_mode="workflow",
            entry_point="internal:install",
        ),
        GuiAction(
            id="graphical-installer",
            label="Graphical Installer",
            description=(
                "Open the guided installer flow, including license review and "
                "hardware/software selection."
            ),
            source="installer",
            launch_mode="window",
            module_name="huey.install_gui",
            function_name="launch_install_gui",
            entry_point="huey.install_gui:launch_install_gui",
        ),
        GuiAction(
            id="run",
            label="Run",
            description="Launch the main runtime entrypoint.",
            source="launch-pad",
            launch_mode="workflow",
            entry_point="internal:run",
        ),
        GuiAction(
            id="update",
            label="Update",
            description="Refresh the local install helpers.",
            source="launch-pad",
            launch_mode="workflow",
            entry_point="internal:update",
        ),
        GuiAction(
            id="clear-log",
            label="Clear Log",
            description="Reset the command log for the next task.",
            source="launch-pad",
            launch_mode="workflow",
            entry_point="internal:clear-log",
        ),
        GuiAction(
            id="command-center",
            label="Command Center",
            description=(
                "Open the read-only Command Center dashboard in the browser so it "
                "can stay visible alongside the desktop shell."
            ),
            source="command-center",
            launch_mode="browser",
            module_name="huey.apps.command_center.cli",
            function_name="open_command_center",
            entry_point="huey.apps.command_center.cli:open_command_center",
        ),
        GuiAction(
            id="data-summary",
            label="Data Summary",
            description="Count bundled prompts and memory files.",
            source="memory",
            launch_mode="dialog",
            entry_point="internal:data-summary",
        ),
        GuiAction(
            id="license",
            label="License",
            description="Open the current license agreement for review.",
            source="license",
            launch_mode="dialog",
            module_name="huey.license_gui",
            function_name="show_license_gui",
            entry_point="huey.license_gui:show_license_gui",
        ),
        GuiAction(
            id="config-toggles",
            label="Config Toggles",
            description="Adjust common runtime toggles in a separate window.",
            source="config",
            launch_mode="window",
            module_name="huey.config_toggle_gui",
            function_name="run_config_toggle_gui",
            entry_point="huey.config_toggle_gui:run_config_toggle_gui",
        ),
        GuiAction(
            id="simple-chat",
            label="Simple Chat",
            description="Open the lightweight chat demonstration.",
            source="chat",
            launch_mode="window",
            module_name="huey.simple_chat_gui",
            function_name="run_simple_chat",
            entry_point="huey.simple_chat_gui:run_simple_chat",
        ),
        GuiAction(
            id="ai-console",
            label="AI Console",
            description="Launch the notebook-style AI tools console.",
            source="ai-console",
            launch_mode="window",
            module_name="huey.memory.PY.ai_tools_gui",
            function_name="run_ai_tools",
            entry_point="huey.memory.PY.ai_tools_gui:run_ai_tools",
        ),
        GuiAction(
            id="dashboard",
            label="Dashboard",
            description="Open the operations dashboard in its own process.",
            source="dashboard",
            launch_mode="window",
            module_name="huey.memory.PY.dashboard",
            function_name="launch_dashboard",
            entry_point="huey.memory.PY.dashboard:launch_dashboard",
        ),
        GuiAction(
            id="convert-media",
            label="Convert Media",
            description="Convert a source media file to another format.",
            source="media",
            launch_mode="workflow",
            entry_point="internal:convert-media",
        ),
        GuiAction(
            id="build-image",
            label="Build Image",
            description="Build the Docker image.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:build-image",
        ),
        GuiAction(
            id="start-containers",
            label="Start Containers",
            description="Start the container stack.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:start-containers",
        ),
        GuiAction(
            id="stop-containers",
            label="Stop Containers",
            description="Stop running containers.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:stop-containers",
        ),
        GuiAction(
            id="manage-volumes",
            label="Manage Volumes",
            description="Open the volume management action.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:manage-volumes",
        ),
        GuiAction(
            id="manage-networks",
            label="Manage Networks",
            description="Open the network management action.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:manage-networks",
        ),
        GuiAction(
            id="deploy-kubernetes",
            label="Deploy",
            description="Apply the Kubernetes resources.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:deploy-kubernetes",
        ),
        GuiAction(
            id="scale-deployment",
            label="Scale Deployment",
            description="Change the deployment replica count.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:scale-deployment",
        ),
        GuiAction(
            id="get-pod-logs",
            label="Get Pod Logs",
            description="Read the logs for a selected pod.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:get-pod-logs",
        ),
        GuiAction(
            id="cleanup-kubernetes",
            label="Cleanup",
            description="Remove deployed Kubernetes resources.",
            source="runtime",
            launch_mode="workflow",
            entry_point="internal:cleanup-kubernetes",
        ),
    )


def default_gui_sections() -> tuple[GuiActionSection, ...]:
    """Return the launcher sections that compose the unified shell."""

    return (
        GuiActionSection(
            id="launch-core",
            tab_id="launch-pad",
            tab_title="Launch Pad",
            title="Core lifecycle",
            description=(
                "Get the machine ready, launch the program, or reset the visible "
                "log without leaving the same control deck."
            ),
            action_ids=(
                "install",
                "graphical-installer",
                "run",
                "update",
                "clear-log",
            ),
        ),
        GuiActionSection(
            id="launch-guidance",
            tab_id="launch-pad",
            tab_title="Launch Pad",
            title="Readiness and policy",
            description=(
                "Keep the project data summary, license review, and browser-based "
                "Command Center one click away."
            ),
            action_ids=("command-center", "data-summary", "license"),
        ),
        GuiActionSection(
            id="connected-windows",
            tab_id="connectors-and-windows",
            tab_title="Connectors & Windows",
            title="Unified project surfaces",
            description=(
                "Open every maintained GUI window and browser surface from one "
                "connected workbench instead of hunting across separate entrypoints."
            ),
            action_ids=(
                "command-center",
                "graphical-installer",
                "simple-chat",
                "ai-console",
                "dashboard",
            ),
        ),
        GuiActionSection(
            id="connected-utilities",
            tab_id="connectors-and-windows",
            tab_title="Connectors & Windows",
            title="Popups and utility windows",
            description=(
                "Keep the smaller policy and configuration surfaces in the same "
                "shell so dialogs like license review stay part of the larger flow."
            ),
            action_ids=("license", "config-toggles", "data-summary"),
        ),
        GuiActionSection(
            id="runtime-media",
            tab_id="runtime-ops",
            tab_title="Runtime Ops",
            title="Media and runtime helpers",
            description=(
                "Prepare assets and operate the local runtime from one consistent "
                "desktop workflow."
            ),
            action_ids=(
                "convert-media",
                "build-image",
                "start-containers",
                "stop-containers",
                "manage-volumes",
                "manage-networks",
            ),
        ),
        GuiActionSection(
            id="runtime-kubernetes",
            tab_id="runtime-ops",
            tab_title="Runtime Ops",
            title="Kubernetes",
            description=(
                "Deploy, scale, inspect logs, and clean up cluster resources "
                "without switching to a separate launcher."
            ),
            action_ids=(
                "deploy-kubernetes",
                "scale-deployment",
                "get-pod-logs",
                "cleanup-kubernetes",
            ),
        ),
    )


def action_lookup(
    actions: tuple[GuiAction, ...] | None = None,
) -> dict[str, GuiAction]:
    """Return actions keyed by id."""

    return {action.id: action for action in actions or default_gui_actions()}


def section_actions(
    section: GuiActionSection,
    actions: tuple[GuiAction, ...] | None = None,
) -> tuple[GuiAction, ...]:
    """Resolve ``section.action_ids`` into concrete action descriptors."""

    indexed = action_lookup(actions)
    return tuple(indexed[action_id] for action_id in section.action_ids)


def default_gui_surfaces(
    actions: tuple[GuiAction, ...] | None = None,
) -> tuple[GuiAction, ...]:
    """Return only the actions that open visible GUI/browser surfaces."""

    return tuple(
        action
        for action in (actions or default_gui_actions())
        if action.launch_mode != "workflow"
    )


__all__ = [
    "GuiAction",
    "GuiActionSection",
    "GuiLaunchMode",
    "action_lookup",
    "default_gui_actions",
    "default_gui_sections",
    "default_gui_surfaces",
    "section_actions",
]
