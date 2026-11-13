"""Smoke guard for the checked-in kernel/huey-linux/build.yaml.

This is deliberately a *smoke* test, not the full schema/policy validator.
Full schema validation lands in Step 4 (models.py) and Step 33
(test_models.py); risk-gate rejection lands in Step 5 (policy.py) and
Step 34 (test_policy.py). This file's job is to catch accidental drift in
the checked-in YAML: broken syntax, missing top-level sections, weakened
safe defaults, or leaked secrets.

Tests that require PyYAML are marked with pytest.importorskip and will be
skipped when PyYAML is not present in the test environment. PyYAML is added
as a minimal dependency in Step 31 (root pyproject.toml integration).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_YAML = REPO_ROOT / "kernel" / "huey-linux" / "build.yaml"

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "profile",
    "kernel",
    "nvidia",
    "build",
    "paths",
    "signing",
    "safety",
}

# Obvious secret markers we must never see in a checked-in intent file.
_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bGPU-[0-9a-fA-F]{8,}\b"),          # nvidia-smi GPU UUIDs
    re.compile(r"\bMIG-[0-9a-fA-F]{8,}\b"),          # MIG UUIDs
]

_FORBIDDEN_VALUES = {"runfile", "autoinstall"}


def _read_text() -> str:
    assert BUILD_YAML.exists(), f"missing build intent file: {BUILD_YAML}"
    text = BUILD_YAML.read_text(encoding="utf-8")
    assert text.strip(), "build.yaml is empty"
    return text


def test_build_yaml_exists_and_is_nonempty() -> None:
    _read_text()


def test_required_top_level_keys_present_stdlib() -> None:
    """Stdlib-only check that all required top-level sections appear."""
    text = _read_text()
    found = set(re.findall(r"^([a-z_][a-z0-9_]*):", text, flags=re.MULTILINE))
    missing = REQUIRED_TOP_LEVEL_KEYS - found
    assert not missing, f"build.yaml missing top-level sections: {sorted(missing)}"


def test_no_obvious_secrets_in_text() -> None:
    """Guard against accidental commit of PEM blocks or GPU UUIDs."""
    text = _read_text()
    for pattern in _SECRET_PATTERNS:
        match = pattern.search(text)
        assert match is None, f"build.yaml appears to contain secret material: {match.group(0)!r}"


def test_parses_and_preserves_safe_defaults() -> None:
    yaml = pytest.importorskip("yaml", reason="PyYAML required; added in Step 31")

    data = yaml.safe_load(_read_text())
    assert isinstance(data, dict), "build.yaml must parse to a mapping"

    # Preserve safe defaults. Relaxing these requires a validated policy change
    # in later steps, not an edit to this file.
    assert data["schema_version"] == 1
    assert data["profile"] == "v100-workstation"

    assert data["nvidia"]["module_flavor"] == "proprietary"
    assert data["nvidia"]["version"] == "580.196.07"

    assert data["build"]["jobs"] == 4

    assert data["safety"]["allow_host_mutation"] is False
    assert data["safety"]["allow_root_build"] is False
    assert data["safety"]["allow_network_fetch"] is False

    assert data["signing"]["required_policy"] in {"required_if_secureboot", "required"}

    # Source and signing paths remain unresolved until an operator pins them.
    assert data["kernel"]["source"] is None
    assert data["kernel"]["version"] is None
    assert data["kernel"]["checksum"] is None
    assert data["nvidia"]["source_path"] is None
    assert data["signing"]["key_path"] is None
    assert data["signing"]["cert_path"] is None


def test_no_runfile_or_autoinstall_fields_or_values() -> None:
    yaml = pytest.importorskip("yaml", reason="PyYAML required; added in Step 31")

    data = yaml.safe_load(_read_text())

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield ("key", key)
                yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)
        else:
            yield ("value", node)

    for kind, node in walk(data):
        if isinstance(node, str):
            assert node.strip().lower() not in _FORBIDDEN_VALUES, (
                f"build.yaml contains forbidden {kind} string: {node!r} "
                "(runfile/autoinstall NVIDIA installers must not be referenced)"
            )
