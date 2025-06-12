from pathlib import Path


class CustomPyGPT:
    """A minimal PyGPT-like chatbot."""

    def __init__(self):
        from .pygpt_memory import Memory
        self.memory = Memory()
        with open(Path(__file__).resolve().parent.parent / "huey" / "main_prompt.txt", "r", encoding="utf-8") as f:
            self.main_prompt = f.read().strip()

    def generate_reply(self, message: str) -> str:
        """Generate a simple echo reply."""
        return f"Echo: {message}"

    def run_cli(self) -> None:
        """Run an interactive CLI loop."""
        print("Custom PyGPT CLI. Type 'exit' to quit.")
        choice = input("Use default 'Main Prompt'? [Y/n]: ").strip().lower()
        if choice and choice not in {"y", "yes"}:
            print("Enter your custom main prompt. Finish with an empty line:")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            if lines:
                self.main_prompt = "\n".join(lines)
        print("\nUsing main prompt:\n" + self.main_prompt + "\n")
        while True:
            try:
                user_input = input("You: ")
            except EOFError:
                break
            if user_input.lower() in {"exit", "quit"}:
                break
            self.memory.add_user_message(user_input)
            reply = self.generate_reply(user_input)
            self.memory.add_assistant_message(reply)
            print(f"Bot: {reply}")

if __name__ == "__main__":
    CustomPyGPT().run_cli()
