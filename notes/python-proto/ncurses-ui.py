import contextlib
import curses
import dataclasses
import enum
import logging
import sys

import orca_format


logger = logging.getLogger(__name__)

CURSOR_GLYPH = "@"
CROSS_GLYPH = "+"
DOT_GLYPH = "."


@contextlib.contextmanager
def noecho():
    curses.noecho()
    yield
    curses.echo()


@contextlib.contextmanager
def keypad(screen):
    screen.keypad(True)
    yield
    screen.keypad(False)


@contextlib.contextmanager
def cbreak():
    curses.cbreak()
    yield
    curses.nocbreak()


@dataclasses.dataclass
class Cursor:
    x: int
    y: int

    height: int
    width: int

    def move_left(self):
        self._move_relative(-1, 0)

    def move_right(self):
        self._move_relative(1, 0)

    def move_up(self):
        self._move_relative(0, -1)

    def move_down(self):
        self._move_relative(0, 1)

    def _move_relative(self, x, y):
        self.x = max(0, min(self.x + x, self.width - 1))
        self.y = max(0, min(self.y + y, self.height - 1))


@enum.unique
class CursesColor(enum.IntEnum):
    DEFAULT = -1
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7


N_COLOR_BASE = len(CursesColor)


def init_colors():
    curses.use_default_colors()

    # Undocumented: -1 refers to default color, assuming use_default_colors has
    # been called first
    for i in range(N_COLOR_BASE):
        for j in range(N_COLOR_BASE):
            c = 1 + i * N_COLOR_BASE + j
            fg = i - 1
            bg = j - 1
            curses.init_pair(c, fg, bg)


def pair_to_index(fg, bg):
    return 1 + (fg + 1) * N_COLOR_BASE + bg + 1


def color_from_pair(fg, bg):
    return curses.color_pair(pair_to_index(fg, bg))

GLYPH_TABLE = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', #  0-11
    'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', # 12-23
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', # 24-35
]
GLYPH_SIZE = len(GLYPH_TABLE)
INDEX_TO_GLYPH = {k: i for i, k in enumerate(GLYPH_TABLE)}

ORD_0 = ord('0')
ORD_9 = ord('9')
ORD_a = ord('a')
ORD_z = ord('z')
ORD_A = ord('A')
ORD_Z = ord('Z')


def index_of_orca_js(c):
    return INDEX_TO_GLYPH.get(c.lower(), -1)


def index_of_orca_c(c):
    ord_c = ord(c)
    if ord_c >= ORD_0 and ord_c <= ORD_9:
        return ord_c - ORD_0
    elif ord_c >= ORD_a and ord_c <= ORD_z:
        return ord_c - ORD_a
    elif ord_c >= ORD_A and ord_c <= ORD_Z:
        return ord_c - ORD_A
    else:
        return 0


index_of = index_of_orca_js


class KrillGrid:
    @classmethod
    def from_path(cls, path):
        raw = orca_format.load_orca_file(path)

        rows = len(raw)
        cols = len(raw[0])
        ret = cls(rows, cols)
        ret._state = raw
        return ret

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        # Raw state of the grid at a given state
        self._state = [
            ["." for _ in range(cols)]
            for _ in range(rows)
        ]

    def iter_rows(self):
        return iter(self._state)

    def peek(self, i, j):
        """ Returns the glyph at the given indices.

        Will return no-op (".") if outside the grid boundaries.
        """
        try:
            return self._state[i][j]
        except IndexError:
            return "."

    def poke(self, i, j, value):
        """ Will set the given value at the given position in the grid.

        Will do nothing if outside the grid boundaries.
        """
        try:
            self._state[i][j] = value
        except IndexError:
            return


def operator_add(grid, i, j):
    a = grid.peek(i, j - 1)
    b = grid.peek(i, j + 1)
    index = index_of(a) + index_of(b)
    value = GLYPH_TABLE[index % GLYPH_SIZE]
    logger.debug("add: %s, %s -> table[%d] = %s", a, b, index, value)
    # FIXME: orca-js seems to have complicated logic about when to upper the
    # output in this case, based on the operator sensitivity and the right
    # operand.
    if b.isupper():
        value = value.upper()
    grid.poke(i + 1, j, value)


def update_grid(grid):
    for i, row in enumerate(grid.iter_rows()):
        for j, c in enumerate(row):
            if c == ".":
                continue
            elif c == "A":
                operator_add(grid, i, j)
            else:
                pass


def render_grid(window, grid):
    for i, row in enumerate(grid.iter_rows()):
        window.move(i, 0)
        window.addstr("".join(row))


def main(screen, path):
    grid = KrillGrid.from_path(path)

    top_x = 20
    top_y = 5

    # Must be called before any color setup
    curses.start_color()

    init_colors()

    # +1 as a hack to avoid ERR when writing on lower right corner
    window = curses.newwin(grid.rows, grid.cols + 1, top_y, top_x)
    window.keypad(True)

    cursor = Cursor(0, 0, grid.rows, grid.cols)

    def clear_window():
        for i in range(grid.rows):
            window.move(i, 0)
            window.addstr(" " * grid.cols)

    def draw_cursor(cursor):
        window.move(cursor.y, cursor.x)
        window.addch(
            CURSOR_GLYPH,
            curses.A_REVERSE | curses.A_BOLD
            | color_from_pair(CursesColor.YELLOW, CursesColor.DEFAULT)
        )

    clear_window()

    screen.addstr(0, 0, f"Cursor new pos: {cursor.x, cursor.y}")
    screen.refresh()

    update_grid(grid)
    render_grid(window, grid)
    draw_cursor(cursor)

    window.refresh()

    while True:
        k = window.getch()
        if k == curses.KEY_UP:
            cursor.move_up()
        elif k == curses.KEY_DOWN:
            cursor.move_down()
        elif k == curses.KEY_LEFT:
            cursor.move_left()
        elif k == curses.KEY_RIGHT:
            cursor.move_right()
        else:
            pass

        screen.addstr(0, 0, f"Cursor new pos: {cursor.x, cursor.y}")
        screen.refresh()

        clear_window()

        update_grid(grid)
        render_grid(window, grid)
        draw_cursor(cursor)

        window.refresh()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, filename="curses-ui.log")
    screen = curses.initscr()

    try:
        # Do not echo typed keys into window
        with noecho():
            # Receive arrow keys, etc.
            with keypad(screen):
                # Hide cursor
                curses.curs_set(0)
                main(screen, sys.argv[1])
                curses.napms(2000)
    finally:
        curses.endwin()
