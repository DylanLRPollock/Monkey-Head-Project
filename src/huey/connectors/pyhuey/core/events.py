"""Minimal event constants for repository-local plugin tests."""

from __future__ import annotations

from dataclasses import dataclass, field


class Event:
    CMD_SYNTAX = "cmd.syntax"
    CMD_INLINE = "cmd.inline"
    CMD_EXECUTE = "cmd.execute"
    ENABLE = "plugin.enable"
    DISABLE = "plugin.disable"
    FORCE_STOP = "plugin.force_stop"
    PLUGIN_SETTINGS_CHANGED = "plugin.settings_changed"
    CTX_BEFORE = "ctx.before"
    CTX_AFTER = "ctx.after"
    CTX_END = "ctx.end"
    USER_SEND = "user.send"
    SYSTEM_PROMPT = "system.prompt"
    INPUT_BEFORE = "input.before"


@dataclass(slots=True)
class KernelEvent:
    name: str
    data: dict[str, object] = field(default_factory=dict)
    ctx: object | None = None


__all__ = ["Event", "KernelEvent"]
