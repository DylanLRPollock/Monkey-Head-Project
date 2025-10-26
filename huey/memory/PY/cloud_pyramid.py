# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Cloud Pyramid module (huey/memory/PY)

"""Simplified implementation of the Cloud Pyramid governance system."""

from __future__ import annotations

import random
from typing import Iterable


class Council:
    """Generic voting council."""

    def __init__(self, members: Iterable[str]) -> None:
        self.members = list(members)

    def vote(self, proposal: str) -> bool:
        """Return True if the majority votes yes."""
        votes = [random.choice([True, False]) for _ in self.members]
        return votes.count(True) >= len(self.members) / 2


class CloudPyramid:
    """Governance structure managing system decisions."""

    def __init__(self) -> None:
        self.pinnacle = Council(["pinnacle"])
        self.executive = Council([f"exec{i}" for i in range(3)])
        self.senate = Council([f"sen{i}" for i in range(5)])
        self.parliament = Council([f"mp{i}" for i in range(10)])
        self.populace = Council([f"cit{i}" for i in range(100)])
        self.supreme_court = Council([f"judge{i}" for i in range(3)])

    def decide(self, proposal: str) -> bool:
        """Make a decision using the pyramid hierarchy."""
        if not self.populace.vote(proposal):
            return False
        if not self.parliament.vote(proposal):
            return False
        if not self.senate.vote(proposal):
            return False
        if not self.executive.vote(proposal):
            return False
        if not self.supreme_court.vote(proposal):
            return False
        return self.pinnacle.vote(proposal)
