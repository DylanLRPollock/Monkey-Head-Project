# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
from .config_manager import ConfigManager
from .file_manager import FileManager


class CLI:
    def __init__(self):
        self.config_manager = ConfigManager("config/pygpt_net/config.json")
        self.file_manager = FileManager()

    def choose_provider(self) -> None:
        """Interactively choose an LLM provider."""
        options = ["openai", "google", "deepseek"]
        choice = input(
            "Select provider (openai/google/deepseek): "
        ).strip().lower()
        if choice not in options:
            print("Invalid provider. Available options: openai, google, deepseek")
            return
        self.config_manager.set_setting("agent.llama.provider", choice)
        print(f"Provider set to {choice}")

    def run(self):
        while True:
            command = input("Enter command (type 'exit' to quit): ")
            if command == "exit":
                break
            elif command.startswith("set "):
                _, key, value = command.split()
                self.config_manager.set_setting(key, value)
            elif command.startswith("get "):
                _, key = command.split()
                print(self.config_manager.get_setting(key))
            elif command == "provider":
                self.choose_provider()
            else:
                print("Unknown command")


if __name__ == "__main__":
    CLI().run()
