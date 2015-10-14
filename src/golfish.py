"""
Gol><>, the slightly golfier version of ><>

Requires Python 3 (tested on Python 3.4.2)

Version: 0.3 (updated 12 Oct 2015)
"""

import codecs
from collections import defaultdict
import sys

try:
    from getch import _Getch
    getch = _Getch()
except ImportError:
    # Fail silently, for online interpreter
    pass

from fractions import gcd
from functools import reduce
import math
import operator
import random
import traceback

try:
    from library import *
except ImportError:
    from .library import *

DIGITS = "0123456789abcdef"

DIRECTIONS = {"^": (0, -1),
              ">": (1, 0),
              "v": (0, 1),
              "<": (-1, 0)}

MIRRORS = {"/": lambda x,y: (-y, -x),
           "\\": lambda x,y: (y, x),
           "#": lambda x,y: (-x, -y)}

EOF = -1


class HaltProgram(Exception):
    pass


class InvalidStateException(Exception):
    pass


class Golfish():
    def __init__(self, code="", input_=None, debug=False, online=False):
        rows = code.split("\n")
        self._board = defaultdict(lambda: defaultdict(int))
        x = y = 0

        for char in code:
            if char == "\n":
                y += 1
                x = 0

            else:
                self._board[y][x] = ord(char)
                x += 1

        self._pos = [-1, 0] # [x, y]
        self._dir = DIRECTIONS[">"]

        self._stack_tape = defaultdict(list)
        self._curr_stack = self._stack_tape[0]
        self._stack_num = 0
        self._register_tape = defaultdict(lambda:None)

        self._input_buffer = None

        self._toggled = False # S
        self._skip = 0 # ?! and more

        self._bookmark_pos = [-1, 0] # tT
        self._bookmark_dir = DIRECTIONS[">"]

        self._variable_map = {}

        self._input = input_
        self._debug = debug

        self._online = online

        self._R_repeat = 1

    def run(self):        
        try:
            while True:
                self.tick()

        except HaltProgram:
            pass
        
        except KeyboardInterrupt as e:    
            print("^C", file=sys.stderr)

            if self._debug:
                if self._online:
                    traceback.print_exc(file=sys.stdout)
                else:
                    raise e

        except Exception as e:
            pos = self._pos
            char = self._board[pos[1]][pos[0]]

            # Can't assign file = stdout if online else stderr for some reason
            if self._online:
                print("something smells fishy... ", end="")

                if char in range(32, 127):
                    print("(instruction {} '{}' at {},{})".format(char, "S"*self._toggled + chr(char), pos[0], pos[1]))
                else:
                    print("(instruction {} at {},{})".format(char, pos[0], pos[1]))
                    
            else:
                print("something smells fishy... ", end="", file=sys.stderr)
                
                if char in range(32, 127):
                    print("(instruction {} '{}' at {},{})".format(char, "S"*self._toggled + chr(char), pos[0], pos[1]), file=sys.stderr)
                else:
                    print("(instruction {} at {},{})".format(char, pos[0], pos[1]), file=sys.stderr)       

            if self._debug:
                if self._online:
                    traceback.print_exc(file=sys.stdout)
                else:
                    raise e

    def tick(self):
        self.move()

        if self._pos[1] in self._board and self._pos[0] in self._board[self._pos[1]]:
            self.handle_instruction(self._board[self._pos[1]][self._pos[0]])


    def move(self):
        if any(not isinstance(coord, int) for coord in self._pos):
            raise InvalidStateException

        # Move forward one step
        self._pos[0] += self._dir[0]
        self._pos[1] += self._dir[1]

        # Wrap around
        if self._pos[1] in self._board:
            if self._dir == DIRECTIONS[">"] and self._pos[0] > max(self._board[self._pos[1]].keys()):
                self._pos[0] = 0

            elif self._dir == DIRECTIONS["<"] and self._pos[0] < 0:
                self._pos[0] = max(self._board[self._pos[1]].keys())

        elif self._dir == DIRECTIONS["v"] and self._pos[1] > max(self._board.keys()):
            self._pos[1] = 0
        
        elif self._dir == DIRECTIONS["^"] and self._pos[1] < 0:
            self._pos[1] = max(self._board.keys())


    def handle_instruction(self, char):
        instruction = chr(char)

        if instruction == "S" and not self._toggled:
            self._toggled = True
            return

        if instruction == "D":
            self.output(str(self._curr_stack).replace(",", "") + "\n")
            return

        if self._skip > 0:
            self._skip -= 1
            self._toggled = False
            return

        elif self._skip < 0:
            self._skip = 0

        tmp_R_repeat, self._R_repeat = self._R_repeat, 1
        tmp_pos = self._pos[:]
        
        if self._toggled:
            for _ in range(int(tmp_R_repeat)):
                self._pos = tmp_pos[:]
                self.handle_switched_instruction(instruction)
                
            self._toggled = False

        else:
            for _ in range(int(tmp_R_repeat)):
                self._pos = tmp_pos[:]
                self.handle_normal_instruction(instruction)

    def handle_normal_instruction(self, instruction):
        if instruction in self._variable_map:
            self.push(self._variable_map[instruction])
            return

        if instruction in DIRECTIONS:
            self._dir = DIRECTIONS[instruction]

        elif instruction in MIRRORS:
            self._dir = MIRRORS[instruction](*self._dir)

        elif instruction in DIGITS:
            self.push(DIGITS.index(instruction))

        elif instruction == " ":
            pass

        elif instruction == "!":
            self._skip = 1

        elif instruction in '"\'':
            escaped = False
            parse_char = ord(instruction)
            parse_buffer = []

            self.move()
            char = self._board[self._pos[1]][self._pos[0]]
            
            while escaped or char != parse_char:
                if escaped:
                    escapes = {ord(a): ord(b) for a,b in zip("`nr","`\n\r")}
                    escapes.update({parse_char: parse_char})
                    
                    if char in escapes:
                        parse_buffer.append(escapes[char])

                    else:
                        parse_buffer.append(ord('`'))
                        parse_buffer.append(char)

                    escaped = False

                else:
                    if char == ord('`'):
                        escaped = True
                    else:
                        parse_buffer.append(char)

                self.move()
                char = self._board[self._pos[1]][self._pos[0]]

            self._curr_stack.extend(parse_buffer)

        elif instruction == "$":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem2)
            self.push(elem1)
            
        elif instruction == "%":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 % elem2)

        elif instruction == "&":
            if self._register_tape[self._stack_num] is None:
                self._register_tape[self._stack_num] = self.pop()

            else:
                self.push(self._register_tape[self._stack_num])
                self._register_tape[self._stack_num] = None

        elif instruction == "(":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(1 if elem1 < elem2 else 0)

        elif instruction == ")":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(1 if elem1 > elem2 else 0)

        elif instruction == "*":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 * elem2)

        elif instruction == "+":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 + elem2)

        elif instruction == ",":
            elem2 = self.pop()
            elem1 = self.pop()

            div = elem1 / elem2

            if int(div) == div:
                div = int(div)
                
            self.push(div)

        elif instruction == "-":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 - elem2)

        elif instruction == ".":
            y = self.pop()
            x = self.pop()

            self._pos = [x, y]

        elif instruction == ":":
            elem = self.pop()

            self.push(elem)
            self.push(elem)
            
        elif instruction == ";":
            self.halt()

        elif instruction == "=":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(1 if elem1 == elem2 else 0)

        elif instruction == "?":
            condition = self.pop()

            if not condition:
                self._skip = 1

        elif instruction == "@":
            elem3 = self.pop()
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem2)
            self.push(elem3)
            self.push(elem1)

        elif instruction == "D":
            raise InvalidStateException # Shouldn't reach here

        elif instruction == "E":
            elem = self.pop()

            if elem != EOF:
                self._skip = 1
                self.push(elem)
        
        elif instruction == "H":
            while self._curr_stack:
                elem = self.pop()
                self.output_as_char(elem)

            self.halt()

        elif instruction == "I":
            num = ""
            dots = 0
            char = self.read_char()

            while char >= 0 and chr(char) not in "0123456789.":
                char = self.read_char()

            while char >= 0 and chr(char) in "0123456789.":
                if char == ord(".") and dots > 0:
                    break

                num += chr(char)
                dots += (char == ord("."))
                char = self.read_char()

            self._input_buffer = char

            if num:
                num = float(num)
                self.push(int(num) if num == int(num) else num)

            else:
                self.push(-1)

        elif instruction == "J":
            y = self.pop()
            x = self.pop()
            condition = self.pop()

            if condition:
                self._pos = [x, y]

        elif instruction == "K":
            elem = self.pop()
            popped = [self.pop() for _ in range(elem)][::-1]

            self._curr_stack.extend(popped)
            self._curr_stack.extend(popped)

        elif instruction == "M":
            elem = self.pop()
            self.push(elem - 1)

        elif instruction == "N":
            self.output_as_num(self.pop())
            self.output("\n")

        elif instruction == "P":
            elem = self.pop()
            self.push(elem + 1)

        elif instruction == "Q":
            skip = self.pop()
            cond = self.pop()

            if not cond:
                self._skip = max(0, skip)

        elif instruction == "R":
            elem = self.pop()
            self._R_repeat = elem

        elif instruction == "S":
            raise InvalidStateException # Shouldn't reach here

        elif instruction == "T":
            self._bookmark_pos = self._pos[:]
            self._bookmark_dir = self._dir

        elif instruction == "V":
            self.move()
            char = self._board[self._pos[1]][self._pos[0]]
            self._variable_map[chr(char)] = self.pop()

        elif instruction == "X":
            elem2 = self.pop()
            elem1 = self.pop()
            result = elem1 ** elem2

            if isinstance(result, complex):
                raise InvalidStateException
            
            self.push(result)

        elif instruction == "Z":
            condition = self.pop()

            if condition:
                self._skip = 1

        elif instruction == "`":
            self.move()
            char = self._board[self._pos[1]][self._pos[0]]
            self.push(char)

        elif instruction == "g":
            y = self.pop()
            x = self.pop()

            if y in self._board and x in self._board[y]:
                self.push(self._board[y][x])
            else:
                self.push(0)

        elif instruction == "h":
            self.output_as_num(self.pop())
            self.halt()

        elif instruction == "i":
            self.push(self.read_char())

        elif instruction == "k":
            elem = self.pop()
            self.push(self._curr_stack[~elem])

        elif instruction == "l":
            self.push(len(self._curr_stack))

        elif instruction == "m":
            self.push(-1)

        elif instruction == "n":
            self.output_as_num(self.pop())

        elif instruction == "o":
            self.output_as_char(self.pop())

        elif instruction == "p":
            elem3 = self.pop()
            elem2 = self.pop()
            elem1 = self.pop()

            y = elem3
            x = elem2
            char = elem1
            self._board[y][x] = char                  
                    
        elif instruction == "q":
            cond = self.pop()

            if not cond:
                self._skip = 2

        elif instruction == "r":
            self._curr_stack.reverse()

        elif instruction == "t":
            self._pos = self._bookmark_pos[:]
            self._dir = self._bookmark_dir
                
        elif instruction == "x":
            self._dir = random.choice(list(DIRECTIONS.values()))

        elif instruction == "z":
            elem = self.pop()
            self.push(0 if elem else 1)

        elif instruction in "[]":
            elem = self.pop()
            to_take = []

            for _ in range(int(elem)):
                to_take.append(self.pop())

            self._stack_num += 1 if instruction == "]" else -1
            self._curr_stack = self._stack_tape[self._stack_num]
            self._curr_stack.extend(to_take[::-1])

        elif instruction == "{":
            self.rotate_left()

        elif instruction == "}":
            self.rotate_right()

        elif instruction == "~":
            self.pop()

        else:
            raise NotImplementedError


    def handle_switched_instruction(self, instruction):
        if instruction == "%":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(gcd(elem1, elem2))

        elif instruction == "(":
            elem = self.pop()
            self.push(math.floor(elem))

        elif instruction == ")":
            elem = self.pop()
            self.push(math.ceil(elem))

        elif instruction == ",":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(int(elem1 // elem2))

        elif instruction == "2":
            self.push(math.e)

        elif instruction == "3":
            self.push(math.pi)

        elif instruction == "=":
            elem = self.pop()
            self.push(round(elem))

        elif instruction == "C":
            elem = self.pop()
            self.push(math.cos(elem))

        elif instruction == "I":
            num = ""
            dots = 0
            char = self.read_char()

            while char >= 0 and chr(char) not in "-0123456789.":
                char = self.read_char()

            while char >= 0 and chr(char) in "-0123456789.":
                if char == ord(".") and dots > 0:
                    break

                if char == ord("-") and num:
                    break

                num += chr(char)
                dots += (char == ord("."))
                char = self.read_char()

            self._input_buffer = char

            if num:
                num = float(num)
                self.push(int(num) if num == int(num) else num)

            else:
                self._dir = DIRECTIONS["v"]

        elif instruction == "L":
            elem2 = self.pop()
            elem1 = self.pop()
            self.push(math.log(elem1, elem2))

        elif instruction == "P":
            elem = self.pop()
            self.push(1 if is_probably_prime(elem) else 0)

        elif instruction == "S":
            elem = self.pop()
            self.push(math.sin(elem))

        elif instruction == "T":
            elem = self.pop()
            self.push(math.tan(elem))

        elif instruction == "X":
            self.push(random.random())

        elif instruction == "l":
            elem = chr(self.pop())
            self.push(ord(elem.lower()))

        elif instruction == "u":
            elem = chr(self.pop())
            self.push(ord(elem.upper()))

        else:
            raise NotImplementedError


    def push(self, elem, index=None):
        if index is None:
            self._curr_stack.append(elem)

        else:
            self._curr_stack.insert(index, elem)


    def pop(self, index=None):
        if self._curr_stack:
            if index is None:
                return self._curr_stack.pop()
            else:
                return self._curr_stack.pop(index)

        else:
            return 0


    def rotate_left(self):
        self.push(self.pop(index=0))


    def rotate_right(self):
        self.push(self.pop(), index=0)


    def read_char(self):
        if self._input is None:
            if self._input_buffer is not None:
                char = self._input_buffer
                self._input_buffer = None
                return char

            if sys.stdin.isatty():
                # Console
                char = getch()

                if ord(char) == 3:
                    raise KeyboardInterrupt

            else:
                char = sys.stdin.read(1)

            return ord(char) if char else EOF

        else:
            if self._input:
                c = self._input[0]
                self._input = self._input[1:]
                return ord(c)

            else:
                return EOF


    def output(self, out):
        sys.stdout.write(out)
        sys.stdout.flush()
            

    def output_as_char(self, out):
        if isinstance(out, list):
            for elem in out:
                self.output_as_char(elem)

        else:
            self.output(chr(int(out)))


    def output_as_num(self, out):
        if isinstance(out, list):
            for elem in out:
                self.output_as_num(elem)

        else:
            if int(out) == out:
                out = int(out)
                    
            self.output(str(out))


    def halt(self):
        raise HaltProgram

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Please include a filename")
        exit()
        
    filename = sys.argv[-1]
    debug = (len(sys.argv) > 2 and "-d" in sys.argv[:-1])

    try:
        with open(filename) as infile:
            interpreter = Golfish(infile.read(), debug=debug)

    except UnicodeDecodeError:
        with codecs.open(filename, "r", "utf_8") as infile:
            interpreter = Golfish(infile.read(), debug=debug)

    interpreter.run()
