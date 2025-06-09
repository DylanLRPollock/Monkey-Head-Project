# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from .logger import get_logger
from .config_manager import ConfigManager
from .file_manager import FileManager

logger = get_logger(__name__)


class CLI:
    def __init__(self):
        self.config_manager = ConfigManager("config.json")
        self.file_manager = FileManager()

    def run(self):
        while True:
            command = input("Enter command (type 'exit' to quit): ")
            if command == "exit":
                logger.info("Exiting CLI")
                break
            elif command.startswith("set "):
                _, key, value = command.split()
                self.config_manager.set_setting(key, value)
                logger.info(f"Set {key} to {value}")
            elif command.startswith("get "):
                _, key = command.split()
                value = self.config_manager.get_setting(key)
                print(value)
                logger.info(f"Retrieved setting {key}: {value}")
            else:
                print("Unknown command")
                logger.warning(f"Unknown command: {command}")


if __name__ == "__main__":
    CLI().run()
