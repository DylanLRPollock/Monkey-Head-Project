import unittest
from src.gencore import generate_core_data


class TestGencore(unittest.TestCase):
    def test_generate_core_data(self):
        data = {"a": 1, "b": 2}
        result = generate_core_data(data)
        self.assertTrue(result["processed"])
        self.assertEqual(result["input_length"], 2)
        self.assertEqual(result["details"], data)


if __name__ == "__main__":
    unittest.main()
