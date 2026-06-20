"""Central safety policy for the Huey Tools PyHuey bridge."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class HueyToolSafetyPolicy:
    allow_shell: bool = False
    allow_hardware_control: bool = False
    allow_power_actions: bool = False
    allow_governance_mutation: bool = False
    allow_memory_mutation: bool = False
    allow_network_mutation: bool = False
    allow_file_delete: bool = False
    allow_overwrite: bool = False
    allow_audio_prepare: bool = True
    allow_ffmpeg_validate: bool = True
    allow_status: bool = True
    allow_media_probe: bool = True
    allow_list_tools: bool = True
    allow_generate_prompt: bool = True
    allow_safety_policy: bool = True


def default_safety_policy() -> HueyToolSafetyPolicy:
    return HueyToolSafetyPolicy()


def blocked_actions(
    policy: HueyToolSafetyPolicy | None = None,
) -> list[str]:
    resolved = policy or default_safety_policy()
    blocked = [
        "shell",
        "arbitrary_command",
        "servo_control",
        "motor_control",
        "firmware_flash",
        "git_push",
        "git_commit",
        "repo_write",
    ]
    if not resolved.allow_hardware_control:
        blocked.extend(["hardware_control"])
    if not resolved.allow_power_actions:
        blocked.extend(["power_action"])
    if not resolved.allow_governance_mutation:
        blocked.extend(["governance_mutation"])
    if not resolved.allow_memory_mutation:
        blocked.extend(["memory_mutation"])
    if not resolved.allow_file_delete:
        blocked.extend(["file_delete"])
    if not resolved.allow_network_mutation:
        blocked.extend(["network_mutation"])
    if not resolved.allow_overwrite:
        blocked.extend(["overwrite"])
    return blocked


def is_action_allowed(
    action: str, policy: HueyToolSafetyPolicy | None = None
) -> bool:
    resolved = policy or default_safety_policy()
    if action in {"status"}:
        return resolved.allow_status
    if action in {"ffmpeg_validate"}:
        return resolved.allow_ffmpeg_validate
    if action in {"audio_prepare"}:
        return resolved.allow_audio_prepare
    if action in {"media_probe"}:
        return resolved.allow_media_probe
    if action in {"list_tools"}:
        return resolved.allow_list_tools
    if action in {"generate_prompt"}:
        return resolved.allow_generate_prompt
    if action in {"safety_policy"}:
        return resolved.allow_safety_policy
    return action not in blocked_actions(resolved)


def assert_action_allowed(
    action: str, policy: HueyToolSafetyPolicy | None = None
) -> None:
    if not is_action_allowed(action, policy):
        raise PermissionError(f"Action blocked by safety policy: {action}")


def policy_to_dict(
    policy: HueyToolSafetyPolicy | None = None,
) -> dict[str, object]:
    resolved = policy or default_safety_policy()
    payload = asdict(resolved)
    payload["blocked_actions"] = blocked_actions(resolved)
    return payload


__all__ = [
    "HueyToolSafetyPolicy",
    "assert_action_allowed",
    "blocked_actions",
    "default_safety_policy",
    "is_action_allowed",
    "policy_to_dict",
]
