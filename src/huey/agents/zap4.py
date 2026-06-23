"""Zap-4 agent focused on rapid experimentation."""

from __future__ import annotations

from .base_agent import BaseAgent


class Zap4Agent(BaseAgent):
    name = "Zap-4"
    role = "rapid-prototyper"
    approval_bias = 0.02


__all__ = ["Zap4Agent"]
