"""Huey Tools plugin for the lightweight PyHuey connector."""

from __future__ import annotations

import os
from typing import Any

from ...core.events import Event
from ...item.ctx import CtxItem
from ..base.plugin import BasePlugin
from .bridge import HueyToolBridge
from .config import HueyToolsSettings, load_settings_from_env, settings_to_bridge_config
from .formatting import (
    format_bridge_result,
    format_safety_policy,
    format_status,
    format_tool_specs,
)
from .prompts import generate_task_prompt
from .registry import HueyToolRegistry
from .safety import (
    assert_action_allowed,
    default_safety_policy,
    policy_to_dict,
)


class Plugin(BasePlugin):
    """Safe cockpit bridge for HueyOS / Monkey-Head-Project tools."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.id = "huey_tools"
        self.name = "Huey Tools"
        self.description = "Safe cockpit bridge for HueyOS / Monkey-Head-Project tools."
        self.prefix = "Huey"
        self.type = ["cmd.inline", "cmd.execute", "tool"]
        self.order = 9800
        self.allowed_cmds = [
            "huey_status",
            "huey_ffmpeg_check",
            "huey_prepare_audio",
            "huey_probe_media",
            "huey_list_tools",
            "huey_generate_task_prompt",
            "huey_safety_policy",
        ]
        self.registry = HueyToolRegistry()
        self.init_options()

    def init_options(self) -> None:
        settings = load_settings_from_env()
        self.add_option(
            "monkey_head_project_path",
            type="text",
            value=settings.monkey_head_project_path,
            label="Monkey-Head-Project path",
        )
        self.add_option(
            "python_executable",
            type="text",
            value=settings.python_executable,
            label="Python executable",
        )
        self.add_option(
            "timeout_seconds",
            type="float",
            value=settings.timeout_seconds,
            label="Command timeout seconds",
        )
        self.add_option(
            "allow_external_paths",
            type="bool",
            value=settings.allow_external_paths,
            label="Allow external paths",
        )
        self.add_option(
            "allowed_workspace_roots",
            type="text",
            value=os.pathsep.join(settings.allowed_workspace_roots),
            label="Allowed workspace roots",
        )

    def setup_menu(self) -> dict[str, object]:
        return {
            "huey_tools.status": lambda: self.execute_command(
                "huey_status", {"include_paths": True, "include_environment": True}
            ),
            "huey_tools.list": lambda: self.execute_command("huey_list_tools", {}),
        }

    def cmd_syntax(self, data: dict[str, object] | None = None) -> list[dict[str, object]]:
        return [
            {
                "cmd": "huey_status",
                "instruction": "Return Huey bridge configuration status.",
                "params": [
                    {"name": "include_paths", "type": "bool", "required": False},
                    {"name": "include_environment", "type": "bool", "required": False},
                ],
            },
            {
                "cmd": "huey_ffmpeg_check",
                "instruction": "Validate FFmpeg readiness through a fixed wrapper.",
                "params": [
                    {"name": "strict", "type": "bool", "required": False},
                    {"name": "json", "type": "bool", "required": False},
                ],
            },
            {
                "cmd": "huey_prepare_audio",
                "instruction": "Prepare an audio file for transcription.",
                "params": [
                    {"name": "source_path", "type": "str", "required": True},
                    {"name": "output_path", "type": "str", "required": False},
                    {"name": "overwrite", "type": "bool", "required": False},
                ],
            },
            {
                "cmd": "huey_probe_media",
                "instruction": "Probe media metadata using a fixed wrapper.",
                "params": [{"name": "path", "type": "str", "required": True}],
            },
            {
                "cmd": "huey_list_tools",
                "instruction": "List available Huey tool groups and readiness.",
                "params": [{"name": "group", "type": "str", "required": False}],
            },
            {
                "cmd": "huey_generate_task_prompt",
                "instruction": "Generate an implementation prompt for a known task id.",
                "params": [
                    {"name": "task_id", "type": "str", "required": True},
                    {"name": "target_repo", "type": "str", "required": False},
                ],
            },
            {
                "cmd": "huey_safety_policy",
                "instruction": "Return the current Huey Tools safety policy.",
                "params": [
                    {
                        "name": "include_blocked_actions",
                        "type": "bool",
                        "required": False,
                    }
                ],
            },
        ]

    def handle(self, event: object, *args: Any, **kwargs: Any) -> object | None:
        name = getattr(event, "name", None)
        data = getattr(event, "data", None)
        ctx = getattr(event, "ctx", None)
        if not isinstance(data, dict):
            data = {}
        if name == Event.CMD_SYNTAX:
            data["commands"] = self.cmd_syntax(data)
            return data["commands"]
        if name in {Event.CMD_EXECUTE, Event.CMD_INLINE}:
            return self.cmd(ctx, data.get("commands", []))
        return None

    def cmd(self, ctx: CtxItem | None, cmds: list) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for item in cmds:
            if not isinstance(item, dict):
                continue
            name = str(item.get("cmd", ""))
            params = item.get("params", {})
            if name not in self.allowed_cmds:
                results.append(
                    {"cmd": name, "ok": False, "error": f"Unsupported command: {name}"}
                )
                continue
            if not isinstance(params, dict):
                params = {}
            results.append(self.execute_command(name, params))
        if ctx is not None:
            ctx.extra[self.id] = results
        return results

    def execute_command(
        self, command_name: str, params: dict[str, object]
    ) -> dict[str, object]:
        policy = default_safety_policy()
        bridge = self._bridge()
        try:
            if command_name == "huey_status":
                assert_action_allowed("status", policy)
                result = self._status_payload(
                    bridge,
                    include_paths=bool(params.get("include_paths", True)),
                    include_environment=bool(params.get("include_environment", True)),
                )
                return {
                    "cmd": command_name,
                    "ok": True,
                    "result": result,
                    "display": format_status(result),
                }

            if command_name == "huey_ffmpeg_check":
                assert_action_allowed("ffmpeg_validate", policy)
                result = bridge.check_ffmpeg(strict=bool(params.get("strict", False)))
                return {
                    "cmd": command_name,
                    "ok": result.ok,
                    "result": result.to_dict(),
                    "display": format_bridge_result(result),
                }

            if command_name == "huey_prepare_audio":
                assert_action_allowed("audio_prepare", policy)
                overwrite = bool(params.get("overwrite", False))
                if overwrite and not policy.allow_overwrite:
                    raise PermissionError("Overwrite is blocked by safety policy")
                source_path = self._require_str(params, "source_path")
                output_path = params.get("output_path")
                result = bridge.prepare_audio(
                    source_path,
                    output_path=None if output_path is None else str(output_path),
                    overwrite=overwrite,
                )
                return {
                    "cmd": command_name,
                    "ok": result.ok,
                    "result": result.to_dict(),
                    "display": format_bridge_result(result),
                }

            if command_name == "huey_probe_media":
                assert_action_allowed("media_probe", policy)
                result = bridge.probe_media(self._require_str(params, "path"))
                return {
                    "cmd": command_name,
                    "ok": result.ok,
                    "result": result.to_dict(),
                    "display": format_bridge_result(result),
                }

            if command_name == "huey_list_tools":
                assert_action_allowed("list_tools", policy)
                group = params.get("group")
                payload = self._tool_listing(
                    bridge,
                    group=None if group is None else str(group),
                )
                return {
                    "cmd": command_name,
                    "ok": True,
                    "result": payload,
                    "display": format_tool_specs(self.registry.list_specs(group=payload["group"])),
                }

            if command_name == "huey_generate_task_prompt":
                assert_action_allowed("generate_prompt", policy)
                prompt = generate_task_prompt(
                    self._require_str(params, "task_id"),
                    target_repo=str(params.get("target_repo", "Monkey-Head-Project")),
                )
                return {
                    "cmd": command_name,
                    "ok": True,
                    "result": {"prompt": prompt},
                    "display": prompt,
                }

            if command_name == "huey_safety_policy":
                assert_action_allowed("safety_policy", policy)
                payload = policy_to_dict(policy)
                if not bool(params.get("include_blocked_actions", True)):
                    payload.pop("blocked_actions", None)
                return {
                    "cmd": command_name,
                    "ok": True,
                    "result": payload,
                    "display": format_safety_policy(policy),
                }
        except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
            return {"cmd": command_name, "ok": False, "error": str(exc)}

        return {"cmd": command_name, "ok": False, "error": "Unknown command"}

    def _settings(self) -> HueyToolsSettings:
        env_settings = load_settings_from_env()
        project_path = self.get_option_value(
            "monkey_head_project_path", env_settings.monkey_head_project_path
        )
        python_executable = self.get_option_value(
            "python_executable", env_settings.python_executable
        )
        timeout_seconds = float(
            self.get_option_value("timeout_seconds", env_settings.timeout_seconds)
        )
        allow_external_paths = bool(
            self.get_option_value(
                "allow_external_paths", env_settings.allow_external_paths
            )
        )
        workspace_raw = self.get_option_value("allowed_workspace_roots", "")
        if isinstance(workspace_raw, str):
            allowed_roots = [value for value in workspace_raw.split(os.pathsep) if value]
        elif isinstance(workspace_raw, list):
            allowed_roots = [str(value) for value in workspace_raw if value]
        else:
            allowed_roots = list(env_settings.allowed_workspace_roots)
        return HueyToolsSettings(
            monkey_head_project_path=None if not project_path else str(project_path),
            python_executable=None if not python_executable else str(python_executable),
            timeout_seconds=timeout_seconds,
            allow_external_paths=allow_external_paths,
            allowed_workspace_roots=allowed_roots,
        )

    def _bridge(self) -> HueyToolBridge:
        return HueyToolBridge(settings_to_bridge_config(self._settings()))

    @staticmethod
    def _require_str(params: dict[str, object], key: str) -> str:
        value = params.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing required string parameter: {key}")
        return value

    def _status_payload(
        self,
        bridge: HueyToolBridge,
        *,
        include_paths: bool,
        include_environment: bool,
    ) -> dict[str, object]:
        payload = {
            "bridge": bridge.status(),
            "safety_policy": policy_to_dict(default_safety_policy()),
        }
        if include_paths:
            payload["paths"] = {
                "project_path": self._settings().monkey_head_project_path,
                "python_executable": self._settings().python_executable,
            }
        if include_environment:
            payload["environment"] = {
                "HUEY_MONKEY_HEAD_PROJECT_PATH": os.getenv(
                    "HUEY_MONKEY_HEAD_PROJECT_PATH"
                ),
                "HUEY_PYTHON_EXECUTABLE": os.getenv("HUEY_PYTHON_EXECUTABLE"),
                "HUEY_TOOLS_TIMEOUT_SECONDS": os.getenv(
                    "HUEY_TOOLS_TIMEOUT_SECONDS"
                ),
                "HUEY_TOOLS_ALLOW_EXTERNAL_PATHS": os.getenv(
                    "HUEY_TOOLS_ALLOW_EXTERNAL_PATHS"
                ),
            }
        return payload

    def _tool_listing(
        self, bridge: HueyToolBridge, *, group: str | None
    ) -> dict[str, object]:
        available_scripts = bridge.list_available_scripts()
        specs = []
        for spec in self.registry.list_specs(group=group):
            availability = spec.implemented
            if spec.command_name == "huey_ffmpeg_check":
                availability = available_scripts["check_ffmpeg_environment"]
            elif spec.command_name == "huey_prepare_audio":
                availability = available_scripts["prepare_audio_for_transcription"]
            elif spec.command_name == "huey_probe_media":
                availability = available_scripts["probe_media"]
            specs.append(
                {
                    "id": spec.id,
                    "name": spec.name,
                    "group": spec.group,
                    "implemented": spec.implemented,
                    "safe_by_default": spec.safe_by_default,
                    "available": availability,
                }
            )
        return {"group": group, "tools": specs}


__all__ = ["Plugin"]
