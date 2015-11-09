import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish
from library import *
from unittests_base import TestGolfish

class TestGolfishCore(TestGolfish):
    def test_wrap(self):
        code = dedent("""\
                      <  vn1
                        n\     !2
                        //;
                        3
                      """)
        
        self.run_test(code, "103")

    def test_bottomless_stack(self):
        self.run_test(":D;", "[0 0]\n")
        self.run_test("@D;", "[0 0 0]\n")

    def test_get_space(self):
        code = dedent("""\
                      01go11go21go31go;
                      a b""")
                      
        self.run_test(code, "a b\0")

    def test_eof(self):
        self.run_test(("INE;IN;", "5"), "5\n-1\n")
        self.run_test(("INE;IN;", "5 "), "5\n-1\n")
        self.run_test(("INE;IN;", "5 6"), "5\n6\n")

    def test_switched_block(self):
        self.run_test("0Q56S||h", "0")

    def test_var_block(self):
        self.run_test("5V'0Q'|h'|3h", "5")

    def test_alias_block(self):
        self.run_test("5A'0Q'|h'|5h", "0")

    def test_QL(self):
        self.run_test("5F1QL||D;", "[0 1 2 3 4]\n")

if __name__ == '__main__':
    unittest.main()
