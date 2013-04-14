
# test/test_core/parser_test.py

import unittest
import sys

sys.path.append("../")
### sys.path.append("../../")

from spacewar_func import *  # My Spacewar functions

class TestSun(unittest.TestCase):

    def setUp(self):
        testsun = Sun()

    def test_Sun_has_mass_by_default(self):
        self.assertGreater(testsun.mass, 0)

if __name__ == "__main__":
    unittest.main()
