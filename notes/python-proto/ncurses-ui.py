import contextlib
import curses
import dataclasses
import enum
import logging
import sys

import krill_grid
import orca_operators
import orca_utils

from orca_utils import (
    CROSS_GLYPH, CURSOR_GLYPH, DOT_GLYPH, EMPTY_GLYPH, glyph_table_index_of,
    glyph_table_value_at
)

logger = logging.getLogger(__name__)


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


def operator_add(grid, i, j):
    a = grid.peek(i, j - 1)
    b = grid.peek(i, j + 1)
    index = glyph_table_index_of(a) + glyph_table_index_of(b)
    value = glyph_table_value_at(index)

    logger.debug("add: %s, %s -> table[%d] = %s", a, b, index, value)

    # FIXME: orca-js seems to have complicated logic about when to upper the
    # output in this case, based on the operator sensitivity and the right
    # operand.
    if b.isupper():
        value = value.upper()
    grid.poke(i + 1, j, value)


def parse_grid(grid):
    operators = []
    for y, row in enumerate(grid.iter_rows()):
        for x, c in enumerate(row):
            if c != DOT_GLYPH:
                operator = orca_operators.operator_factory(grid, c, x, y)
                if operator is not None:
                    operators.append(operator)
                else:
                    logger.debug("No operator found for glyph %r", c)

    return operators


def update_grid(grid, frame):
    grid.reset_locks()

    operators = parse_grid(grid)
    logger.debug("Found %d operators", len(operators))

    for operator in operators:
        logger.debug("Looking at operator %s, pos %d, %d", operator, operator.x, operator.y)
        if grid.is_locked(operator.x, operator.y):
            logger.debug("operator %s @ %d, %d is locked", operator, operator.x, operator.y)
            continue
        operator.run(frame)


def render_grid(window, grid):
    for i, row in enumerate(grid.iter_rows()):
        window.move(i, 0)
        rendered_row = (
            c if c != DOT_GLYPH else EMPTY_GLYPH
            for c in row
        )
        window.addstr("".join(rendered_row))


def main(screen, path):
    grid = krill_grid.KrillGrid.from_path(path)

    top_x = 20
    top_y = 5

    frame = 0

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

    def render_top_banner():
        screen.addstr(0, 0, f"Cursor new pos: {cursor.x, cursor.y}")
        screen.addstr(1, 0, f"Frame: {frame}")

    clear_window()

    render_top_banner()
    screen.refresh()

    render_grid(window, grid)
    draw_cursor(cursor)

    window.refresh()

    while True:
        k = window.getch()
        if k == ord(" "):
            frame += 1
            logging.debug("Frame %r", frame)
            update_grid(grid, frame)
        elif k == curses.KEY_UP:
            cursor.move_up()
        elif k == curses.KEY_DOWN:
            cursor.move_down()
        elif k == curses.KEY_LEFT:
            cursor.move_left()
        elif k == curses.KEY_RIGHT:
            cursor.move_right()
        else:
            pass

        render_top_banner()
        screen.refresh()

        clear_window()

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
