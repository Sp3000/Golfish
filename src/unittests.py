import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish
from library import *

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

    def test_B(self):
        code = dedent("""\
                      5FLNL2=?BC
                       ;""")

        self.run_test(code, "0\n1\n2\n")

    def test_F(self):
        code = dedent("""\
                      0FLNMC
                       ;""")

        self.run_test(code, "")
    
        code = dedent("""\
                      5FLNMC
                       ;""")

        self.run_test(code, "0\n1\n2\n3\n4\n")

    def test_I(self):
        self.run_test(("IINN;", "5 7"), "7\n5\n")

        code = dedent("""\
                      IEv
                        >nnn;""")

        self.run_test((code, "  5   6     7    "), "765")
        self.run_test(("In;", "sdfbgf567.4566njn43kn"), str(float("567.4566")))

    def test_W(self):
        code = dedent("""\
                      WC
                      ;""")

        self.run_test(code, "")

        code = dedent("""\
                      5W:NMC
                       h""")

        self.run_test(code, "5\n4\n3\n2\n1\n0")

    def test_wrap(self):
        code = dedent("""\
                      <  vn1
                        n\     !2
                        //;
                        3
                      """)
        
        self.run_test(code, "103")

    def test_k(self):
        self.run_test("123450kh", "5")
        self.run_test("123451kh", "4")
        self.run_test("123452kh", "3")
        self.run_test("12345mkh", "1")
        self.run_test("12345akh", "5")
        self.run_test("1234503-kh", "3")
        self.run_test("123450a-kh", "5")

    def test_Rspace(self):
        self.run_test("123R D;", "[1 2]\n")
        self.run_test("120R D;", "[1 2]\n")
        self.run_test("5R 0D;", "[0]\n")

    def test_Rarrow(self):
        self.run_test("123R>D;", "[1 2]\n")

    def test_Rmirror(self):
        self.run_test(dedent("""\
                             0R\\1n;
                               >2n;"""), "1")
        
        self.run_test(dedent("""\
                             4R\\1n;
                               >2n;"""), "1")
        
        self.run_test(dedent("""\
                             5R\\1n;
                               >2n;"""), "2")

        self.run_test(dedent("""\
                             4R/1n;
                               >2n;"""), "1")

        self.run_test(dedent("""\
                             5R/1n;
                               >2n;"""), "2")

    def test_Rexclamation(self):
        self.run_test("120R!3h", "3")
        self.run_test("122R!456h", "6")
        self.run_test("123R!456h", "2")

    def test_Rquestion(self):
        self.run_test(dedent("""\
                             00R?v0n;
                                 >1n;"""), "1")

        self.run_test(dedent("""\
                             01R?v0n;
                                 >1n;"""), "0")

        self.run_test(dedent("""\
                             11R?v0n;
                                 >1n;"""), "1")

        self.run_test(dedent("""\
                             101105R?v0n;
                                     >1n;"""), "0")

        self.run_test(dedent("""\
                             111115R?v0n;
                                     >1n;"""), "1")

    def test_RZ(self):
        self.run_test(dedent("""\
                             00RZv0n;
                                 >1n;"""), "1")

        self.run_test(dedent("""\
                             11RZv0n;
                                 >1n;"""), "0")
        
        self.run_test(dedent("""\
                             01RZv0n;
                                 >1n;"""), "1")

        self.run_test(dedent("""\
                             101105RZv0n;
                                     >1n;"""), "0")

        self.run_test(dedent("""\
                             000005RZv0n;
                                     >1n;"""), "1")


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

    def test_primes2(self):
        code = dedent("""\
                      I:2(q0h\\
                      2W)K2w2/CPh0qz%K
                      h>1""")

        for n in range(30):
            self.run_test((code, str(n)), str(int(is_probably_prime(n))))

    def test_primes3(self):
        code = "I:1)*2T2K=q1h2K%zq0hPt"

        for n in range(30):
            self.run_test((code, str(n)), str(int(is_probably_prime(n))))
        
    def test_sorter(self):
        self.run_test((dedent("""\
                              iEv:2gP$2p
                              Pt>0TVC:2gRC:`}=3Q~rH"""), "Hello, World!"), " !,HWdellloor")

    def test_jarvis(self):
        code = dedent("""\
                      I:N:a(?;T:a(m1J:a%$aS,t
                      1T&lZv :?vP&+t
                      .!00&<t*&<>""")

        self.run_test((code, "77"), "77\n49\n36\n18\n8\n")
        self.run_test((code, "806"), "806\n54\n20\n3\n")

    def test_times_table(self):
        code = dedent("""\
                      fF LfF:L*n` oC
                       ;Coa<""")

        self.run_test(code, '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 \n0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 \n0 2 4 6 8 10 12 14 16 18 20 22 24 26 28 \n0 3 6 9 12 15 18 21 24 27 30 33 36 39 42 \n0 4 8 12 16 20 24 28 32 36 40 44 48 52 56 \n0 5 10 15 20 25 30 35 40 45 50 55 60 65 70 \n0 6 12 18 24 30 36 42 48 54 60 66 72 78 84 \n0 7 14 21 28 35 42 49 56 63 70 77 84 91 98 \n0 8 16 24 32 40 48 56 64 72 80 88 96 104 112 \n0 9 18 27 36 45 54 63 72 81 90 99 108 117 126 \n0 10 20 30 40 50 60 70 80 90 100 110 120 130 140 \n0 11 22 33 44 55 66 77 88 99 110 121 132 143 154 \n0 12 24 36 48 60 72 84 96 108 120 132 144 156 168 \n0 13 26 39 52 65 78 91 104 117 130 143 156 169 182 \n0 14 28 42 56 70 84 98 112 126 140 154 168 182 196 \n')

    def test_fibonacci_recursive(self):
        code = dedent("""\
                      M1AFIFh
                      :3(?vM:MF$F+B
                       B1~<""")

        self.run_test((code, "1"), "1")
        self.run_test((code, "2"), "1")
        self.run_test((code, "3"), "2")
        self.run_test((code, "4"), "3")
        self.run_test((code, "5"), "5")
        self.run_test((code, "13"), "233")

    def test_large_number(self):
        self.run_test("1234567890987654321rTlMZha*$+t", "1234567890987654321")        

    def test_hex(self):
        code = dedent("""\
                      I:?v0h>m1.
                      @S,>:?v~H
                      :%K2s0/@+&~~&k&"W0"&(a""")

        for n in range(50):
            self.run_test((code, str(n)), hex(n)[2:])

    def test_partial(self):
        code = dedent("""\
                      SI
                      C>rFlMF:}+
                      NRl<C}<;""")

        self.run_test((code, "3 | -3, 4, 7, -1, 15"), "-3\n-5\n1\n14\n49\n")

    def test_prime_index_primes(self):
        code = dedent("""\
                      TP:SP?\\
                      SPzq$t\\$P:
                      ?;Pr:N\\@:a1X)""")

        self.run_test(code, "3\n5\n11\n17\n31\n41\n59\n67\n83\n109\n127\n")

    def run_test(self, prog, output):
        if isinstance(prog, str):
            gf = Golfish(prog, online=True)
        else:
            gf = Golfish(*prog, online=True)

        gf.run()
        self.assertEqual(self.output(), output)   

    def output(self):
        val = sys.stdout.getvalue()
        sys.stdout = io.StringIO()
        return val

if __name__ == '__main__':
    unittest.main()
