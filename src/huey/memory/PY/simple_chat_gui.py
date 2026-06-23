"""Compatibility wrapper for the canonical simple chat GUI."""

from huey.simple_chat_gui import get_answer, run_simple_chat

__all__ = ["get_answer", "run_simple_chat"]


if __name__ == "__main__":
    run_simple_chat()
