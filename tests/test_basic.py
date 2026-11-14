import unittest

from clock import ClockMapper


class ClockMapperBasicTests(unittest.TestCase):
    def test_exact_anchor(self):
        m = ClockMapper()
        m.add({"track": "audio", "epoch": 1, "tick": 100, "wall_ms": 2000, "numerator": 1, "denominator": 1, "revision": 1})
        self.assertEqual(m.map("audio", 1, 100), 2000)


if __name__ == "__main__":
    unittest.main()
