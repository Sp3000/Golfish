import io
import sys
import unittest

from golfish import Golfish
from library import *

class TestGolfish(unittest.TestCase):
    def setUp(self):
        sys.stdout = io.StringIO()
        self.lib = Library()

    def run_test(self, prog, output):
        if isinstance(prog, str):
            gf = Golfish(prog, online=True, debug=True, tick_limit=10000)
        else:
            gf = Golfish(prog[0], str(prog[1]), online=True,
                         debug=True, tick_limit=10000)

        gf.run()
        self.assertEqual(self.output(), str(output))

    def output(self):
        val = sys.stdout.getvalue()
        sys.stdout = io.StringIO()
        return val

    def num_to_str(self, n):
        assert n in range(-1, 16)
        return "m0123456789abcdef"[n+1]
