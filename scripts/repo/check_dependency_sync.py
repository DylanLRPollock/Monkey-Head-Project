#!/usr/bin/env python3
"""Guardrail for obvious dependency drift across pyproject/requirements/constraints.

Checks:
- tracked dependencies declared in pyproject.toml are present in requirements.txt
- conflicting exact pins between tracked pyproject deps and requirements.txt
- conflicting exact pins between constraints.txt and requirements.txt

The tracked set defaults to the supported root requirements surface:
- [project].dependencies
- [project.optional-dependencies].dev

Heavier optional groups remain declared in pyproject extras and are validated
independently when those install surfaces are exercised.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Dict

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name


def parse_requirement_line(line: str) -> Requirement | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith(
        ("-r", "--requirement", "-c", "--constraint", "-e", "--editable")
    ):
        return None
    try:
        return Requirement(stripped)
    except InvalidRequirement:
        return None


def collect_requirements(requirement_strings: list[str]) -> Dict[str, Requirement]:
    result: Dict[str, Requirement] = {}
    for req_text in requirement_strings:
        req = parse_requirement_line(req_text)
        if req is None:
            continue
        result[canonicalize_name(req.name)] = req
    return result


def read_requirements_file(path: Path) -> Dict[str, Requirement]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return collect_requirements(lines)


def load_pyproject_direct_requirements(
    path: Path, optional_groups: list[str]
) -> Dict[str, Requirement]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    deps: list[str] = list(project.get("dependencies", []))
    optional = project.get("optional-dependencies", {})
    for group in optional_groups:
        deps.extend(optional.get(group, []))
    return collect_requirements(deps)


def exact_pin(req: Requirement) -> str | None:
    if len(req.specifier) != 1:
        return None
    spec = next(iter(req.specifier))
    if spec.operator != "==":
        return None
    return spec.version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--requirements", default="requirements.txt")
    parser.add_argument("--constraints", default="constraints.txt")
    parser.add_argument(
        "--optional-group",
        dest="optional_groups",
        action="append",
        default=None,
        help="Optional pyproject dependency group to mirror into requirements.txt. Repeatable.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if args.optional_groups is None:
        args.optional_groups = ["dev"]

    pyproject_reqs = load_pyproject_direct_requirements(
        Path(args.pyproject), args.optional_groups
    )
    requirements_reqs = read_requirements_file(Path(args.requirements))
    constraints_reqs = read_requirements_file(Path(args.constraints))

    missing_from_requirements: list[str] = []
    pyproject_req_conflicts: list[str] = []
    constraints_conflicts: list[str] = []

    for name, py_req in sorted(pyproject_reqs.items()):
        req_req = requirements_reqs.get(name)
        if req_req is None:
            missing_from_requirements.append(py_req.name)
            continue
        py_pin = exact_pin(py_req)
        req_pin = exact_pin(req_req)
        if py_pin and req_pin and py_pin != req_pin:
            pyproject_req_conflicts.append(
                f"{py_req.name}: pyproject={py_pin} requirements={req_pin}"
            )

    shared = sorted(set(constraints_reqs).intersection(requirements_reqs))
    for name in shared:
        con_pin = exact_pin(constraints_reqs[name])
        req_pin = exact_pin(requirements_reqs[name])
        if con_pin and req_pin and con_pin != req_pin:
            constraints_conflicts.append(
                f"{constraints_reqs[name].name}: constraints={con_pin} requirements={req_pin}"
            )

    had_issue = False
    if missing_from_requirements:
        had_issue = True
        print("Tracked pyproject dependencies missing from requirements.txt:")
        for dep in missing_from_requirements:
            print(f"  - {dep}")

    if pyproject_req_conflicts:
        had_issue = True
        print(
            "Conflicting exact pins between tracked pyproject deps and requirements.txt:"
        )
        for conflict in pyproject_req_conflicts:
            print(f"  - {conflict}")

    if constraints_conflicts:
        had_issue = True
        print("Conflicting exact pins between constraints.txt and requirements.txt:")
        for conflict in constraints_conflicts:
            print(f"  - {conflict}")

    if had_issue:
        return 1

    print("Dependency sync check passed.")
    return 0


def run_self_test() -> int:
    pyproject_req_map = collect_requirements(
        ["corepkg==1.0.0", "sharedpkg==2.0.0", "optionalpkg==3.0.0"]
    )
    requirements_req_map = collect_requirements(
        ["corepkg==1.0.0", "sharedpkg==2.1.0", "transitive-only==9.9.9"]
    )
    constraints_req_map = collect_requirements(["sharedpkg==2.2.0", "helper==0.1.0"])

    missing = [n for n in pyproject_req_map if n not in requirements_req_map]
    py_conflict = exact_pin(pyproject_req_map["sharedpkg"]) != exact_pin(
        requirements_req_map["sharedpkg"]
    )
    con_conflict = exact_pin(constraints_req_map["sharedpkg"]) != exact_pin(
        requirements_req_map["sharedpkg"]
    )

    assert "optionalpkg" in missing
    assert py_conflict
    assert con_conflict
    print("Self-test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
