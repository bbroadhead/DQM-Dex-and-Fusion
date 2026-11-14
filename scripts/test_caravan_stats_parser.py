#!/usr/bin/env python3
"""Regression checks for the Caravan Heart FAQ stat importer."""
import re
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("import_caravan_stats.py").read_text(encoding="utf-8")
# Extract the exact compiled expression rather than maintaining a second copy.
namespace = {"re": re}
line = next(x.strip() for x in SCRIPT.splitlines() if x.strip().startswith("pattern=re.compile("))
exec(line, namespace)
pattern = namespace["pattern"]

class FAQParsingTests(unittest.TestCase):
    def test_normal_monster(self):
        row = "1 1 739 6/492 2/435 3/575 3/575 1/267 14/999 4/557 0 3 Slime"
        match = pattern.match(row)
        self.assertIsNotNone(match)
        self.assertEqual(match.groups()[0:3], ("1", "1", "739"))
        self.assertEqual(match.groups()[-1], "Slime")
        self.assertEqual(len(match.group(4).split()), 6)

    def test_six_star_monster(self):
        row = "6 6 14899 10/999 7/546 18/999 3/119 4/494 14/999 9/752 4 4 Gran Slime"
        match = pattern.match(row)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(8), "Gran Slime")
        self.assertEqual(match.group(5), "9/752")

    def test_special_marker(self):
        row = "6 6 14899 10/999 7/546 18/999 3/119 4/494 14/999 9/752 4 4 *Gran Slime"
        self.assertEqual(pattern.match(row).group(8), "Gran Slime")

    def test_invalid_row(self):
        self.assertIsNone(pattern.match("1 2 3 4/5 Slime"))

if __name__ == "__main__":
    unittest.main()
