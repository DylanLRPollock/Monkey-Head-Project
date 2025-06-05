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
