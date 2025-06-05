class CLI:
    def __init__(self):
        self.config_manager = ConfigManager("config.json")
        self.file_manager = FileManager()

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
            else:
                print("Unknown command")


if __name__ == "__main__":
    CLI().run()
