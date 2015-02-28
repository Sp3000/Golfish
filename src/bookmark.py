from collections import namedtuple
from enum import Enum

class BookmarkTypes(Enum):
    TELEPORT = 0
    MAP = 1
    REDUCE = 2
    REPEAT = 3

Bookmark = namedtuple("Bookmark", ["pos", "dir", "type", "extra"])

class BookmarkManager():
    def __init__(self):
        self.bookmarks = []


    def add_teleport(self, pos, dir_):
        self.bookmarks.append(Bookmark(pos[:], dir_[:], BookmarkTypes.TELEPORT, None))


    def add_map(self, pos, dir_, elems):
        self.bookmarks.append(Bookmark(pos[:], dir_[:], BookmarkTypes.MAP, [elems, []]))


    def add_reduce(self, pos, dir_, elems):
        self.bookmarks.append(Bookmark(pos[:], dir_[:], BookmarkTypes.REDUCE, elems))


    def add_repeat(self, pos, dir_, n):
        self.bookmarks.append(Bookmark(pos[:], dir_[:], BookmarkTypes.REPEAT, [n]))


    def pop(self):
        if self.bookmarks:
            self.bookmarks.pop()


    def teleport(self, curr_pos, curr_dir, curr_stack):
        if not self.bookmarks:
            return [-1, 0], (1, 0)

        last_bm = self.bookmarks[-1]

        if last_bm.type == BookmarkTypes.TELEPORT:
            return BookmarkTypes.TELEPORT, [last_bm.pos, last_bm.dir]

        if last_bm.type == BookmarkTypes.MAP:
            if curr_stack:
                last_bm.extra[1].append(curr_stack.pop())
                
            if not last_bm.extra[0]:
                mapped = last_bm.extra[1]
                self.pop()
                args = [curr_pos, curr_dir, mapped]

            else:
                args = [last_bm.pos, last_bm.dir, last_bm.extra[0].pop(0)]

            return BookmarkTypes.MAP, args

        if last_bm.type == BookmarkTypes.REDUCE:
            if last_bm.extra:
                args = [last_bm.pos, last_bm.dir, last_bm.extra.pop(0)]

            else:
                self.pop()
                args = [curr_pos, curr_dir]

            return BookmarkTypes.REDUCE, args

        if last_bm.type == BookmarkTypes.REPEAT:
            last_bm.extra[0] -= 1

            if last_bm.extra[0] > 0:
                args = [last_bm.pos, last_bm.dir]

            else:
                self.pop()
                args = [curr_pos, curr_dir]

            return BookmarkTypes.REPEAT, args
        
    
