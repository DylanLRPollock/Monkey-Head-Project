# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Memory module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import unittest

from monkey_head.pygpt_memory import Memory


class TestMemory(unittest.TestCase):
    def test_add_and_get_messages(self):
        mem = Memory()
        mem.add_user_message("hi")
        mem.add_assistant_message("hello")
        history = mem.get_messages()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "hi")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "hello")

    def test_get_returns_copy(self):
        mem = Memory()
        mem.add_user_message("hi")
        history = mem.get_messages()
        history.append({"role": "assistant", "content": "changed"})
        # internal history should not change
        self.assertEqual(len(mem.get_messages()), 1)

    def test_clear(self):
        mem = Memory()
        mem.add_user_message("hi")
        mem.clear()
        self.assertEqual(mem.get_messages(), [])


if __name__ == "__main__":
    unittest.main()
