import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish

class TestGolfish(unittest.TestCase):
    def setUp(self):
        sys.stdout = io.StringIO()

    def test_arithmetic(self):
        gf = Golfish("12+n;").run()
        self.assertEqual(self.output(), "3")

        gf = Golfish("34+5*n;").run()
        self.assertEqual(self.output(), "35")

        gf = Golfish("42,7-n;").run()
        self.assertEqual(self.output(), "-5")

        gf = Golfish("67*5%7+9*n;").run()
        self.assertEqual(self.output(), "81")

    def test_push_num(self):
        for i, c in enumerate("m0123456789abcdef", start=-1):
            gf = Golfish(c + "n;").run()
            self.assertEqual(self.output(), str(i))

    def test_push_string(self):
        gf = Golfish("'abcdef'rH").run()
        self.assertEqual(self.output(), "abcdef")
        gf = Golfish('"abcdef"rH').run()
        self.assertEqual(self.output(), "abcdef")

        gf = Golfish("'ab`n`rdef'rH").run()
        self.assertEqual(self.output(), "ab\n\rdef")
        gf = Golfish('"ab`n`rdef"rH').run()
        self.assertEqual(self.output(), "ab\n\rdef")

        gf = Golfish("""'`''"`""rH""").run()
        self.assertEqual(self.output(), "'\"")

        gf = Golfish("'````a'rH").run()
        self.assertEqual(self.output(), "``a")

    def output(self):
        val = sys.stdout.getvalue()
        sys.stdout = io.StringIO()
        return val

if __name__ == '__main__':
    unittest.main()
