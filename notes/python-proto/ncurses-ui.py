import contextlib

import curses


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


def main(screen):
    rows = 10
    cols = 10

    top_x = 20
    top_y = 5

    msg = "Type any char to fill the window:"
    screen.addstr(msg)
    screen.refresh()

    fill_char = screen.getch()

    grid = [
        [None for _ in range(cols)]
        for _ in range(rows)
    ]
    for i in range(rows):
        for j in range(cols):
            if (i + j) % 2 == 0:
                c = fill_char
            else:
                c = " "
            grid[i][j] = c

    # +1 as a hack to avoid ERR when writing on lower right corner
    window = curses.newwin(rows, cols + 1, top_y, top_x)

    for i, row in enumerate(grid):
        for j, c in enumerate(row):
            window.addch(i, j, c)

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
