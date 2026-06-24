"""Registry of safe Huey tool capabilities exposed in PyHuey."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class HueyToolSpec:
    id: str
    name: str
    group: str
    description: str
    command_name: str | None
    implemented: bool
    safe_by_default: bool
    target_repo: str
    target_module_or_script: str | None
    notes: str = ""


def list_tool_specs(group: str | None = None) -> list[HueyToolSpec]:
    specs = [
        HueyToolSpec(
            id="ffmpeg_environment_check",
            name="FFmpeg environment check",
            group="media",
            description="Validate FFmpeg and ffprobe readiness through fixed wrappers.",
            command_name="huey_ffmpeg_check",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script="scripts/check_ffmpeg_environment.py",
        ),
        HueyToolSpec(
            id="speech_prepare_audio",
            name="Prepare audio for transcription",
            group="speech",
            description=(
                "Prepare an audio file using the Huey speech pipeline wrapper and "
                "emit structured pipeline metadata."
            ),
            command_name="huey_prepare_audio",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script="scripts/prepare_audio_for_transcription.py",
        ),
        HueyToolSpec(
            id="media_probe",
            name="Probe media",
            group="video",
            description="Inspect media metadata via the Huey media probe wrapper.",
            command_name="huey_probe_media",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script="scripts/probe_media.py",
        ),
        HueyToolSpec(
            id="huey_status",
            name="Huey bridge status",
            group="pyhuey",
            description="Report PyHuey/Monkey-Head-Project bridge status and safety mode.",
            command_name="huey_status",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script=None,
        ),
        HueyToolSpec(
            id="safety_policy",
            name="Safety policy",
            group="security",
            description="Display the current read-only Huey bridge safety policy.",
            command_name="huey_safety_policy",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script=None,
        ),
        HueyToolSpec(
            id="task_prompt_generator",
            name="Task prompt generator",
            group="runtime",
            description="Generate implementation prompts for known Huey tasks.",
            command_name="huey_generate_task_prompt",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script=None,
        ),
        HueyToolSpec(
            id="tool_registry",
            name="Tool registry",
            group="runtime",
            description="List supported and planned Huey tools.",
            command_name="huey_list_tools",
            implemented=True,
            safe_by_default=True,
            target_repo="Monkey-Head-Project",
            target_module_or_script=None,
        ),
        HueyToolSpec(
            id="video_pipeline",
            name="Video pipeline",
            group="video",
            description="Future structured video pipeline orchestration.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/media/video_pipeline.py",
        ),
        HueyToolSpec(
            id="command_center_backend",
            name="Command Center backend",
            group="command_center",
            description="Future Command Center bridge integration.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/apps/command_center/server.py",
        ),
        HueyToolSpec(
            id="gui_unification",
            name="GUI unification",
            group="gui",
            description="Future GUI unification planning for PyHuey and HueyOS.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/gui",
        ),
        HueyToolSpec(
            id="runtime_orchestrator",
            name="Runtime orchestrator",
            group="runtime",
            description="Future runtime orchestration hooks.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/runtime/orchestrator.py",
        ),
        HueyToolSpec(
            id="memory_ingestion",
            name="Memory ingestion",
            group="memory",
            description="Future memory ingestion tooling.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/memory",
        ),
        HueyToolSpec(
            id="hardware_simulation",
            name="Hardware simulation",
            group="hardware_sim",
            description="Future simulation-first hardware tooling.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/hardware",
        ),
        HueyToolSpec(
            id="governance_mock",
            name="Governance mock",
            group="governance_mock",
            description="Future audit-first governance tools.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="Monkey-Head-Project",
            target_module_or_script="src/huey/governance",
        ),
        HueyToolSpec(
            id="pyhuey_package_rename",
            name="PyHuey package rename",
            group="pyhuey",
            description="Future phase-3 rename planning only.",
            command_name=None,
            implemented=False,
            safe_by_default=False,
            target_repo="PyHuey",
            target_module_or_script=None,
            notes="Deferred: do not rename pygpt_net in this bridge PR.",
        ),
    ]
    if group is None:
        return specs
    return [spec for spec in specs if spec.group == group]


def list_tool_groups() -> list[str]:
    return sorted({spec.group for spec in list_tool_specs()})


def get_tool_spec(tool_id: str) -> HueyToolSpec:
    for spec in list_tool_specs():
        if spec.id == tool_id:
            return spec
    raise KeyError(f"Unknown Huey tool: {tool_id}")


def specs_to_dicts(specs: list[HueyToolSpec]) -> list[dict[str, object]]:
    return [asdict(spec) for spec in specs]


class HueyToolRegistry:
    """Small object wrapper around the static tool specification list."""

    def list_specs(self, group: str | None = None) -> list[HueyToolSpec]:
        return list_tool_specs(group=group)

    def list_groups(self) -> list[str]:
        return list_tool_groups()

    def get_spec(self, tool_id: str) -> HueyToolSpec:
        return get_tool_spec(tool_id)

    def as_dicts(self, group: str | None = None) -> list[dict[str, object]]:
        return specs_to_dicts(self.list_specs(group=group))


__all__ = [
    "HueyToolRegistry",
    "HueyToolSpec",
    "get_tool_spec",
    "list_tool_groups",
    "list_tool_specs",
    "specs_to_dicts",
]
