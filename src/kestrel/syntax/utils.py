from lark import Lark
from pkgutil import get_data
from itertools import chain

from kestrel.codegen.relations import all_relations


def get_keywords():
    grammar = get_data(__name__, "kestrel.lark").decode("utf-8")
    parser = Lark(grammar, parser="lalr")
    alphabet_patterns = filter(lambda x: x.pattern.value.isalnum(), parser.terminals)
    keywords = [x.pattern.value for x in alphabet_patterns] + all_relations
    keywords_lower = map(lambda x: x.lower(), keywords)
    keywords_upper = map(lambda x: x.upper(), keywords)
    keywords_comprehensive = list(chain(keywords_lower, keywords_upper))
    return keywords_comprehensive
