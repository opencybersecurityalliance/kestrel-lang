# parse Kestrel syntax, apply frontend mapping, transform to IR

from lark import Lark

from kestrel.frontend.compile import _KestrelT
from kestrel.utils import load_data_file


# Create a single, reusable transformer
_parser = Lark(
    load_data_file("kestrel.frontend", "kestrel.lark"),
    parser="lalr",
    transformer=_KestrelT(),
)


def parse_kestrel(stmts):
    return _parser.parse(stmts)
