import abc
import logging


from orca_utils import glyph_table_index_of, glyph_table_value_at


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
        a = self._grid.peek(a_port.x, a_port.y)
        b = self._grid.peek(b_port.x, b_port.y)

        index = glyph_table_index_of(a) + glyph_table_index_of(b)
        value = glyph_table_value_at(index)

        logger.debug("add: %s, %s -> table[%d] = %s", a, b, index, value)

        # FIXME: orca-js seems to have complicated logic about when to upper the
        # output in this case, based on the operator sensitivity and the right
        # operand.
        if b.isupper():
            value = value.upper()

        output_port = self.ports["output"]
        self._grid.poke(output_port.x, output_port.y, value)


_CHAR_TO_OPERATOR_CLASS = {
    "a": Add,
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


