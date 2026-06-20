"""Safety guardrails shared by GUI and command-center surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SafetyPolicy:
    mock_only: bool = True
    allow_command_execution: bool = False
    allow_memory_mutation: bool = False
    allow_governance_mutation: bool = False
    allow_network_mutation: bool = False
    allow_power_actions: bool = False
    allow_task_execution: bool = False


DANGEROUS_ACTIONS = {
    "shutdown",
    "reboot",
    "network_change",
    "memory_mutation",
    "governance_emergency",
    "task_execution",
    "shell_command",
}

_ACTION_TO_POLICY = {
    "shutdown": "allow_power_actions",
    "reboot": "allow_power_actions",
    "network_change": "allow_network_mutation",
    "memory_mutation": "allow_memory_mutation",
    "governance_emergency": "allow_governance_mutation",
    "task_execution": "allow_task_execution",
    "shell_command": "allow_command_execution",
}


def default_safety_policy() -> SafetyPolicy:
    """Return the default safe/mock-only GUI policy."""

    return SafetyPolicy()


def is_dangerous_action(action: str) -> bool:
    """Return ``True`` when the action is dangerous in operator GUI context."""

    return action.strip().lower() in DANGEROUS_ACTIONS


def assert_action_allowed(action: str, policy: SafetyPolicy | None = None) -> None:
    """Raise ``PermissionError`` if a GUI action is not allowed."""

    normalised = action.strip().lower()
    if not is_dangerous_action(normalised):
        return

    selected = policy or default_safety_policy()
    flag_name = _ACTION_TO_POLICY.get(normalised)
    if flag_name is None:
        raise PermissionError(f"Action '{action}' is blocked by GUI safety policy")
    if not getattr(selected, flag_name):
        raise PermissionError(f"Action '{action}' is disabled in safe GUI mode")


def safety_banner() -> dict[str, str | bool]:
    """Return a JSON-safe safety status banner."""

    policy = default_safety_policy()
    banner = asdict(policy)
    banner["summary"] = (
        "Read-only safe mode: no command, task, memory, or power mutation."
    )
    return banner


__all__ = [
    "DANGEROUS_ACTIONS",
    "SafetyPolicy",
    "assert_action_allowed",
    "default_safety_policy",
    "is_dangerous_action",
    "safety_banner",
]
