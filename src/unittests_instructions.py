import io
import sys
from textwrap import dedent
import unittest

from golfish import Golfish
from library import *
from unittests_base import TestGolfish

class TestGolfishInstructions(TestGolfish):
    def test_space(self):
        self.run_test("   ;", "")

    def test_exclamation(self):
        self.run_test("1!2h", "1")

    def test_quote(self):
        self.run_test("'Hello'H", "olleH")
        self.run_test("'`He`nl`\"l`ro`''H", "'o\rl\"`l\neH`")

        self.run_test('"Hello"H', "olleH")
        self.run_test('"`He`nl`\'l`ro`""H', '"o\rl\'`l\neH`')

    def test_hash(self):
        self.run_test("1#hl", "2")
        self.run_test("#h1", "1")
        self.run_test("<#h!", "0")

        code = dedent("""\
                      v h1/;
                      !   !
                      /   /
                      #   #""")

        self.run_test(code, "1")

    def test_dollar(self):
        self.run_test("12345$D;", "[1 2 3 5 4]\n")

    def test_ampersand(self):
        self.run_test("D1D&D&D;", "[]\n[1]\n[]\n[1]\n")

    def test_comparison(self):
        for a, b in [[2, 5], [6, 6], [-1, 1]]:            
            for inst, command in [['(', '<'], [')', '>'], ['=', '==']]:
                sa, sb = map(self.num_to_str, [a, b])
                self.run_test("{}{}{}h".format(sa, sb, inst),
                              int(eval("{}{}{}".format(a, command, b))))

    def test_arithmetic(self):
        for a, b in [[5, 2], [5, 3], [9, 5], [1, 1], [0, 7], [15, 3]]:
            for inst, command in [['+', '+'], ['-', '-'], ['*', '*'],
                                  [',', '/'], ['%', '%']]:

                sa, sb = map(self.num_to_str, [a, b])
                expected = eval("{}{}{}".format(a, command, b))

                if expected == int(expected):
                    expected = int(expected)

                self.run_test("{}{}{}h".format(sa, sb, inst), expected)

    def test_push_num(self):
        for n, c in enumerate("m0123456789abcdef", start=-1):
            self.run_test(c + "h", n)

    def test_colon(self):
        self.run_test("5:D;", "[5 5]\n")
        self.run_test("a:D;", "[10 10]\n")
        self.run_test(":D;", "[0 0]\n")

    def test_semicolon(self):
        self.run_test(";", "")

    def test_question(self):
        self.run_test("3m?4D;", "[3 4]\n")
        self.run_test("30?4D;", "[3]\n")
        self.run_test("31?4D;", "[3 4]\n")
        self.run_test("3a?4D;", "[3 4]\n")

    def test_at(self):
        self.run_test("12345@D;", "[1 2 4 5 3]\n")
        self.run_test("12@D;", "[1 2 0]\n")
        self.run_test("@D;", "[0 0 0]\n")

    def test_A(self):
        code = dedent("""\
                      1AF 5FN 6FN 7FN ;
                      2*B""")
        
        self.run_test(code, "10\n12\n14\n")

    def test_B(self):
        self.run_test("5FL:3=?B|D;", "[0 1 2 3]\n")
        self.run_test("5W:M:3=?B|D;", "[5 4 3]\n")

    def test_C(self):
        pass

    def test_D(self):
        self.run_test("D;", "[]\n")
        self.run_test("D0D1D2D~D;", "[]\n[0]\n[0 1]\n[0 1 2]\n[0 1]\n")
        self.run_test("0?D2D;", "[2]\n")
        self.run_test("1?D2D;", "[]\n[2]\n")

    def test_E(self):
        self.run_test(("iEH", "Hello, World!"), "!dlroW ,olleH")

    def test_F(self):
        self.run_test("0F1N|;", "")
        self.run_test("1F1N|;", "1\n")
        self.run_test("5F1N|;", "1\n1\n1\n1\n1\n")

    def test_G(self):
        pass

    def test_H(self):
        self.run_test("'Hi'aH", "\niH")
        self.run_test("H", "")

    def test_I(self):
        self.run_test(("IIIID;", "5 6 7 8 9"), "[5 6 7 8]\n")
        self.run_test(("IIIID;", "5\nabc6def7"), "[5 6 7 -1]\n")
        self.run_test(("ID;", "-5.67-6-9"), "[{}]\n".format(-5.67))
        self.run_test(("IID;", "-5.67-6-9"), "[{} -6]\n".format(-5.67))
        self.run_test(("ID;","-.6.5"), "[{}]\n".format(-.6))
        self.run_test(("IID;","-.6.5"), "[{} {}]\n".format(-.6, .5))

    def test_J(self):
        pass

    def test_K(self):
        self.run_test("12345 2K D;", "[1 2 3 4 5 4 5]\n")
        self.run_test("12345 7K D;", "[0 0 1 2 3 4 5 0 0 1 2 3 4 5]\n")

    def test_L(self):
        pass

    def test_M(self):
        self.run_test("Mh", "-1")
        self.run_test("5Mh", "4")

    def test_N(self):
        self.run_test("N;", "0\n")
        self.run_test("ff*N;", "225\n")
        self.run_test("12,N;", str(0.5) + '\n')
        self.run_test("42,N;", "2\n")

    def test_O(self):
        pass

    def test_P(self):
        self.run_test("Ph", "1")
        self.run_test("5Ph", "6")

    def test_Q(self):
        self.run_test("1Q'Hi'oo|;", "iH")
        self.run_test("0Q'Hi'oo|;", "")
        self.run_test("35,Q'Hi'oo|;", "iH")
        self.run_test("1Q|;", "")
        self.run_test("0Q|;", "")
        self.run_test("1Q 2n 1Q 3n 0Q 4n | 5n | 6n 1Q 7n | 8n |;", "235678")

    def test_R(self):
        pass

    def test_S(self):
        pass

    def test_Tt(self):
        pass

    def test_U(self):
        pass

    def test_V(self):
        self.run_test("5VXDXXXD;", "[5]\n[5 5 5 5]\n")
        self.run_test("VVVVVD;", "[0 0 0 0]\n")

    def test_W(self):
        pass

    def test_X(self):
        self.run_test("00Xh", 0**0)
        self.run_test("50Xh", 5**0)
        self.run_test("5fXh", 5**15)
        self.run_test("312,Xh", 3**.5)

    def test_Y(self):
        pass

    def test_Z(self):
        self.run_test("10Zh~h", "1")
        self.run_test("11Zh~h", "0")

    def test_square_brackets(self):
        self.run_test("12345D 3]D ++[D;", "[1 2 3 4 5]\n[3 4 5]\n[1 2 12]\n")

    def test_backtick(self):
        self.run_test("`'``a`a`b`HH", "Hba\n`'")

    def test_g(self):
        self.run_test("00go01gn20go;", "00g")

    def test_h(self):
        self.run_test("12345h", "5")

    def test_i(self):
        self.run_test(("ioioioio;", "Hello"), "Hell")
        self.run_test(("ioioioin;", "Hel"), "Hel-1")
        self.run_test("in;", "-1")

    def test_j(self):
        pass

    def test_k(self):
        pass

    def test_l(self):
        self.run_test("lDlDlD;", "[0]\n[0 1]\n[0 1 2]\n")

    def test_m(self):
        pass # See push_num

    def test_n(self):
        self.run_test("5n;", 5)
        self.run_test("12,n;", 1/2)
        self.run_test("37,n;", 3/7)
        self.run_test("42,n;", 2)

    def test_o(self):
        self.run_test("48*o;", " ")

    def test_p(self):
        code = dedent("""\
                      `v50p
                           >fh""")
        
        self.run_test(code, "15")

    def test_q(self):
        pass

    def test_r(self):
        self.run_test("12345rD;", "[5 4 3 2 1]\n")

    def test_s(self):
        self.run_test("fsh", 31)
        self.run_test("5" + "s"*10 + "h", 5 + 10*16)

    def test_t(self):
        pass # See Tt

    def test_uy(self):
        self.run_test("12345D yD uD;", "[1 2 3 4 5]\n[]\n[1 2 3 4 5]\n")

    def test_w(self):
        pass

    def test_x(self):
        pass

    def test_y(self):
        pass # See uy

    def test_z(self):
        self.run_test("5DzDzD;", "[5]\n[0]\n[1]\n")

    def test_brace(self):
        self.run_test("1234D{D{D}D}D;", "[1 2 3 4]\n[2 3 4 1]\n[3 4 1 2]"
                                        "\n[2 3 4 1]\n[1 2 3 4]\n")

    def test_tilde(self):
        self.run_test("1234D~D~D~D;", "[1 2 3 4]\n[1 2 3]\n[1 2]\n[1]\n")
        
if __name__ == '__main__':
    unittest.main()
