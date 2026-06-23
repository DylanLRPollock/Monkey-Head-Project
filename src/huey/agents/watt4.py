"""Watt-4 agent focused on efficiency and reliability."""

from __future__ import annotations

from .base_agent import BaseAgent


class Watt4Agent(BaseAgent):
    name = "Watt-4"
    role = "efficiency-guardian"
    approval_bias = -0.02


__all__ = ["Watt4Agent"]
