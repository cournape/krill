BANG_GLYPH = "*"
CURSOR_GLYPH = "@"
CROSS_GLYPH = "+"
DOT_GLYPH = "."
COMMENT_GLYPH = "#"
EMPTY_GLYPH = " "

GLYPH_TABLE = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', #  0-11
    'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', # 12-23
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', # 24-35
]
GLYPH_TABLE_SIZE = len(GLYPH_TABLE)
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


glyph_table_index_of = index_of_orca_js


def glyph_table_value_at(index):
    return GLYPH_TABLE[index % GLYPH_TABLE_SIZE]
