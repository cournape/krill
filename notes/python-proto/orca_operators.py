import abc
import logging
import math


from orca_utils import (
    BANG_GLYPH, COMMENT_GLYPH, DOT_GLYPH, EMPTY_GLYPH, glyph_table_index_of,
    glyph_table_value_at
)


logger = logging.getLogger("operators")


class IPort:
    pass


class InputPort(IPort):
    def __init__(self, x, y, *, clamp=None, default=None):
        self.x = x
        self.y = y

        self.clamp = clamp or default_clamp
        self.default = default


class OutputPort(IPort):
    def __init__(self, x, y, *, clamp=None, sensitive=False, bang=False):
        self.x = x
        self.y = y

        self.clamp = clamp or default_clamp

        self.is_sensitive = sensitive

        self.is_bang = bang


class IOperator(abc.ABC):
    def __init__(self, grid, x, y, *, glyph=DOT_GLYPH, passive=False):
        self.x = x
        self.y = y

        self.ports = {}

        self._grid = grid

        self.is_passive = passive
        self.do_draw = passive

        self.glyph = glyph.upper() if passive else glyph

    @abc.abstractmethod
    def operation(self, frame, force=False):
        pass

    def erase(self):
        self._grid.poke(self.x, self.y, EMPTY_GLYPH)

    def explode(self):
        self._grid.poke(self.x, self.y, BANG_GLYPH)

    def move(self, offset_x, offset_y):
        new_x = self.x + offset_x
        new_y = self.y + offset_x
        if not self._grid.is_inside(new_x, new_y):
            self.explode()
            return

        collider = self._grid.peek(new_x, new_y)
        if collider not in (BANG_GLYPH, DOT_GLYPH):
            self.explode()
            return

        # Erase
        self._grid.poke(self.x, self.y, DOT_GLYPH)
        # Change coordinates
        self.x += offset_x
        self.y += offset_y
        # Redraw at new pos
        self._grid.poke(self.x, self.y, self.glyph)
        if self._grid.is_inside(self.x, self.y):
            self._grid.lock(self.x, self.y)

    def run(self, frame, force=False):
        payload = self.operation(frame, force)

        for port in self.ports.values():
            if isinstance(port, OutputPort) and port.is_bang:
                continue
            logger.debug("Ops %d, %d: locking port @ %d, %d", self.x, self.y, port.x, port.y)
            self._grid.lock(port.x, port.y)

        if "output" in self.ports:
            output_port = self.ports["output"]
            if output_port.is_bang:
                raise ValueError("Output bang not implemented yet")
            else:
                # FIXME: orca-js seems to have complicated logic about when to upper the
                # output in this case, based on the operator sensitivity and the right
                # operand (operator.shouldUpperCase method)
                if output_port.is_sensitive:
                    right_port = InputPort(self.x + 1 ,self.y)
                    right_operand = self.listen(right_port)
                    if right_operand.isupper():
                        payload = payload.upper()
                self._grid.poke(port.x, port.y, payload)

    def listen(self, port, to_value=False):
        glyph = self._grid.peek(port.x, port.y)
        if glyph in (DOT_GLYPH, BANG_GLYPH) and port.default is not None:
            value = port.default
        else:
            value = glyph

        if to_value:
            return port.clamp(glyph_table_index_of(value))
        else:
            return value


class Add(IOperator):
    def __init__(self, grid, x, y, *, passive=False):
        super().__init__(grid, x, y, glyph="a", passive=passive)

        self.ports.update({
            "a": InputPort(x - 1, y),
            "b": InputPort(x + 1, y),
            "output": OutputPort(x, y + 1, sensitive=True)
        })

    def operation(self, frame, force=False):
        a_port = self.ports["a"]
        b_port = self.ports["b"]

        index = (
            self.listen(self.ports["a"], True) + self.listen(self.ports["b"], True)
        )
        return glyph_table_value_at(index)


class Bang(IOperator):
    def __init__(self, grid, x, y, *, passive=False):
        super().__init__(grid, x, y, glyph=BANG_GLYPH, passive=passive)
        self.do_draw = False

    def operation(self, frame, force=False):
        self.do_draw = False
        self.erase()


class Clock(IOperator):
    def __init__(self, grid, x, y, *, passive=False):
        super().__init__(grid, x, y, glyph="c", passive=passive)

        self.ports.update({
            "rate": InputPort(x - 1, y, clamp=lambda x: max(1, x)),
            "mod": InputPort(x + 1, y, default='8'),
            "output": OutputPort(x, y + 1, sensitive=True)
        })

    def operation(self, frame, force=False):
        rate = self.listen(self.ports["rate"], True)
        mod = self.listen(self.ports["mod"], True)

        output = math.floor(frame / rate) % mod
        return glyph_table_value_at(output)


class Comment(IOperator):
    def __init__(self, grid, x, y, *, passive=False):
        super().__init__(grid, x, y, glyph=COMMENT_GLYPH, passive=passive)
        self.do_draw = False

    def operation(self, frame, force=False):
        self._grid.lock(self.x, self.y)
        for x in range(self.x + 1, self._grid.cols):
            self._grid.lock(x, self.y)
            if self._grid.peek(x, self.y) == self.glyph:
                break


class East(IOperator):
    def __init__(self, grid, x, y, *, passive=False):
        super().__init__(grid, x, y, glyph="e", passive=passive)
        self.do_draw = False

    def operation(self, frame, force=False):
        self.move(1, 0)


_CHAR_TO_OPERATOR_CLASS = {
    "a": Add,
    "c": Clock,
    "e": East,
    BANG_GLYPH: Bang,
    COMMENT_GLYPH: Comment,
}


def operator_factory(grid, grid_char, x, y):
    """Factory for operators.

    Note: it will return None if no Operator class is found.
    """
    klass =  _CHAR_TO_OPERATOR_CLASS.get(grid_char.lower())
    if klass is not None:
        return klass(grid, x, y, passive=grid_char.isupper())
    else:
        return None


def default_clamp(v):
    return v
