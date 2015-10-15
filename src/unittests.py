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

    def test_backtick(self):
        self.run_test("`````aH", "a``")

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
        self.run_test("120R D;", "[1 2]\n")

    def test_Rexclamation(self):
        self.run_test("120R!3h", "3")
        self.run_test("122R!456h", "6")
        self.run_test("123R!456h", "2")

    def test_Rquote(self):
        self.run_test("0R'abc'H", "")
        self.run_test("1R'abc'H", "cba")
        self.run_test("5R'abc'H", "cbacbacbacbacba")
        self.run_test('5R"abc"H', "cbacbacbacbacba")

    def test_Rbacktick(self):
        self.run_test("0R`aH", "")
        self.run_test("1R`aH", "a")
        self.run_test("5R`aH", "aaaaa")

    def test_hello_world(self):
        self.run_test('"!dlroW ,olleH"H', "Hello, World!")

    def test_quine(self):
        self.run_test("'r3d*H", "'r3d*H")

    def test_fibonacci(self):
        x, y = 0, 1
        for i in range(20):
            self.run_test(("10IT:zq~hM}:@+{t", str(i)), str(x))
            x, y = y, x+y

    def test_lowercase(self):
        self.run_test("`aT:o:`z=?;Pt", "abcdefghijklmnopqrstuvwxyz")

    def test_collatz(self):
        self.run_test(("IT:NM:Z;P3*:2%qPt6,t", "5"), "5\n16\n8\n4\n2\n1\n")
        self.run_test(("IT:NM:Z;P3*:2%qPt6,t", "7"), "7\n22\n11\n34\n17\n52\n26\n13\n40\n20\n10\n5\n16\n8\n4\n2\n1\n")

    def test_primes(self):
        self.run_test("P:` )?;:SPq:N", "2\n3\n5\n7\n11\n13\n17\n19\n23\n29\n31\n")

    def test_sorter(self):
        self.run_test((dedent("""\
                              iEv:2gP$2p
                              Pt>0T:VC:2gRC:`}=3Q~rH"""), "Hello, World!"), " !,HWdellloor")

    def test_jarvis(self):
        code = dedent("""\
                      I:N:a(?;T:a(m1J:a%$aS,t
                      1T&lZv :?vP&+t
                      .!00&<t*&<>""")

        self.run_test((code, "77"), "77\n49\n36\n18\n8\n")
        self.run_test((code, "806"), "806\n54\n20\n3\n")

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
