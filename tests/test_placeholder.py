# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import unittest
import os
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_SRC = ROOT / "src"
SUBMODULE_SRC = ROOT / "repo" / "pygpt-MHP" / "src"

local_module = LOCAL_SRC / "pygpt_net" / "controller" / "config" / "placeholder.py"
if local_module.exists():
    MODULE_PATH = str(local_module)
    sys.path.append(str(LOCAL_SRC))
else:
    MODULE_PATH = str(
        SUBMODULE_SRC / "pygpt_net" / "controller" / "config" / "placeholder.py"
    )
    sys.path.append(str(SUBMODULE_SRC))

spec = importlib.util.spec_from_file_location("placeholder_module", MODULE_PATH)
placeholder_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(placeholder_module)
Placeholder = placeholder_module.Placeholder
from pygpt_net.item.preset import PresetItem


class DummyWindow:
    def __init__(self, presets):
        class DummyPresets:
            def __init__(self, data):
                self._data = data

            def get_all(self):
                return self._data

        class DummyCore:
            def __init__(self, presets):
                self.presets = DummyPresets(presets)

        self.core = DummyCore(presets)


class TestPlaceholder(unittest.TestCase):
    def test_get_presets_returns_names(self):
        preset = PresetItem()
        preset.name = "Example"
        preset.filename = "example.json"
        presets = {preset.filename: preset}
        placeholder = Placeholder(DummyWindow(presets))
        result = placeholder.get_presets()
        self.assertIn({"_": "---"}, result)
        self.assertIn({"example.json": "Example"}, result)


if __name__ == "__main__":
    unittest.main()
