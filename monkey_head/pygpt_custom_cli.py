class CustomPyGPT:
    """A minimal PyGPT-like chatbot."""

    def __init__(self):
        from .pygpt_memory import Memory
        self.memory = Memory()

    def generate_reply(self, message: str) -> str:
        """Generate a simple echo reply."""
        return f"Echo: {message}"

    def run_cli(self) -> None:
        """Run an interactive CLI loop."""
        print("Custom PyGPT CLI. Type 'exit' to quit.")
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
