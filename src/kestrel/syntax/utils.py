from typeguard import typechecked
from lark import Lark
from pkgutil import get_data
from itertools import chain
from typing import Tuple, Iterable
import datetime
import os

from kestrel.utils import resolve_path
from kestrel.codegen.relations import (
    all_relations,
    stix_2_0_ref_mapping,
    stix_2_0_identical_mapping,
)

LITERALS = {"CNAME", "LETTER", "DIGIT", "WS", "INT", "WORD", "ESCAPED_STRING", "NUMBER"}
AGG_FUNCS = {"MIN", "MAX", "AVG", "SUM", "COUNT", "NUNIQUE"}
EXPRESSION_OPTIONS = {"WHERE", "ATTR", "SORT", "LIMIT", "OFFSET"}
TRANSFORMS = {"TIMESTAMPED", "ADDOBSID", "RECORDS"}


def get_keywords():
    grammar = get_data(__name__, "kestrel.lark").decode("utf-8")
    parser = Lark(grammar, parser="lalr")
    alphabet_patterns = filter(lambda x: x.pattern.value.isalnum(), parser.terminals)
    keywords = [x.pattern.value for x in alphabet_patterns] + all_relations
    keywords_lower = map(lambda x: x.lower(), keywords)
    keywords_upper = map(lambda x: x.upper(), keywords)
    keywords_comprehensive = list(chain(keywords_lower, keywords_upper))
    return keywords_comprehensive


def get_entity_types():
    all_types = {"x-ibm-finding", "x-oca-asset", "x-oca-event"}
    for mapping in stix_2_0_ref_mapping:
        for i in (0, 2):
            if not mapping[i].endswith("-ext"):
                all_types.add(mapping[i])
    all_types.update(stix_2_0_identical_mapping.keys())
    return tuple(all_types)


def get_all_input_var_names(stmt):
    input_refs = ["input", "input_2", "variablesource"]
    inputs_refs = stmt["inputs"] if "inputs" in stmt else []
    return [stmt.get(k) for k in input_refs if k in stmt] + inputs_refs


@typechecked
def merge_timeranges(trs: Iterable[Tuple[datetime.datetime, datetime.datetime]]):
    # return the earliest start time and latest end time
    trs = [tr for tr in trs if tr is not None]
    if trs:
        starts, ends = list(zip(*trs))
        start = min(starts)
        end = max(ends)
        return (start, end)
    else:
        return None


@typechecked
def timedelta_seconds(t: int):
    return datetime.timedelta(seconds=t)


def resolve_uri(uri: str):
    if uri.startswith("file://"):
        path = uri[7:]
        if os.path.exists(path):
            uri = "file://" + resolve_path(path)
    return uri
