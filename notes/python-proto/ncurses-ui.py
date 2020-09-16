import contextlib
import dataclasses
import enum
import logging

import curses

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
            logger.debug("%d -> {%s:%d, %s:%d}", c, CursesColor(fg), fg, CursesColor(bg), bg)
            curses.init_pair(c, fg, bg)


def pair_to_index(fg, bg):
    return 1 + (fg + 1) * N_COLOR_BASE + bg + 1


def color_from_pair(fg, bg):
    return curses.color_pair(pair_to_index(fg, bg))


def main(screen):
    rows = 10
    cols = 10

    top_x = 20
    top_y = 5

    # Must be called before any color setup
    curses.start_color()

    init_colors()

    # +1 as a hack to avoid ERR when writing on lower right corner
    window = curses.newwin(rows, cols + 1, top_y, top_x)
    window.keypad(True)

    cursor = Cursor(0, 0, rows, cols)

    def clear_window():
        for i in range(rows):
            window.move(i, 0)
            window.addstr(" " * cols)

    def draw_cursor(cursor):
        window.move(cursor.y, cursor.x)
        window.addch(
            CURSOR_GLYPH,
            curses.A_REVERSE | curses.A_BOLD
            | color_from_pair(CursesColor.YELLOW, CursesColor.DEFAULT)
        )

    clear_window()

    screen.addstr(0, 0, f"Cursor new pos: {cursor.x, cursor.y} / color pair: {pair_to_index(curses.COLOR_RED, -1)}")
    screen.refresh()

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
        screen.addstr(1, 0, f"Key pressed: {k} vs {curses.KEY_UP}       ")
        screen.refresh()

        clear_window()
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
                main(screen)
                curses.napms(2000)
    finally:
        curses.endwin()
