import contextlib
import dataclasses

import curses


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


def main(screen):
    rows = 10
    cols = 10

    top_x = 20
    top_y = 5

    #msg = "Type any char to fill the window:"
    #screen.addstr(msg)
    #screen.refresh()

    #fill_char = screen.getch()

    #grid = [
    #    [None for _ in range(cols)]
    #    for _ in range(rows)
    #]
    #for i in range(rows):
    #    for j in range(cols):
    #        if (i + j) % 2 == 0:
    #            c = fill_char
    #        else:
    #            c = " "
    #        grid[i][j] = c

    # +1 as a hack to avoid ERR when writing on lower right corner
    window = curses.newwin(rows, cols + 1, top_y, top_x)
    window.keypad(True)

    cursor = Cursor(0, 0, rows, cols)

    def clear_window():
        window.move(0, 0)
        for _ in range(rows):
            window.addstr(" " * cols)

    def draw_cursor(cursor):
        window.move(cursor.y, cursor.x)
        window.addch(CURSOR_GLYPH)

    clear_window()

    screen.addstr(0, 0, f"Cursor new pos: {cursor.x, cursor.y}")
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
