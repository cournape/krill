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

    top_x = 0
    top_y = 0

    window = curses.newwin(rows, cols, top_y, top_x)
    window.addch(0, 0, "@")

    window.refresh()


if __name__ == "__main__":
    screen = curses.initscr()

    try:
        # Do not echo typed keys into window
        with noecho():
            # Receive arrow keys, etc.
            with keypad(screen):
                main(screen)
                curses.napms(2000)
    finally:
        curses.endwin()
