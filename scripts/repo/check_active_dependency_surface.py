#!/usr/bin/env python3
"""Inspect the active dependency surface for obvious drift and duplicates."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def _parse_requirements(path: Path) -> dict[str, Requirement]:
    result: dict[str, Requirement] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(("-c", "-r", "-e")):
            continue
        requirement = Requirement(line)
        result[canonicalize_name(requirement.name)] = requirement
    return result


def _load_pyproject(path: Path) -> dict[str, Requirement]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    dependencies: list[str] = list(data.get("project", {}).get("dependencies", []))
    optional = data.get("project", {}).get("optional-dependencies", {})
    for values in optional.values():
        dependencies.extend(values)
    result: dict[str, Requirement] = {}
    for value in dependencies:
        requirement = Requirement(value)
        result[canonicalize_name(requirement.name)] = requirement
    return result


def main() -> int:
    pyproject = _load_pyproject(Path("pyproject.toml"))
    requirements = _parse_requirements(Path("requirements.txt"))
    constraints = _parse_requirements(Path("constraints.txt"))

    missing_from_requirements = sorted(
        name for name in pyproject if name not in requirements
    )
    missing_from_constraints = sorted(
        name
        for name in pyproject
        if name not in constraints and name not in requirements
    )
    orphan_requirements = sorted(
        name
        for name in requirements
        if name not in pyproject and name not in constraints
    )

    if missing_from_requirements or missing_from_constraints or orphan_requirements:
        if missing_from_requirements:
            print("Direct pyproject dependencies missing from requirements.txt:")
            for name in missing_from_requirements:
                print(f"  - {name}")
        if missing_from_constraints:
            print(
                "Direct pyproject dependencies missing from both requirements and constraints:"
            )
            for name in missing_from_constraints:
                print(f"  - {name}")
        if orphan_requirements:
            print(
                "Requirement pins with no matching direct or constrained declaration:"
            )
            for name in orphan_requirements:
                print(f"  - {name}")
        return 1

    print("Active dependency surface check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
