# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Pygpt Memory module (huey)

"""Simplified conversation memory helpers for Monkey Head's PyGPT integration."""

from __future__ import annotations


class Memory:
    """A minimal conversation buffer compatible with the legacy PyGPT tooling."""

    def __init__(self) -> None:
        self._messages: list[dict[str, str]] = []

    def add_user_message(self, content: str) -> None:
        """Store a user-authored message in the conversation history."""

        self._messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Store an assistant-authored message in the conversation history."""

        self._messages.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict[str, str]]:
        """Return a shallow copy of the stored conversation history."""

        return list(self._messages)

    def clear(self) -> None:
        """Remove all stored conversation history."""

        self._messages.clear()
