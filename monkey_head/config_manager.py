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


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as file:
                return json.load(file)
        else:
            return {}

    def save_config(self):
        with open(self.config_path, "w") as file:
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
