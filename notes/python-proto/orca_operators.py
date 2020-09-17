import abc
import logging
import math


from orca_utils import (
    BANG_GLYPH, DOT_GLYPH, glyph_table_index_of, glyph_table_value_at
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
    @abc.abstractmethod
    def run(self, frame):
        pass

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
    def __init__(self, grid, x, y, passive=False):
        self.x = x
        self.y = y

        self.ports = {
            "a": InputPort(x - 1, y),
            "b": InputPort(x + 1, y),
            "output": OutputPort(x, y + 1, sensitive=True)
        }

        self._grid = grid

    def run(self, frame):
        a_port = self.ports["a"]
        b_port = self.ports["b"]

        index = (
            self.listen(self.ports["a"], True) + self.listen(self.ports["b"], True)
        )
        return glyph_table_value_at(index)



class Clock(IOperator):
    def __init__(self, grid, x, y, passive=False):
        self.x = x
        self.y = y

        self.ports = {
            "rate": InputPort(x - 1, y, clamp=lambda x: max(1, x)),
            "mod": InputPort(x + 1, y, default='8'),
            "output": OutputPort(x, y + 1, sensitive=True)
        }

        self._grid = grid

    def run(self, frame):
        rate = self.listen(self.ports["rate"], True)
        mod = self.listen(self.ports["mod"], True)

        output = math.floor(frame / rate) % mod
        return glyph_table_value_at(output)


_CHAR_TO_OPERATOR_CLASS = {
    "a": Add,
    "c": Clock,
}


def operator_factory(grid, grid_char, x, y):
    """Factory for operators.

    Note: it will return None if no Operator class is found.
    """
    klass =  _CHAR_TO_OPERATOR_CLASS.get(grid_char.lower())
    if klass is not None:
        return klass(grid, x, y, grid_char.isupper())
    else:
        return None


def default_clamp(v):
    return v


