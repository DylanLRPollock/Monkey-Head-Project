import unittest
from src.pygpt_memory import Memory


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


if __name__ == "__main__":
    unittest.main()
