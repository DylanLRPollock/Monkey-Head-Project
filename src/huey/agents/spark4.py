"""Spark-4 agent focused on ideation and creative planning."""

from __future__ import annotations

from .base_agent import BaseAgent


class Spark4Agent(BaseAgent):
    name = "Spark-4"
    role = "creative-strategist"
    approval_bias = 0.08


__all__ = ["Spark4Agent"]
