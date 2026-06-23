# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Python Compatibility module (tests)

"""Guards around Python version compatibility markers for key dependencies."""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement


def _get_requirement_line(package_name: str, *, group: str = "ml") -> str:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["optional-dependencies"][group]
    for line in dependencies:
        requirement = Requirement(line)
        if requirement.name == package_name:
            return line
    raise AssertionError(f"Requirement for {package_name!r} not found")


def _marker_allows(line: str, python_version: str) -> bool:
    req = Requirement(line)
    if req.marker is None:
        return True
    return req.marker.evaluate({"python_version": python_version})


def test_pygpt_marker_allows_python_313() -> None:
    line = _get_requirement_line("pygpt-net")
    assert _marker_allows(line, "3.13")


def test_audio_bridge_allows_python_313() -> None:
    line = _get_requirement_line("audioop-lts")
    assert _marker_allows(line, "3.13")


def test_aifc_bridge_allows_python_313() -> None:
    line = _get_requirement_line("standard-aifc")
    assert _marker_allows(line, "3.13")


def test_audio_bridge_blocks_python_314() -> None:
    line = _get_requirement_line("audioop-lts")
    assert not _marker_allows(line, "3.14")


def test_aifc_bridge_blocks_python_314() -> None:
    line = _get_requirement_line("standard-aifc")
    assert not _marker_allows(line, "3.14")
