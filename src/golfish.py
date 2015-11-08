"""
Gol><>, the slightly golfier version of ><>

Requires Python 3 (tested on Python 3.4.2)

Version: 0.4.0 (updated 6 Nov 2015)
"""

import argparse
import codecs
from collections import defaultdict, namedtuple
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

DIRECTIONS = {'^': [0, -1],
              '>': [1, 0],
              'v': [0, 1],
              '<': [-1, 0]}

MIRRORS = {'/': lambda x,y: [-y, -x],
           '\\': lambda x,y: [y, x],
           '#': lambda x,y: [-x, -y]}

EOF = -1


class HaltProgram(Exception):
    pass


class InvalidStateException(Exception):
    pass


class Bookmark():
    def __init__(self, pos, dir_, closure_stack):
        self.pos = pos
        self.dir = dir_
        self.closure_stack = closure_stack


class LoopBookmark(Bookmark):
    def __init__(self, pos, dir_, closure_stack):
        super().__init__(pos, dir_, closure_stack)
        self.counter = 0

    def increment_counter(self):
        self.counter += 1

class WhileBookmark(LoopBookmark):
     def __init__(self, pos, dir_, closure_stack, w_marker=None):
         super().__init__(pos, dir_, closure_stack)
         self.w_marker = w_marker


class ForBookmark(LoopBookmark):
    def __init__(self, pos, dir_, closure_stack, limit):
        super().__init__(pos, dir_, closure_stack)
        self.limit = limit


class FunctionBookmark(Bookmark):
    def __init__(self, pos, dir_, closure_stack):
        super().__init__(pos, dir_, closure_stack)


class IfBookmark(Bookmark):
    def __init__(self, pos, dir_):
        super().__init__(pos, dir_, None)


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

        self._bookmark_pos = [-1, 0] # tT, not the same as while/for bookmarks
        self._bookmark_dir = DIRECTIONS[">"]

        self._variable_map = {}
        self._function_alias_map = {}

        self._input = input_
        self._debug = debug

        self._online = online

        self._R_repeat = 1

        self._bookmark_stack = []
        self._marker_stack = []

        self._eof = False

        self._last_loop_counter = 0

        self._closure_stack = []

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
            if self._dir == DIRECTIONS['>'] and self._pos[0] > max(self._board[self._pos[1]].keys()):
                self._pos[0] = 0

            elif self._dir == DIRECTIONS['<'] and self._pos[0] < 0:
                self._pos[0] = max(self._board[self._pos[1]].keys())

        elif self._dir == DIRECTIONS['v'] and self._pos[1] > max(self._board.keys()):
            self._pos[1] = 0
        
        elif self._dir == DIRECTIONS['^'] and self._pos[1] < 0:
            self._pos[1] = max(self._board.keys())


    def pos_before(self):
        return [self._pos[0] - self._dir[0], self._pos[1] - self._dir[1]]
    

    def handle_instruction(self, char):
        instruction = chr(char)

        if instruction == "S" and not self._toggled:
            self._toggled = True
            return

        if self._skip > 0:
            self._skip -= 1
            self._toggled = False
            return

        elif self._skip < 0:
            self._skip = 0

        tmp_R_repeat, self._R_repeat = int(self._R_repeat), 1
        tmp_pos = self._pos[:]
        
        if self._toggled:
            for _ in range(tmp_R_repeat):
                self._pos = tmp_pos[:]
                self.handle_switched_instruction(instruction)
                
            self._toggled = False

        else:
            if tmp_R_repeat > 0:
                for _ in range(tmp_R_repeat):
                    self._pos = tmp_pos[:]
                    self.handle_normal_instruction(instruction)

            else:
                # Special cases for 0R
                if instruction in "'\"`":
                    tmp_stack = self._curr_stack[:]
                    self.handle_normal_instruction(instruction)
                    self._curr_stack = tmp_stack

    def handle_normal_instruction(self, instruction):
        if instruction in self._variable_map:
            self.push(self._variable_map[instruction])
            return

        if instruction in self._function_alias_map:
            y, c = self._function_alias_map[instruction]
            
            bookmark = FunctionBookmark(self._pos[:], self._dir[:], c)
            self._bookmark_stack.append(bookmark)
            self._pos = [-1, y]
            self._dir = [1, 0]
            self._curr_stack.extend(c[::-1])
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
            self._skip += 1

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

        elif instruction == "A":
            self.move()
            char = chr(self._board[self._pos[1]][self._pos[0]])

            y = self.pop()
            self._function_alias_map[char] = [y, self._closure_stack]
            self._closure_stack = []

        elif instruction == "B":
            if self._bookmark_stack:
                self.bookmark_break()
            else:
                raise InvalidStateException("Break from non-loop/function")

        elif instruction == "C":
            while self._bookmark_stack and isinstance(self._bookmark_stack[-1], IfBookmark):
                self._bookmark_stack.pop()

            if self._bookmark_stack and isinstance(self._bookmark_stack[-1], LoopBookmark):
                bookmark = self._bookmark_stack[-1]
                self._pos = bookmark.pos[:]
                self._dir = bookmark.dir[:]

                if isinstance(bookmark, WhileBookmark) and bookmark.w_marker:
                        self._pos = bookmark.w_marker[0][:]
                        self._dir = bookmark.w_marker[1][:]

            else:
                raise InvalidStateException("Continue from non-loop")

        elif instruction == "D":
            self.output(str(self._curr_stack).replace(',', '') + '\n')

        elif instruction == "E":
            if self._eof:
                self.pop()
            else:
                self._skip = 1

        elif instruction == "F":
            if self._bookmark_stack and self._bookmark_stack[-1].pos == self.pos_before():
                self._bookmark_stack[-1].increment_counter()
                self._last_loop_counter = self._bookmark_stack[-1].counter
                
            else:
                limit = self.pop()
                
                bookmark = ForBookmark(self.pos_before(), self._dir[:],
                                       self._closure_stack, limit)

                self._bookmark_stack.append(bookmark)
                self._closure_stack = []

            if (self._bookmark_stack and
                self._bookmark_stack[-1].counter >= self._bookmark_stack[-1].limit):

                self.bookmark_break()

            else:
                self._curr_stack.extend(self._bookmark_stack[-1].closure_stack)

        elif instruction == "H":
            while self._curr_stack:
                elem = self.pop()
                self.output_as_char(elem)

            self.halt()

        elif instruction == "I":
            num = ""
            char = self.read_char()

            while char >= 0 and chr(char) not in "-0123456789.":
                char = self.read_char()

            while char >= 0 and chr(char) in "-0123456789.":
                if chr(char) == '.' and '.' in num:
                    break

                if chr(char) == '-' and num:
                    break

                num += chr(char)
                char = self.read_char()

            self._input_buffer = char

            if num:
                num = float(num)
                self.push(int(num) if num == int(num) else num)

            else:
                self._eof = True
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

        elif instruction == "L":
            if self._bookmark_stack and isinstance(self._bookmark_stack[-1], LoopBookmark):
                self.push(self._bookmark_stack[-1].counter)
            else:
                self.push(self._last_loop_counter)

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
            if self._bookmark_stack and self._bookmark_stack[-1].pos == self.pos_before():
                self.bookmark_break()
                
            else:
                cond = self.pop()

                if cond:
                    bookmark = IfBookmark(self.pos_before(), self._dir[:])
                    self._bookmark_stack.append(bookmark)

                else:
                    self.to_block_end()

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
            char = chr(self._board[self._pos[1]][self._pos[0]])

            elem = self.pop()
            self.push(elem)
            self._variable_map[char] = elem

        elif instruction == "W":
            if self._bookmark_stack and self._bookmark_stack[-1].pos == self.pos_before():
                self._bookmark_stack[-1].increment_counter()
                self._last_loop_counter = self._bookmark_stack[-1].counter
                
            else:
                if self._marker_stack:
                    w_marker = self._marker_stack.pop()
                else:
                    w_marker = None
                    
                bookmark = WhileBookmark(self.pos_before(), self._dir[:],
                                         self._closure_stack, w_marker)
                
                self._bookmark_stack.append(bookmark)
                self._closure_stack = []

            if self._bookmark_stack[-1].w_marker:
                checker = self.pop
            else:
                checker = self.peek
                
            if not checker():
                self.bookmark_break()
            else:
                self._curr_stack.extend(self._bookmark_stack[-1].closure_stack)

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

        elif instruction == '[':
            buffer, self._stack_tape[self._stack_num] = self._curr_stack, []
            self.stack_left()
            self._curr_stack.extend(buffer)

        elif instruction == '_':
            elem = self.pop()
            self._closure_stack.append(elem)

        elif instruction == ']':
            n = self.pop()
            buffer = []

            for _ in range(n):
                buffer.append(self.pop())

            self.stack_right()

            while buffer:
                self.push(buffer.pop())

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
            char = self.read_char()

            if char == EOF:
                self.eof = True

            self.push(char)

        elif instruction == "k":
            elem = self.pop()

            if self._curr_stack:
                self.push(self._curr_stack[~elem % len(self._curr_stack)])
            else:
                self.push(0)

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

        elif instruction == "s":
            elem = self.pop()
            self.push(elem + 16)

        elif instruction == "t":
            self._pos = self._bookmark_pos[:]
            self._dir = self._bookmark_dir

        elif instruction == 'u':
            self.stack_right()
            
        elif instruction == "w":
            self._marker_stack.append([self._pos[:], self._dir[:]])
                
        elif instruction == "x":
            self._dir = random.choice(list(DIRECTIONS.values()))

        elif instruction == 'y':
            self.stack_left()

        elif instruction == "z":
            elem = self.pop()
            self.push(0 if elem else 1)

        elif instruction == "{":
            self.rotate_left()

        elif instruction == "|":
            if self._bookmark_stack and isinstance(self._bookmark_stack[-1], IfBookmark):
                self._bookmark_stack.pop()
                
            elif self._bookmark_stack and isinstance(self._bookmark_stack[-1], LoopBookmark):
                bookmark = self._bookmark_stack[-1]
                self._pos = bookmark.pos[:]
                self._dir = bookmark.dir[:]

                if isinstance(bookmark, WhileBookmark) and bookmark.w_marker:
                        self._pos = bookmark.w_marker[0][:]
                        self._dir = bookmark.w_marker[1][:]

            else:
                raise InvalidStateException("Unexpected if/loop end")

        elif instruction == "}":
            self.rotate_right()

        elif instruction == "~":
            self.pop()

        else:
            raise NotImplementedError


    def handle_switched_instruction(self, instruction):
        if instruction == '"':
            escaped = False
            parse_char = ord(instruction)
            self.move()
            char = self._board[self._pos[1]][self._pos[0]]
            
            while escaped or char != parse_char:
                if escaped:
                    escapes = {ord(a): ord(b) for a,b in zip("`nr","`\n\r")}
                    escapes.update({parse_char: parse_char})

                    if char in escapes:
                        self.output(chr(escapes[char]))
                    else:
                        self.output('`' + chr(char))

                    escaped = False

                else:
                    if char == ord('`'):
                        escaped = True
                    else:
                        self.output(chr(char))

                self.move()
                char = self._board[self._pos[1]][self._pos[0]]
        
        elif instruction == "%":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(gcd(elem1, elem2))

        elif instruction == "&":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 & elem2)

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

        elif instruction == "A":
            elem = self.pop()
            self.push(abs(elem))

        elif instruction == "D":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 // elem2)
            self.push(elem1 % elem2)

        elif instruction == "E":
            self.push(int(self._eof))

        elif instruction == "L":
            elem2 = self.pop()
            elem1 = self.pop()
            self.push(math.log(elem1, elem2))

        elif instruction == "P":
            elem = self.pop()
            self.push(1 if is_probably_prime(elem) else 0)

        elif instruction == "T":
            func_num = self.pop()
            functions = [math.sin, math.cos, math.tan, math.sinh, math.cosh, math.tanh,
                         math.asin, math.acos, math.atan, math.asinh, math.acosh, math.atanh, math.atan2]

            elem = self.pop()
            self.push(functions[func_num % len(functions)](elem))

        elif instruction == ']':
            n = self.pop()
            buffer = []

            for _ in range(n):
                buffer.append(self.pop())

            self.stack_right()

            while buffer:
                elem = buffer.pop()
                self.push(elem)
                self._stack_tape[self._stack_num-1].append(elem)

        elif instruction == "^":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 ^ elem2)

        elif instruction == "l":
            elem = chr(self.pop())
            self.push(ord(elem.lower()))

        elif instruction == "n":
            places = self.pop()
            num = self.pop()
            self.output("{{:.{}f}}".format(places).format(float(num)))

        elif instruction == "u":
            elem = chr(self.pop())
            self.push(ord(elem.upper()))

        elif instruction == "x":
            self.push(random.random())

        elif instruction == "|":
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 | elem2)

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


    def peek(self):
        if self._curr_stack:
            return self._curr_stack[-1]

        else:
            return 0


    def char(self):
        if self._pos[0]+1 in self._board[self._pos[1]]:
            return chr(self._board[self._pos[1]][self._pos[0] + 1])
        
        return chr(self._board[self._pos[1]][0])


    def rotate_left(self):
        self.push(self.pop(index=0))


    def rotate_right(self):
        self.push(self.pop(), index=0)


    def stack_left(self):
        self._stack_num -= 1
        self._curr_stack = self._stack_tape[self._stack_num]


    def stack_right(self):
        self._stack_num += 1
        self._curr_stack = self._stack_tape[self._stack_num]


    def bookmark_break(self):
        bookmark = self._bookmark_stack.pop()
        self._pos = bookmark.pos[:]
        self._dir = bookmark.dir[:]
        
        if not isinstance(bookmark, FunctionBookmark):
            self.to_block_end()

    def to_block_end(self):
        # To do: improve
        string_parse = False
        escape = False
        depth = -(self.char() in "FWQ")

        while depth or string_parse or escape or self.char() != '|':
            if self.char() == '`':
                escape = not escape

            elif escape:
                escape = False

            elif self.char() in "'\"":
                string_parse = not string_parse

            elif not string_parse:
                if self.char() in "FWQ":
                    depth += 1

                if self.char() == '|':
                    depth -= 1

            self.move()
        self.move()
        
    def read_char(self):
        if self._input_buffer is not None:
            char = self._input_buffer
            self._input_buffer = None
            return char
            
        if self._input is None:
            if sys.stdin.isatty():
                # Console
                char = getch()

                if ord(char) == 3:
                    raise KeyboardInterrupt

            else:
                char = sys.stdin.read(1)

            if char:
                return ord(char)
            else:
                self._eof = True
                return EOF

        else:
            if self._input:
                c = self._input[0]
                self._input = self._input[1:]
                return ord(c)

            else:
                self._eof = True
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help="Debug mode (show interpreter errors)", action="store_true")
    parser.add_argument("program_path", help="Path to file containing program",
                        type=str)

    args = parser.parse_args()
    filename = args.program_path
    debug = args.debug    

    try:
        with open(filename) as infile:
            interpreter = Golfish(infile.read(), debug=debug)

    except UnicodeDecodeError:
        with codecs.open(filename, "r", "utf_8") as infile:
            interpreter = Golfish(infile.read(), debug=debug)

    interpreter.run()
