"""Cover generated compatibility bridges without optional runtimes."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

BRIDGE_NAMES = ("pdf_chat", "pdf_pre_digestion", "tensorflow_feed")
SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "huey"


@pytest.mark.parametrize("name", BRIDGE_NAMES)
@pytest.mark.parametrize("explicit_exports", [False, True])
def test_compatibility_bridge_exports_and_delegates(
    monkeypatch, name, explicit_exports
):
    bridge_name = f"huey.{name}"
    implementation_name = f"huey.memory.PY.{name}"
    implementation = ModuleType(implementation_name)
    implementation.public_value = f"{name}-value"
    implementation.delegated_value = f"{name}-delegated"
    if explicit_exports:
        implementation.__all__ = ["public_value"]
    monkeypatch.setitem(sys.modules, implementation_name, implementation)

    bridge_path = SOURCE_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(bridge_name, bridge_path)
    assert spec is not None and spec.loader is not None
    bridge = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, bridge_name, bridge)
    spec.loader.exec_module(bridge)

    assert bridge.public_value == f"{name}-value"
    assert bridge.delegated_value == f"{name}-delegated"
    if explicit_exports:
        assert bridge.__all__ == ["public_value"]
    else:
        assert set(bridge.__all__) >= {"public_value", "delegated_value"}
