import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish

class TestGolfish(unittest.TestCase):
    def setUp(self):
        sys.stdout = io.StringIO()

    def test_arithmetic(self):
        self.run_test("12+n;", "3")
        self.run_test("34+5*n;", "35")
        self.run_test("42,7-n;", "-5")
        self.run_test("67*5%7+9*n;", "81")

    def test_push_num(self):
        for i, c in enumerate("m0123456789abcdef", start=-1):
            self.run_test(c + "n;", str(i))

    def test_push_string(self):
        self.run_test("'abcdef'rH", "abcdef")
        self.run_test('"abcdef"rH', "abcdef")

        self.run_test("'ab`n`rdef'rH", "ab\n\rdef")
        self.run_test('"ab`n`rdef"rH', "ab\n\rdef")

        self.run_test("""'`''"`""rH""", "'\"")
        self.run_test("'````a'rH", "``a")

    def test_debug_jump(self):
        self.run_test("5RDn;", "[]\n00000")
        self.run_test("4!D5nn;", "[4]\n40")

    def test_wrap(self):
        grid = dedent("""\
                      <  vn1
                        n\     !2
                        //;
                        3
                      """)
        
        self.run_test(grid, "103")

    def test_Rspace(self):
        self.run_test("123R D;", "[1 2]\n")

    def test_Rspace(self):
        self.run_test("123R D;", "[1 2]\n")

    def test_Rexclamation(self):
        self.run_test("123R!456h", "2")

    def run_test(self, prog, output):
        if isinstance(prog, str):
            gf = Golfish(prog)
        else:
            gf = Golfish(*prog)

        gf.run()
        self.assertEqual(self.output(), output)        

    def output(self):
        val = sys.stdout.getvalue()
        sys.stdout = io.StringIO()
        return val

if __name__ == '__main__':
    unittest.main()
