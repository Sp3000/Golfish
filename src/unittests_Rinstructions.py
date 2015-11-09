import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish
from library import *
from unittests_base import TestGolfish

class TestGolfishRInstructions(TestGolfish):
    def test_Rexclamation(self):
        self.run_test("0R!12345lR+h", 15)
        self.run_test("1R!12345lR+h", 14)
        self.run_test("3R!12345lR+h", 9)
        self.run_test("5R!12345lR+h", 0)
        
    def test_Rquote(self):
        self.run_test("0R'ab'H", "")
        self.run_test("1R'ab'H", "ba")
        self.run_test("5R'ab'H", "bababababa")

        self.run_test('0R"ab"H', "")
        self.run_test('1R"ab"H', "ba")
        self.run_test('5R"ab"H', "bababababa")

if __name__ == '__main__':
    unittest.main()
