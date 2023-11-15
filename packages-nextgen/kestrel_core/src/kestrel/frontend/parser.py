# parse Kestrel syntax, apply frontend mapping, transform to IR

import os

from lark import Lark

from kestrel.frontend.compile import _KestrelT


# Create a single, reusable transformer
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "kestrel.lark"), "r"
) as fp:
    _parser = Lark(fp, parser="lalr", transformer=_KestrelT())


def parse_kestrel(stmts):
    return _parser.parse(stmts)
