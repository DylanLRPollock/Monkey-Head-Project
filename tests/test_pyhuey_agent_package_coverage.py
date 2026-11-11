"""Cover PyHuey agent package construction and lifecycle dispatch."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType


def test_agent_initializes_components_and_delegates_lifecycle(monkeypatch):
    calls = []

    class Component:
        def __init__(self, window):
            self.window = window

        def setup(self):
            calls.append(("setup", type(self).__name__))

        def reload(self):
            calls.append(("reload", type(self).__name__))

        def on_stop(self):
            calls.append(("stop", type(self).__name__))

    class Common(Component):
        pass

    class Experts(Component):
        pass

    class Legacy(Component):
        pass

    class Llama(Component):
        pass

    package = "huey.connectors.pyhuey.controller.agent"
    for name, component in (
        ("common", Common),
        ("experts", Experts),
        ("legacy", Legacy),
        ("llama", Llama),
    ):
        stub = ModuleType(f"{package}.{name}")
        setattr(stub, component.__name__, component)
        monkeypatch.setitem(sys.modules, f"{package}.{name}", stub)

    module = importlib.import_module(package)
    window = object()

    agent = module.Agent(window)
    assert all(
        component.window is window
        for component in (agent.common, agent.experts, agent.llama, agent.legacy)
    )

    agent.setup()
    agent.reload()
    agent.stop()

    assert calls == [
        ("setup", "Legacy"),
        ("setup", "Llama"),
        ("reload", "Legacy"),
        ("reload", "Llama"),
        ("stop", "Legacy"),
        ("stop", "Llama"),
    ]
