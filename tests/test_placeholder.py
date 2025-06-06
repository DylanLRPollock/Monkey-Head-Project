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

ROOT = os.path.dirname(os.path.dirname(__file__))
MODULE_PATH = os.path.join(
    ROOT,
    'repo',
    'pygpt-MHP',
    'src',
    'pygpt_net',
    'controller',
    'config',
    'placeholder.py',
)

sys.path.append(os.path.join(ROOT, 'repo', 'pygpt-MHP', 'src'))

spec = importlib.util.spec_from_file_location('placeholder_module', MODULE_PATH)
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

