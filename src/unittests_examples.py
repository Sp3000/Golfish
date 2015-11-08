import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish
from library import *
from unittests_base import TestGolfish

class TestGolfishExamples(TestGolfish):
    def test_hello_world(self):
        self.run_test('"!dlroW ,olleH"H', "Hello, World!")

    def test_quine(self):
        self.run_test("'r3d*H", "'r3d*H")

    def test_1_to_n(self):
        self.run_test(("IFLPN|;", "5"), "1\n2\n3\n4\n5\n")

    def test_n_to_1(self):
        self.run_test(("IW:NM|;", "5"), "5\n4\n3\n2\n1\n")

    def test_n_to_6(self):
        self.run_test(("Iw:5)W:NM|;", "10"), "10\n9\n8\n7\n6\n")

    def test_double_function(self):
        code = dedent("""\
                      1Ad 5dN 6dN 7dN ;
                      2*B""")

        self.run_test(code, "10\n12\n14\n")

    def test_nth_fib(self):
        iterative = "10IT:zq~hM}:@+{t"
        recursive = dedent("""\
                           1AFIFh
                           :2(?vM:MF$F+B
                            B1~<""")

        a, b = 0, 1

        for i in range(10):
            self.run_test((iterative, str(i)), a)
            self.run_test((recursive, str(i)), b)
            a, b = b, a+b

    def test_factorial(self):
        code_R = "1IRllMR*h"
        code_F = "1IFLP*|h"
        code_A = dedent("""\
                        I1AFFh
                        :1(qPB:MF*B""")
        
        fact = 1

        for i in range(10):
            fact *= i or 1

            for code in [code_R, code_F, code_A]:
                self.run_test((code, str(i)), fact)

    def test_alphabet(self):
        self.run_test("`aT:o:`z=?;Pt", "abcdefghijklmnopqrstuvwxyz")
        self.run_test("asFL`a+o|;", "abcdefghijklmnopqrstuvwxyz")

    def test_collatz(self):
        self.run_test(("IT:NM:Z;P3*:2%qPt6,t", "7"),
                      "7\n22\n11\n34\n17\n52\n26\n13\n40\n20\n10\n5\n16\n8\n4\n2\n1\n")

        self.run_test(("Iw:MW:N3*:2%qPC6,|h", "7"),
                      "7\n22\n11\n34\n17\n52\n26\n13\n40\n20\n10\n5\n16\n8\n4\n2\n1")
    
    def test_primes(self):
        self.run_test("fsFLSPqLN|;", "2\n3\n5\n7\n11\n13\n17\n19\n23\n29\n")

    def test_factorisation(self):
        self.run_test(("I2wmkMW2K%qPC:N:},{|;", "1"), "")
        self.run_test(("I2wmkMW2K%qPC:N:},{|;", "7"), "7\n")
        self.run_test(("I2wmkMW2K%qPC:N:},{|;", "120"), "2\n2\n2\n3\n5\n")

    def test_fizz_buzz(self):
        o = ""
        for i in range(1, 101):
            o += (("Fizz"*(i%3<1) + "Buzz"*(i%5<1)) or str(i)) + '\n'

        self.run_test('`e2RFL3%zQS"Fizz"P|L5%zQS"Buzz"P|Q~aoC|LN|;', o)

if __name__ == '__main__':
    unittest.main()
