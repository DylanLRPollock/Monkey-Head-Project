"""Volt-4 agent focused on systems and execution discipline."""

from __future__ import annotations

from .base_agent import BaseAgent


class Volt4Agent(BaseAgent):
    name = "Volt-4"
    role = "systems-operator"
    approval_bias = 0.04


__all__ = ["Volt4Agent"]
