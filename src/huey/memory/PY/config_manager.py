# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Config Manager module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return {}
        else:
            return {}

    def save_config(self):
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)

    def get_setting(self, key, default=None):
        return self.config.get(key, default)

    def set_setting(self, key, value):
        self.config[key] = value
        self.save_config()

    def update_settings(self, data: dict) -> None:
        """Update multiple settings at once and persist them."""
        self.config.update(data)
        self.save_config()
