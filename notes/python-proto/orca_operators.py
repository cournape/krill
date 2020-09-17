class IPort:
    pass


class InputPort(IPort):
    def __init__(self, x, y, *, clamp=None):
        self._x = x
        self._y = y

        self.clamp = clamp or default_clamp


class OutputPort(IPort):
    def __init__(self, x, y, *, clamp=None, sensitive=False):
        self._x = x
        self._y = y

        self.clamp = clamp or default_clamp

        self.sensitive = sensitive


class IOperator:
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


_CHAR_TO_OPERATOR_CLASS = {
    "a": Add
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


