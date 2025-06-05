# tests/test_utils.py

import unittest
from huey.utils import calculate_sum, validate_input
from huey.exceptions import InvalidInputError


class TestUtils(unittest.TestCase):
    def test_calculate_sum(self):
        self.assertEqual(calculate_sum(2, 3), 5)
        self.assertEqual(calculate_sum(-1, 1), 0)

    def test_validate_input(self):
        self.assertTrue(validate_input(5, int))
        with self.assertRaises(InvalidInputError):
            validate_input("five", int)


if __name__ == "__main__":
    unittest.main()
