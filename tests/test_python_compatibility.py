# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Python Compatibility module (tests)

"""Guards around Python version compatibility markers for key dependencies."""

from __future__ import annotations

from pathlib import Path

from packaging.requirements import Requirement


def _get_requirement_line(package_name: str) -> str:
    for line in Path("requirements.txt").read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.split("==")[0].strip().startswith(package_name):
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
