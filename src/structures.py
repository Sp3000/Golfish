from collections import defaultdict

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


class BottomlessStack():
    def __init__(self, stack=None):
        self.stack = stack or []


    def pop(self):
        return self.stack.pop() if self.stack else 0


    def append(self, elem):
        self.stack.append(elem)


    def extend(self, other):
        self.stack.extend(other)


    def reverse(self):
        self.stack.reverse()


    def rotate_left(self):
        if self.stack:
            elem = self.stack.pop(0)
            self.stack.append(elem)


    def rotate_right(self):
        if self.stack:
            elem = self.stack.pop()
            self.stack.insert(0, elem)


    def copy(self):
        return BottomlessStack(self.stack.copy())


    def __getitem__(self, index):
        return self.stack[index % len(self.stack)] if self.stack else 0

    
    def __iter__(self):
        return iter(self.stack)


    def __len__(self):
        return len(self.stack)


    def __repr__(self):
        return repr(self.stack)


class CodeBoard():
    def __init__(self, code=""):
        self.board = defaultdict(lambda: defaultdict(int))

        rows = code.split('\n')
        x = y = 0

        for char in code:
            if char == '\n':
                y += 1
                x = 0

            else:
                self.board[y][x] = ord(char)
                x += 1


    def has_y(self, y):
        return y in self.board


    def max_y(self):
        return max(self.board.keys())


    def max_x(self, y):
        return max(self.board[y].keys())


    def __contains__(self, pos):
        return pos[1] in self.board and pos[0] in self.board[pos[1]]


    def __getitem__(self, pos):
        if pos[1] in self.board and pos[0] in self.board[pos[1]]:
            return self.board[pos[1]][pos[0]]

        return 0


    def __setitem__(self, pos, elem):
        self.board[pos[1]][pos[0]] = elem


    def __repr__(self):
        return repr(self.board)



    
