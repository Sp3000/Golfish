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

    def test_nesting(self):
        self.run_test(

if __name__ == '__main__':
    unittest.main()
