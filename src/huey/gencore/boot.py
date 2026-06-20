"""Boot sequence coordination for the GenCore kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from huey.exceptions import KernelBootError

BootCheck = Callable[[], bool]


@dataclass(slots=True)
class BootStage:
    name: str
    description: str
    check: BootCheck
    required: bool = True


class BootSequence:
    """Run ordered boot stages and capture the result."""

    def __init__(self) -> None:
        self._stages: list[BootStage] = []

    def add_stage(
        self,
        name: str,
        description: str,
        check: BootCheck,
        *,
        required: bool = True,
    ) -> BootStage:
        stage = BootStage(name=name, description=description, check=check, required=required)
        self._stages.append(stage)
        return stage

    def run(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for stage in self._stages:
            ready = bool(stage.check())
            payload = {
                "name": stage.name,
                "description": stage.description,
                "required": stage.required,
                "ready": ready,
            }
            results.append(payload)
            if stage.required and not ready:
                raise KernelBootError(f"Boot stage failed: {stage.name}")
        return results

    def describe(self) -> list[dict[str, object]]:
        return [
            {
                "name": stage.name,
                "description": stage.description,
                "required": stage.required,
            }
            for stage in self._stages
        ]


__all__ = ["BootSequence", "BootStage"]
