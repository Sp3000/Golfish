"""
Gol><>, the slightly golfier version of ><>

Requires Python 3 (tested on Python 3.4.2)

Version: 0.4.2 (updated 11 Nov 2015)
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
    def __init__(self, code="", input_=None, debug=False, online=False, tick_limit=None):
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

        self._ticks = 0
        self._tick_limit = tick_limit

        self._stack_tape = defaultdict(list)
        self._curr_stack = self._stack_tape[0]
        self._stack_num = 0
        self._register_tape = defaultdict(lambda:None)

        self._input = input_
        self._debug = debug
        self._online = online
        
        self._input_buffer = None
        self._last_output = '\n'

        self._toggled = False # S
        self._skip = 0 # ?! and more

        self._teleport_pos = [-1, 0] # tT
        self._teleport_dir = DIRECTIONS[">"]

        self._variable_map = {} # V
        self._function_alias_map = {} # A

        self._R_repeat = 1 # R

        self._bookmark_stack = [] # AFQW
        self._marker_stack = []
        self._last_loop_counter = 0 # L

        self._eof = False # E

        self._closure_stack = [] # j

    def run(self):        
        try:
            while True:
                self.tick()

        except HaltProgram:
            pass
        
        except KeyboardInterrupt as e:    
            print("^C", file=sys.stderr)
            self.traceback(e)

        except TimeoutError as e:
            if self._last_output not in "\n\r":
                self.print_error('\n', end='')
                
            self.print_error("[Timeout]")
            self.traceback(e)

        except Exception as e:
            pos = self._pos
            char = self._board[pos[1]][pos[0]]

            if self._last_output not in "\n\r":
                self.print_error('\n', end='')

            self.print_error("something smells fishy... ", end='')

            if char in range(32, 127):
                self.print_error("(instruction {} '{}' at {},{})".format(char, "S"*self._toggled + chr(char), pos[0], pos[1]))
            else:
                self.print_error("(instruction {} at {},{})".format(char, pos[0], pos[1]))

            self.traceback(e)


    def tick(self):
        self.move()

        if self._pos[1] in self._board and self._pos[0] in self._board[self._pos[1]]:
            self.handle_instruction(self._board[self._pos[1]][self._pos[0]])

        self._ticks += 1

        if self._tick_limit is not None and self._ticks > self._tick_limit:
            raise TimeoutError


    def move(self):
        # Move forward one step
        self._pos[0] = int(self._pos[0]) + self._dir[0]
        self._pos[1] = int(self._pos[1]) + self._dir[1]

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

        elif instruction == ' ':
            pass

        elif instruction == '!':
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

        elif instruction == '$':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem2)
            self.push(elem1)
            
        elif instruction == '%':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 % elem2)

        elif instruction == '&':
            if self._register_tape[self._stack_num] is None:
                self._register_tape[self._stack_num] = self.pop()

            else:
                self.push(self._register_tape[self._stack_num])
                self._register_tape[self._stack_num] = None

        elif instruction == '(':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(1 if elem1 < elem2 else 0)

        elif instruction == ')':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(1 if elem1 > elem2 else 0)

        elif instruction == '*':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 * elem2)

        elif instruction == '+':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 + elem2)

        elif instruction == ',':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 / elem2)

        elif instruction == '-':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 - elem2)

        elif instruction == '.':
            y = self.pop()
            x = self.pop()

            self._pos = [x, y]

        elif instruction == ':':
            elem = self.pop()

            self.push(elem)
            self.push(elem)
            
        elif instruction == ';':
            self.halt()

        elif instruction == '=':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(1 if elem1 == elem2 else 0)

        elif instruction == '?':
            condition = self.pop()

            if not condition:
                self._skip = 1

        elif instruction == '@':
            elem3 = self.pop()
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem2)
            self.push(elem3)
            self.push(elem1)

        elif instruction == 'A':
            self.move()
            char = self.char(num=False)

            y = self.pop()
            self._function_alias_map[char] = [y, self._closure_stack]
            self._closure_stack = []

        elif instruction == 'B':
            if self._bookmark_stack:
                self.bookmark_break()
            else:
                raise InvalidStateException("Break from non-loop/function")

        elif instruction == 'C':
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

        elif instruction == 'D':
            if self._last_output not in "\n\r":
                self.output('\n')

            self.output(str(self._curr_stack).replace(',', '') + '\n')

        elif instruction == 'E':
            if self._eof:
                self.pop()
            else:
                self._skip = 1

        elif instruction == 'F':
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

        elif instruction == 'H':
            while self._curr_stack:
                elem = self.pop()
                self.output_as_char(elem)

            self.halt()

        elif instruction == 'I':
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

        elif instruction == 'J':
            y = self.pop()
            x = self.pop()
            condition = self.pop()

            if condition:
                self._pos = [x, y]

        elif instruction == 'K':
            elem = self.pop()
            popped = [self.pop() for _ in range(elem)][::-1]

            self._curr_stack.extend(popped)
            self._curr_stack.extend(popped)

        elif instruction == 'L':
            if self._bookmark_stack and isinstance(self._bookmark_stack[-1], LoopBookmark):
                self.push(self._bookmark_stack[-1].counter)
            else:
                self.push(self._last_loop_counter)

        elif instruction == 'M':
            elem = self.pop()
            self.push(elem - 1)

        elif instruction == 'N':
            self.output_as_num(self.pop())
            self.output('\n')

        elif instruction == 'P':
            elem = self.pop()
            self.push(elem + 1)

        elif instruction == 'Q':
            cond = self.pop()

            if cond:
                bookmark = IfBookmark(self.pos_before(), self._dir[:])
                self._bookmark_stack.append(bookmark)
            else:
                self.to_block_end()

        elif instruction == 'R':
            elem = self.pop()
            self._R_repeat = elem

        elif instruction == 'S':
            raise InvalidStateException # Shouldn't reach here

        elif instruction == 'T':
            self._teleport_pos = self._pos[:]
            self._teleport_dir = self._dir[:]

        elif instruction == 'V':
            self.move()
            char = self.char(num=False)

            elem = self.pop()
            self.push(elem)
            self._variable_map[char] = elem

        elif instruction == 'W':
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

            elem = self.pop()
            if not self._bookmark_stack[-1].w_marker:
                self.push(elem)
            
            if not elem:
                self.bookmark_break()
            else:
                self._curr_stack.extend(self._bookmark_stack[-1].closure_stack)

        elif instruction == 'X':
            elem2 = self.pop()
            elem1 = self.pop()
            result = elem1 ** elem2

            if isinstance(result, complex):
                raise InvalidStateException("Computation resulted in a complex number")
            
            self.push(result)

        elif instruction == 'Z':
            condition = self.pop()

            if condition:
                self._skip = 1

        elif instruction == '[':
            buffer, self._stack_tape[self._stack_num] = self._curr_stack, []
            self.stack_left()
            self._curr_stack.extend(buffer)

        elif instruction == ']':
            n = self.pop()
            buffer = []

            for _ in range(n):
                buffer.append(self.pop())

            self.stack_right()

            while buffer:
                self.push(buffer.pop())

        elif instruction == '`':
            self.move()
            char = self.char()
            self.push(char)

        elif instruction == 'g':
            y = self.pop()
            x = self.pop()

            if y in self._board and x in self._board[y]:
                self.push(self._board[y][x])
            else:
                self.push(0)

        elif instruction == 'h':
            self.output_as_num(self.pop())
            self.halt()

        elif instruction == 'i':
            char = self.read_char()

            if char == EOF:
                self._eof = True

            self.push(char)

        elif instruction == 'j':
            elem = self.pop()
            self._closure_stack.append(elem)

        elif instruction == 'k':
            elem = self.pop()

            if self._curr_stack:
                self.push(self._curr_stack[~elem % len(self._curr_stack)])
            else:
                self.push(0)

        elif instruction == 'l':
            self.push(len(self._curr_stack))

        elif instruction == 'm':
            self.push(-1)

        elif instruction == 'n':
            self.output_as_num(self.pop())

        elif instruction == 'o':
            self.output_as_char(self.pop())

        elif instruction == 'p':
            elem3 = self.pop()
            elem2 = self.pop()
            elem1 = self.pop()

            y = elem3
            x = elem2
            char = elem1
            self._board[y][x] = char                  
                    
        elif instruction == 'q':
            cond = self.pop()

            if not cond:
                self._skip = 2

        elif instruction == 'r':
            self._curr_stack.reverse()

        elif instruction == 's':
            elem = self.pop()
            self.push(elem + 16)

        elif instruction == 't':
            self._pos = self._teleport_pos[:]
            self._dir = self._teleport_dir[:]

        elif instruction == 'u':
            self.stack_right()
            
        elif instruction == 'w':
            self._marker_stack.append([self._pos[:], self._dir[:]])
                
        elif instruction == 'x':
            self._dir = random.choice(list(DIRECTIONS.values()))

        elif instruction == 'y':
            self.stack_left()

        elif instruction == 'z':
            elem = self.pop()
            self.push(0 if elem else 1)

        elif instruction == '{':
            self.rotate_left()

        elif instruction == '|':
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

        elif instruction == '}':
            self.rotate_right()

        elif instruction == '~':
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
                        self.output_as_char(escapes[char])
                    else:
                        self.output('`')
                        self.output_as_char(char)

                    escaped = False

                else:
                    if char == ord('`'):
                        escaped = True
                    else:
                        self.output_as_char(char)

                self.move()
                char = self._board[self._pos[1]][self._pos[0]]
        
        elif instruction == '%':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(gcd(elem1, elem2))

        elif instruction == '&':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 & elem2)

        elif instruction == '(':
            elem = self.pop()
            self.push(math.floor(elem))

        elif instruction == ')':
            elem = self.pop()
            self.push(math.ceil(elem))

        elif instruction == ',':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(int(elem1 // elem2))

        elif instruction == '2':
            self.push(math.e)

        elif instruction == '3':
            self.push(math.pi)

        elif instruction == '<':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(min(elem1, elem2))

        elif instruction == '=':
            elem = self.pop()
            self.push(round(elem))

        elif instruction == '>':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(max(elem1, elem2))

        elif instruction == 'A':
            elem = self.pop()
            self.push(abs(elem))

        elif instruction == 'D':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 // elem2)
            self.push(elem1 % elem2)

        elif instruction == 'E':
            self.push(int(self._eof))

        elif instruction == 'L':
            elem2 = self.pop()
            elem1 = self.pop()
            self.push(math.log(elem1, elem2))

        elif instruction == 'P':
            elem = self.pop()
            self.push(1 if is_probably_prime(elem) else 0)

        elif instruction == 'T':
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

        elif instruction == '^':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 ^ elem2)

        elif instruction == 'l':
            elem = self.chr(self.pop())
            self.push(ord(elem.lower()))

        elif instruction == 'n':
            places = self.pop()
            num = self.pop()
            self.output("{{:.{}f}}".format(places).format(float(num)))

        elif instruction == 'u':
            elem = self.chr(self.pop())
            self.push(ord(elem.upper()))

        elif instruction == 'x':
            self.push(random.random())

        elif instruction == '|':
            elem2 = self.pop()
            elem1 = self.pop()

            self.push(elem1 | elem2)

        else:
            raise NotImplementedError


    def push(self, elem, index=None):
        if elem == int(elem):
            elem = int(elem)

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


    def char(self, num=True):
        if num:
            return self._board[self._pos[1]][self._pos[0]]
        else:
            return self.chr(self._board[self._pos[1]][self._pos[0]])


    def chr(self, elem):
        return chr(int(elem))


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
        # TODO: improve
        start_pos = self._pos[:]
        self.move()

        if self.char(num=False) in "FWQ":
            self.move()
        
        string_parse = False
        escape = False
        switched = False
        depth = 0

        while depth or string_parse or escape or switched or self.char(num=False) != '|':
            # Need to check VA for everything here
            c = self.char(num=False)
            
            if switched:
                switched = False

            elif c == '`':
                escape = not escape

            elif escape:
                escape = False

            elif (c in "'\"" and c not in self._variable_map and
                  c not in self._function_alias_map):

                string_parse = not string_parse

            elif not string_parse:
                if c in "FWQ":
                    depth += 1

                elif c == '|':
                    depth -= 1

                elif c == 'S':
                    switched = True

            self.move()

            if self._pos == start_pos:
                raise InvalidStateException("Missing | end")
        
    def read_char(self):
        # Note: self._eof not set here, but in input instructions
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
                return EOF

        else:
            if self._input:
                c = self._input[0]
                self._input = self._input[1:]
                return ord(c)

            else:
                return EOF

    def output(self, out):
        if out:
            self._last_output = out[-1]

        sys.stdout.write(out)
        sys.stdout.flush()
            

    def output_as_char(self, out):
        if isinstance(out, list):
            for elem in out:
                self.output_as_char(elem)

        else:
            self.output(self.chr(out))


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


    def print_error(self, *objects, end=""):
        if self._online:
            print(*objects, end=end)
        else:
            print(*objects, end=end, file=sys.stderr)


    def traceback(self, e):
        if self._debug:
            if self._online:
                traceback.print_exc(file=sys.stdout)
            else:
                raise e


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
