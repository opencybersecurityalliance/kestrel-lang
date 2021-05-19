from lark import Lark, Visitor, UnexpectedCharacters, UnexpectedToken
from collections import defaultdict

from kestrel.exceptions import InvalidStixPattern
from firepit.stix20 import get_grammar


def parse_extended_stix_pattern(pattern):
    grammar = get_grammar()
    try:
        ast = Lark(grammar, parser="lalr").parse(pattern)
    except UnexpectedCharacters as err:
        raise InvalidStixPattern(pattern, err.line, err.column, "character", err.char)
    except UnexpectedToken as err:
        raise InvalidStixPattern(pattern, err.line, err.column, "token", err.token)
    retor = ReferenceExtractor()
    retor.visit(ast)
    return retor.references


class ReferenceExtractor(Visitor):
    def __init__(self):
        self.references = defaultdict(list)
        super().__init__()

    def reference(self, tree):
        varname = tree.children[0].value
        attribute = tree.children[1].value
        self.references[varname].append(attribute)
