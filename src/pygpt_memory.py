# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
class Memory:
    """Simple in-memory store for conversation history."""

    def __init__(self):
        self._messages = []

    def add_user_message(self, content: str) -> None:
        """Store a user message."""
        self._messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Store an assistant message."""
        self._messages.append({"role": "assistant", "content": content})

    def get_messages(self):
        """Return the stored conversation history."""
        return list(self._messages)
