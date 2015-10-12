"""
Gol><>, the slightly golfier version of ><>

Requires Python 3 (tested on Python 3.4.2)

Version: 0.3 (updated 12 Oct 2015)
"""

import codecs
from collections import defaultdict
import sys
from getch import _Getch

from fractions import gcd
from functools import reduce
import math
import operator
import random

DIGITS = "0123456789abcdef"

DIRECTIONS = {"^": (0, -1),
              ">": (1, 0),
              "v": (0, 1),
              "<": (-1, 0)}

MIRRORS = {"/": lambda x,y: (-y, -x),
           "\\": lambda x,y: (y, x),
           "#": lambda x,y: (-x, -y)}

EOF = -1

getch = _Getch()


class HaltProgram(Exception):
    pass


class InvalidStateException(Exception):
    pass


class Interpreter():
    def __init__(self, code):
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

        self._stack_stack = [[]]
        self._curr_stack = self._stack_stack[-1]
        self._register_stack = [None]

        self._input_buffer = None

        self._toggled = False # S
        self._skip = 0 # ?! and more
        
        self._push_char = False # `

        self._escape = False
        self._array_parse = False
        self._parse_char = None # ' or "
        self._parse_buffer = []

        self._bookmark_pos = [-1, 0] # tT
        self._bookmark_dir = DIRECTIONS[">"]

        self._variable_map = {}
        self._set_variable = False


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

        if self._set_variable == True:
            elem = self.pop()
            self._variable_map[instruction] = deepcopy(elem)
            self.push(elem)
            
            self._set_variable = False
            return

        if instruction in self._variable_map:
            self.push(self._variable_map[instruction])
            return

        if self._array_parse:
            if self._escape:
                escapes = {"`": ord("`"), "n": ord("\n"), "r": ord("\r")}
                escapes.update({self._parse_char: ord(self._parse_char)})
                
                if instruction in escapes:
                    self._parse_buffer.append(escapes[instruction])

                else:
                    self._parse_buffer.append(ord("`"))
                    self._parse_buffer.append(char)

                self._escape = False

            else:
                if instruction == self._parse_char:
                    self._array_parse = False
                    self.push(self._parse_buffer)
                    self._parse_buffer = []

                elif instruction == '`':
                    self._escape = True

                else:
                    self._parse_buffer.append(char)

            return
            
        if self._push_char:
            self.push(char)
            self._push_char = False
            return

        if instruction == "S" and not self._toggled:
            self._toggled = True
            return

        if self._skip > 0:
            self._skip -= 1
            self._toggled = False
            return

        elif self._skip < 0:
            self._skip = 0
        
        if self._toggled:
            self.handle_switched_instruction(instruction)
            self._toggled = False

        else:
            self.handle_normal_instruction(instruction)

    def handle_normal_instruction(self, instruction):
        if instruction in DIRECTIONS:
            self._dir = DIRECTIONS[instruction]

        elif instruction in MIRRORS:
            self._dir = MIRRORS[instruction](*self._dir)

        elif instruction in DIGITS:
            self.push(DIGITS.index(instruction))

        elif instruction == "!":
            self._skip = 1

        elif instruction in '"\'':
            self._array_parse = True
            self._parse_char = instruction

        elif instruction == "$":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem2)
            self.push(elem1)
            
        elif instruction == "%":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                self.push(elem1 % elem2)

        elif instruction == "&":
            if self._register_stack[-1] is None:
                self._register_stack[-1] = self.pop()

            else:
                self.push(self._register_stack.pop())
                self._register_stack.append(None)

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
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(int(elem1 // elem2))

        elif instruction == "H":
            for elem in self._curr_stack:
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

            if self.is_num(elem):
                popped = [self.pop() for _ in range(elem)][::-1]

                self._curr_stack.extend(popped)
                self._curr_stack.extend(deepcopy(popped))

        elif instruction == "M":
            elem = self.pop()

            if self.is_num(elem):
                self.push(elem - 1)

        elif instruction == "N":
            self.output_as_num(self.pop())
            self.output("\n")

        elif instruction == "P":
            elem = self.pop()

            if self.is_num(elem):
                self.push(elem + 1)

        elif instruction == "Q":
            skip = self.pop()
            cond = self.pop()

            if not cond:
                self._skip = max(0, skip)

        elif instruction == "S":
            raise InvalidStateException # Shouldn't reach here

        elif instruction == "T":
            self._bookmark_pos = self._pos[:]
            self._bookmark_dir = self._dir

        elif instruction == "V":
            self._set_variable = True

        elif instruction == "X":
            elem2 = self.pop()
            elem1 = self.pop()
            self.push(elem1 ** elem2)

        elif instruction == "Z":
            elem = self.pop()
            self.push(0 if elem else 1)

        elif instruction == "`":
            self._push_char = True

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

            if self.is_num(elem):
                self.push(deepcopy(self._curr_stack[~elem]))

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

            if self.is_num(elem2) and self.is_num(elem3):
                y = elem3
                x = elem2
                char = elem1

                if self.is_num(char):
                    self._board[y][x] = char

                elif self.is_array(char):
                    curr_y = y
                    curr_x = x

                    for c in char:
                        if c in [10, 13]:
                            curr_y += 1
                            curr_x = x

                        else:
                            self._board[curr_y][curr_x] = c
                            curr_x += 1                    
                    
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
            condition = self.pop()
            self.push(condition)

            if condition:
                self._skip = 1

##        elif instruction == "[":
##            elem = self.pop()
##            
##            if elem > 0:
##                to_move, self._stack_stack[-1] = self._curr_stack[-elem:], self._curr_stack[:-elem]
##            else:
##                to_move = []
##
##            self._stack_stack.append(to_move)
##            self._curr_stack = self._stack_stack[-1]
##            self._register_stack.append(None)
##
##        elif instruction == "]":           
##            if len(self._stack_stack) == 1:
##                self._stack_stack = [[]]
##                self._curr_stack = self._stack_stack[-1]
##                self._register_stack = [None]
##
##            else:
##                self._register_stack.pop()
##
##                last = self._stack_stack.pop()
##                self._curr_stack = self._stack_stack[-1]
##                self._curr_stack.extend(last)


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

        elif instruction == "+":
            self._curr_stack = [sum(self._curr_stack)]

        elif instruction == "*":
            self._curr_stack = [reduce(operator.mul, self._curr_stack, 1)]

        elif instruction == "2":
            self.push(math.e)

        elif instruction == "3":
            self.push(math.pi)

        elif instruction == "C":
            elem = self.pop()
            self.push(math.cos(elem))

        elif instruction == "L":
            elem2 = self.pop()
            elem1 = self.pop()
            self.push(math.log(elem1, elem2))

        elif instruction == "P":
            elem = self.pop()

            if self.is_num(elem):
                self.push(1 if is_probably_prime(elem) else 0)

        elif instruction == "S":
            elem = self.pop()
            self.push(math.sin(elem))

        elif instruction == "T":
            elem = self.pop()
            self.push(math.tan(elem))

        elif instruction == "l":
            elem = chr(self.pop())
            self.push(ord(elem.lower()))

        elif instruction == "u":
            elem = chr(self.pop())
            self.push(ord(elem.upper()))

        elif instruction == "x":
            elem = self.pop()
            self.push(elem * random.random())

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


    def output(self, out):
        sys.stdout.write(out)
        sys.stdout.flush()
            

    def output_as_char(self, out):
        if isinstance(out, list):
            for elem in out:
                self.output_as_char(elem)

        else:
            self.output(chr(round(out)))


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

    try:
        with open(filename) as infile:
            interpreter = Interpreter(infile.read())

    except UnicodeDecodeError:
        with codecs.open(filename, "r", "utf_8") as infile:
            interpreter = Interpreter(infile.read())

    try:
        while True:
            interpreter.tick()

    except HaltProgram:
        pass
    
    except KeyboardInterrupt:    
        print("^C", file=sys.stderr)

    except Exception as e:
        pos = interpreter._pos
        char = interpreter._board[pos[1]][pos[0]]

        print("something smells fishy... ", end="", file=sys.stderr)
        
        if char in range(32, 127):
            print("(instruction {} '{}' at {},{})".format(char, chr(char), pos[0], pos[1]), file=sys.stderr)
        else:
            print("(instruction {} at {},{})".format(char, pos[0], pos[1]), file=sys.stderr)

        # For debugging
        if len(sys.argv) > 2 and "-d" in sys.argv[:-1]:
            raise e

    

