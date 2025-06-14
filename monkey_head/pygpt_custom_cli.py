from pathlib import Path


class CustomPyGPT:
    """A minimal PyGPT-like chatbot."""

    def __init__(self, prompt_file: str | Path | None = None):
        from .pygpt_memory import Memory

        self.memory = Memory()
        if prompt_file is None:
            prompt_file = (
                Path(__file__).resolve().parent.parent
                / "prompts"
                / "huey_main_prompt.txt"
            )
        self.prompt_file = Path(prompt_file)
        self.main_prompt = self.load_main_prompt()

    def load_main_prompt(self) -> str:
        """Load the default main prompt from ``self.prompt_file``."""
        try:
            return self.prompt_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""

    def generate_reply(self, message: str) -> str:
        """Generate a simple echo reply."""
        return f"Echo: {message}"

    def run_cli(self) -> None:
        """Run an interactive CLI loop."""
        print("Custom PyGPT CLI. Type 'exit' to quit.")
        user_prompt = input(
            f"Enter main prompt or press Enter to use default:\n{self.main_prompt}\n> "
        ).strip()
        if user_prompt:
            self.main_prompt = user_prompt
        print("Chat starting...")
        while True:
            try:
                user_input = input("You: ")
            except EOFError:
                break
            if user_input.lower().strip() == "list pdfs":
                from .pdf_utils import list_available_pdfs

                print("Available PDFs:")
                for pdf in list_available_pdfs():
                    print(f"- {pdf}")
                continue
            if user_input.lower() in {"exit", "quit"}:
                break
            self.memory.add_user_message(user_input)
            reply = self.generate_reply(user_input)
            self.memory.add_assistant_message(reply)
            print(f"Bot: {reply}")


if __name__ == "__main__":
    CustomPyGPT().run_cli()
