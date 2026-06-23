"""Prompt generation helpers for known Monkey-Head-Project tasks."""

from __future__ import annotations


def media_manager_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Implement or refine the FFmpeg-safe media manager in {target_repo}. "
        "Keep imports lightweight, preserve safe subprocess execution, and return "
        "JSON-safe metadata for probe and transform operations."
    )


def ffmpeg_validator_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Improve FFmpeg environment validation in {target_repo}. "
        "Report ffmpeg/ffprobe availability, version details, and clear readiness "
        "status without mutating the system."
    )


def speech_pipeline_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Extend the speech preprocessing pipeline in {target_repo}. "
        "Keep the path non-destructive, rely on the shared media manager, and emit "
        "deterministic manifests for transcription-ready outputs."
    )


def video_pipeline_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Expand the structured video pipeline in {target_repo}. "
        "Reuse the central media manager, surface JSON-safe preview and metadata "
        "objects, and avoid reimplementing raw ffprobe logic."
    )


def command_center_backend_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Add read-only backend support for Command Center in {target_repo}. "
        "Preserve the existing contract, expose status/telemetry safely, and avoid "
        "introducing write-side control flows."
    )


def gui_unification_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Plan a GUI unification pass in {target_repo}. "
        "Connect new UI adapters to the existing GUI and Command Center surfaces "
        "instead of creating parallel frontends."
    )


def dependency_security_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Review dependency and script-surface safety for {target_repo}. "
        "Prefer fixed commands, no shell=True, explicit path validation, and "
        "report-only defaults for any sensitive capability."
    )


def pyhuey_plugin_bridge_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Build a safe PyHuey plugin bridge for {target_repo}. "
        "Expose status, FFmpeg validation, audio preparation, media probing, and "
        "task prompt generation while blocking hardware, governance, and repo mutations."
    )


def phase_2_5_connector_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        f"Plan the phase 2.5 PyHuey connector work for {target_repo}. "
        "Focus on bridge ergonomics and media workflows only; do not rename the "
        "PyHuey package from pygpt_net in this phase."
    )


def phase_3_pyhuey_rename_prompt(target_repo: str = "Monkey-Head-Project") -> str:
    return (
        "Plan a future phase 3 rename of the PyHuey package from pygpt_net to pyhuey "
        "within the PyHuey codebase only. Do not instruct changes to "
        f"{target_repo} for this rename task."
    )


_PROMPTS = {
    "media_manager": media_manager_prompt,
    "ffmpeg_validator": ffmpeg_validator_prompt,
    "speech_pipeline": speech_pipeline_prompt,
    "video_pipeline": video_pipeline_prompt,
    "command_center_backend": command_center_backend_prompt,
    "gui_unification": gui_unification_prompt,
    "dependency_security": dependency_security_prompt,
    "pyhuey_plugin_bridge": pyhuey_plugin_bridge_prompt,
    "phase_2_5_connector": phase_2_5_connector_prompt,
    "phase_3_pyhuey_rename": phase_3_pyhuey_rename_prompt,
}


def generate_task_prompt(
    task_id: str, target_repo: str = "Monkey-Head-Project"
) -> str:
    try:
        builder = _PROMPTS[task_id]
    except KeyError as exc:
        raise ValueError(f"Unknown Huey task id: {task_id}") from exc
    return builder(target_repo=target_repo)


__all__ = [
    "command_center_backend_prompt",
    "dependency_security_prompt",
    "ffmpeg_validator_prompt",
    "generate_task_prompt",
    "gui_unification_prompt",
    "media_manager_prompt",
    "phase_2_5_connector_prompt",
    "phase_3_pyhuey_rename_prompt",
    "pyhuey_plugin_bridge_prompt",
    "speech_pipeline_prompt",
    "video_pipeline_prompt",
]
