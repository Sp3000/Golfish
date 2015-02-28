"""
Golfish, the 2D golf-ish language based on ><>

Requires Python 3 (tested on Python 3.4.2)

Version: 0.2.3 (updated 28 Feb 2015)
"""

from collections import defaultdict, namedtuple
from copy import deepcopy
import sys
from getch import _Getch

from fractions import gcd
from functools import reduce
import operator
import random
import cmath
import math

from library import *

DIGITS = "0123456789abcdef"

DIRECTIONS = {"^": (0, -1),
              ">": (1, 0),
              "v": (0, 1),
              "<": (-1, 0)}

MIRRORS = {"/": lambda x,y: (-y, -x),
           "\\": lambda x,y: (y, x),
           "|": lambda x,y: (-x, y),
           "_": lambda x,y: (x, -y),
           "#": lambda x,y: (-x, -y)}

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

        self._last_printed = ""
        self._output_buffer = []

        self._toggled = False # S
        self._skip = 0 # ?! and more
        
        self._push_char = False # `

        self._escape = False
        self._char_parse = False # '
        self._array_parse = False # "
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

        if instruction in self._variable_map:
            self.push(self._variable_map[instruction])
            return

        if self._set_variable == True:
            elem = self.pop()
            self._variable_map[instruction] = deepcopy(elem)
            self.push(elem)
            
            self._set_variable = False
            return

        if self._char_parse:
            if self._escape:
                if instruction in "'`nr":
                    self.push({"'": 39, "`": 96, "n": 10, "r": 13}[instruction])

                else:
                    self.push(96)
                    self.push(char)

                self._escape = False

            else:
                if instruction == "'":
                    self._char_parse = False

                elif instruction == "`":
                    self._escape = True

                else:
                    self.push(char)

            return

        if self._array_parse:
            if self._escape:
                if instruction in '"`nr':
                    self._parse_buffer.append({'"': 34, '`': 96, 'n': 10, 'r': 13}[instruction])

                else:
                    self._parse_buffer.append(96)
                    self._parse_buffer.append(char)

                self._escape = False

            else:
                if instruction == '"':
                    self._array_parse = False
                    self.push(self._parse_buffer)
                    self._parse_buffer = []

                elif instruction == "`":
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

        elif instruction == '"':
            self._array_parse = True

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

        elif instruction == "'":
            self._char_parse = True

        elif instruction == "(":
            elem2 = self.pop()
            elem1 = self.pop()

            if (self.is_num(elem1) and self.is_num(elem2) or
                self.is_array(elem1) and self.is_array(elem2)):
                
                self.push(1 if elem1 < elem2 else 0)

            elif self.is_array(elem1) and self.is_num(elem2):
                self.push(elem1[elem2:])

            elif self.is_array(elem2) and self.is_num(elem1):
                self.push(elem2[elem1:])

        elif instruction == ")":
            elem2 = self.pop()
            elem1 = self.pop()

            if (self.is_num(elem1) and self.is_num(elem2) or
                self.is_array(elem1) and self.is_array(elem2)):

                self.push(1 if elem1 > elem2 else 0)

            elif self.is_array(elem1) and self.is_num(elem2):
                self.push(elem1[:elem2])

            elif self.is_array(elem2) and self.is_num(elem1):
                self.push(elem2[:elem1])

        elif instruction == "*":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                self.push(elem1 * elem2)

            elif (self.is_array(elem1) and self.is_num(elem2) or
                  self.is_num(elem1) and self.is_array(elem2)):
                
                self.push(elem1 * elem2)

        elif instruction == "+":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                self.push(elem1 + elem2)

            elif self.is_array(elem1) and self.is_array(elem2):
                self.push(elem1 + elem2)

            elif self.is_num(elem1) and self.is_array(elem2):
                self.push([elem1] + elem2)

            elif self.is_array(elem1) and self.is_num(elem2):
                self.push(elem1 + [elem2])

        elif instruction == ",":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                div = elem1 / elem2

                if int(div) == div:
                    div = int(div)
                    
                self.push(div)

        elif instruction == "-":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                self.push(elem1 - elem2)

        elif instruction == ".":
            y = self.pop()
            x = self.pop()

            self._pos = [x, y]

        elif instruction == ":":
            elem = self.pop()

            self.push(elem)
            self.push(deepcopy(elem))
            
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

            self.push(elem3)
            self.push(elem1)
            self.push(elem2)
            
        elif instruction == "A":
            elem = self.pop()

            if self.is_num(elem):
                self.push([self.pop() for _ in range(elem)][::-1])

            elif self.is_array(elem):
                self._curr_stack.extend(elem)

        elif instruction == "B":
            base = self.pop()
            elem = self.pop()

            if self.is_num(elem):
                # Negative numbers?
                elem = abs(elem)
                
                if elem == 0:
                    self.push([0])

                else:
                    converted = []
                    
                    while elem > 0:
                        remainder = elem % base
                        converted.append(remainder)
                        elem //= base

                    self.push(converted[::-1])

            elif self.is_array(elem):
                converted = sum(base**i * x for i,x in enumerate(elem[::-1]))
                self.push(converted)

        elif instruction == "C":
            elem = self.pop()

            if not self.is_num(elem) or elem >= 0:
                self.push(elem)
                self._skip = 1

        elif instruction == "G":
            elem = self.pop()

            if self.is_num(elem):
                self.push(list(range(elem)))

            elif self.is_array(elem):
                self.push(len(elem))

        elif instruction == "H":
            for elem in self._curr_stack:
                self.output_as_char(elem)

            self.halt()

        elif instruction == "I":
            num = ""
            char = self.read_char()

            while char >= 0 and chr(char) in "0123456789":
                num += chr(char)
                char = self.read_char()

            self.push(int(num) if num else -1)

        elif instruction == "J":
            y = self.pop()
            x = self.pop()
            condition = self.pop()

            if condition:
                self._pos = [x, y]

        elif instruction == "K":
            elem = self.pop()

            if self.is_num(elem):
                popped = []
                
                for _ in range(elem):
                    popped.append(self.pop())

                popped.reverse()

                self._curr_stack.extend(popped)
                self._curr_stack.extend(deepcopy(popped))

        elif instruction == "L":
            char = self.read_char()

            if char == -1:
                self.push(char)

            else:
                line = []

                while char not in [-1, 10, 13]:
                    line.append(char)
                    char = self.read_char()

                self.push(line)                

        elif instruction == "M":
            elem = self.pop()

            if self.is_num(elem):
                self.push(elem - 1)

        elif instruction == "N":
            elem = self.pop()
            self.push(0 if elem else 1)

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

            if self.is_array(elem1) and self.is_num(elem2):
                if elem2 in elem1:
                    self.push(elem1.index(elem2))

                else:
                    self.push(-1)

            if self.is_num(elem1) and self.is_array(elem2):
                if elem1 in elem2:
                    self.push(elem2.index(elem1))

                else:
                    self.push(-1)

            elif self.is_num(elem1) and self.is_num(elem2):
                result = elem1 ** elem2

                if not isinstance(result, complex) and int(result) == result:
                    result = int(result)
                    
                self.push(result)
                    
        elif instruction == "Z":
            condition = self.pop()
            self.push(condition)

            if condition:
                self._skip = 1

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
            y = self.pop()
            x = self.pop()
            char = self.pop()

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
            self.push(-1)

        elif instruction == "[":
            elem = self.pop()
            
            if elem > 0:
                to_move, self._stack_stack[-1] = self._curr_stack[-elem:], self._curr_stack[:-elem]
            else:
                to_move = []

            self._stack_stack.append(to_move)
            self._curr_stack = self._stack_stack[-1]
            self._register_stack.append(None)

        elif instruction == "]":           
            if len(self._stack_stack) == 1:
                self._stack_stack = [[]]
                self._curr_stack = self._stack_stack[-1]
                self._register_stack = [None]

            else:
                self._register_stack.pop()

                last = self._stack_stack.pop()
                self._curr_stack = self._stack_stack[-1]
                self._curr_stack.extend(last)

        elif instruction == "{":
            self.rotate_left()

        elif instruction == "}":
            self.rotate_right()

        elif instruction == "~":
            self.pop()

        elif " " < instruction <= "~":
            raise NotImplementedError


    def handle_switched_instruction(self, instruction):
        if instruction == "%":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(gcd(elem1, elem2))

        elif instruction == "+":
            elem = self.pop()

            if self.is_array(elem):
                if all(map(self.is_num, elem)):
                    self.push(reduce(operator.add, elem, 0))

                elif all(map(self.is_array, elem)):
                    self.push(reduce(operator.add, elem, []))

                else:
                    self.push(reduce(operator.add, [x if self.is_array(x) else [x] for x in elem], []))

        elif instruction == "*":
            elem = self.pop()

            if self.is_array(elem):
                if all(map(self.is_num, elem)):
                    self.push(reduce(operator.mul, elem, 1))

        elif instruction == "2":
            self.push(math.e)

        elif instruction == "3":
            self.push(math.pi)

        elif instruction == "?":
            cond = self.pop()
            elem = self.pop()

            if cond:
                self.push(elem)
                
            else:
                self._skip = 1
                
        elif instruction == "D":
            self.output(str(self._curr_stack))

        elif instruction == "P":
            elem = self.pop()

            if self.is_num(elem):
                self.push(1 if is_probably_prime(elem) else 0)

        elif instruction == "l":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                result = math.log(elem1, elem2)

                if elem2**round(result) == elem1:
                    result = round(result)
                    
                self.push(result)

        elif instruction == "n":
            self.output_as_num(self.pop(), buffer=False)

        elif instruction == "x":
            elem2 = self.pop()
            elem1 = self.pop()

            if self.is_num(elem1) and self.is_num(elem2):
                self.push(random.randint(math.ceil(elem1), math.floor(elem2)))

        elif " " < instruction <= "~":
            raise NotImplementedError


    def is_num(self, elem):
        return any(isinstance(elem, x) for x in [int, float, complex])


    def is_array(self, elem):
        return isinstance(elem, list)


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
        if sys.stdin.isatty():
            # Console
            char = getch()

            if ord(char) == 3:
                raise KeyboardInterrupt

        else:
            char = sys.stdin.read(1)

        return ord(char) if char else -1


    def _chr(self, elem):
        return chr(round(elem))


    def output(self, out):
        self.output_check(out)
        sys.stdout.write(out)
        sys.stdout.flush()

        if out:
            self._last_printed = out[-1]


    def output_check(self, out):
        if self._output_buffer:
            if self._output_buffer == [" "]:
                if not (out and out[0].isspace()):
                    self.output(" ")

                self._output_buffer.clear()
            

    def output_as_char(self, out):
        if self.is_num(out):
            self.output(self._chr(out))

        else:
            for elem in out:
                self.output_as_char(elem)


    def output_as_num(self, out, buffer=True):
        if self.is_num(out):
            self.output(str(out))

            if buffer:
                self._output_buffer.append(" ")

        else:
            for elem in out:
                self.output_as_num(elem, buffer)


    def halt(self):
        raise HaltProgram

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Please include a filename")
        exit()
        
    filename = sys.argv[1]

    with open(filename) as infile:
        interpreter = Interpreter(infile.read())

    try:
        while True:
            interpreter.tick()

    except HaltProgram:
        pass
    
    except KeyboardInterrupt:    
        print("^C")

    except Exception as e:
        pos = interpreter._pos
        char = interpreter._board[pos[1]][pos[0]]

        if isinstance(char, list):
            print("something smells fishy... "
                  "(instruction {} at {},{})".format(char, pos[0], pos[1]))

        else:
            print("something smells fishy... "
                  "(instruction {} '{}' at {},{})".format(char, chr(char), pos[0], pos[1]))

        # For debugging
        if len(sys.argv) > 2 and "-d" in sys.argv[2:]:
            raise e

    
