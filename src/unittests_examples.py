import io
import random
import statistics
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
                           :2(?BM:MF$F+B""")

        a, b = 0, 1

        for i in range(10):
            self.run_test((iterative, i), a)
            self.run_test((recursive, i), a)
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

        self.run_test('`e2RFL5%zR"zzuB"L3%zR"zziF"lQlRoaoC|LN|;', o)

    def test_2spooky(self):
        for i in range(10):
            self.run_test(('I:n"emykoops"6Ro{2+nH', i), "{}spooky{}me".format(i, i+2))

    def test_cat(self):
        self.run_test(("iE;o", "Hello,\0World!"), "Hello,\0World!")

    def test_fen_string(self):
        code = '"QRBNP"133595F{2K3pSl&m*&3p|TiEh3g+t'

        self.run_test((code, "5k2/ppp5/4P3/3R3p/6P1/1K2Nr2/PP3P2/8"), 4)
        self.run_test((code, "QQn"), 15)    
    
    def test_small_caps(self):
        code = dedent("""\
                      iE;:Sl:@Su=zQ`a-1g|o
                      ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ""")

        self.run_test((code, "Hello, World!"), "ʜᴇʟʟᴏ, ᴡᴏʀʟᴅ!")

    def test_counting_sort(self):
        code = dedent("""\
                      iEv:2gP$2p
                      rH>ff*FL2gRL|""")

        self.run_test((code, "Hello, World!"), " !,HWdellloor")

    def test_dropsort(self):
        code1 = dedent("""\
                       I:N\!
                       ;EI/!~q)K2""")
        code2 = "I:NTIE;2K)q~t!"

        for code in [code1, code2]:
            self.run_test((code, "-7 -8 -5 0 -1 1 1 -5"), "-7\n-5\n0\n1\n1\n")
            self.run_test((code, "9 8 7 6 5"), "9\n")
            self.run_test((code, "1 2 5 4 3 7"), "1\n2\n5\n7\n")
            self.run_test((code, "10 10 10 9 10"), "10\n10\n10\n10\n")

    @unittest.skip("Float tolerance")
    def test_stdev(self):
        L = [random.random()*100 for _ in range(100)]
        
        self.run_test(("IE!tlS]l&lR+&,[jlF-:*}|l&lR+&,12,Xh", L),
                      statistics.pstdev(L))

    def test_jarvis(self):
        code = "I:Nw:9)WWaSD$|PlMF$:q*C+P|:N|;"
        self.run_test((code, "77"), "77\n49\n36\n18\n8\n")
        self.run_test((code, "806"), "806\n54\n20\n3\n")

    def test_plus1_primes(self):
        for a, b in [[4, 0], [1, 1], [17, 2], [33, 3], [553, 4], [3273, 5],
                     [4145, 6], [4109, 7], [196869, 8]]:
            self.run_test(("IW2SD$|l+1]FylS]LR}1lL-R}lMF2*+|:1gq~C::1pSP1]+y|uh", a), b)

    def test_invert_binary(self):
        self.run_test(("iE;1S^o", "10101110101010010100010001010110101001010"),
                      "01010001010101101011101110101001010110101")

    def test_longest_common_prefix(self):
        pass

    def vote_simulator(self):
        code = "iEh`^=:@)+M"
        self.run_test((code, ""), 0)
        self.run_test((code, "^vvv^^vv^vv^v^"), 1)
        self.run_test((code, "^vvv^^vv^vv^v^^"), 0)
        self.run_test((code, "^vvv^^vv^vv^v^^^"), 1)
        self.run_test((code, "^vvv^^vv^vv^v^^v"), -1)
        self.run_test((code, "^vvv^^vv^vv^v^^vv"), 0)
        self.run_test((code, "^vvv^^vv^vv^v^^vvv"), -1)

    def test_prime(self):
        for i in range(30):
            self.run_test(("I:2(q0h:3RF:L%zq0h|1h", i), int(is_probably_prime(i)))

    def test_biplex(self):
        code = dedent("""\
                      IEvW2SD$|~rlFLmg+Lmp|
                      |h>3F`dFLmg|u|ylRS>[&lF:q}C~|lMRS<&[jjlF2k=&=&S|}|lMF2*+""")

        for a, b in [[[1], 1], [[2], 2], [[1, 2, 5], 7], [[4294967295], 4294967295],
                     [[2454267026, 2863311530, 3681400539], 3817748707],
                     [[2341103945, 2969112506, 1849078949, 1430639189], 3]]:

            self.run_test((code, a), b)

    def test_reverse_and_invert(self):
        self.run_test(("iE;W2SDz$|~rlMF2*+|o", "Hello, World!"), "v,dd\x042>\n\4Xdl\x1e")

if __name__ == '__main__':
    unittest.main()
