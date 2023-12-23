# parse Kestrel syntax, apply frontend mapping, transform to IR

from itertools import chain

from kestrel.frontend.compile import _KestrelT
from kestrel.utils import load_data_file
from lark import Lark
import os
from typeguard import typechecked
import yaml

frontend_mapping = {}


@typechecked
def get_mapping(mapping_type: str, mapping_package: str, mapping_filepath: str) -> dict:
    global frontend_mapping
    mapping = frontend_mapping.get(mapping_type)
    if mapping is not None:
        return mapping
    try:
        mapping_str = load_data_file(mapping_package, mapping_filepath)
        mapping = yaml.safe_load(mapping_str)
        frontend_mapping[mapping_type] = mapping
    except Exception as ex:
        mapping = None
    return mapping


@typechecked
def get_keywords():
    # TODO: this Kestrel1 code needs to be updated
    grammar = load_data_file("kestrel.frontend", "kestrel.lark")
    parser = Lark(grammar, parser="lalr")
    alphabet_patterns = filter(lambda x: x.pattern.value.isalnum(), parser.terminals)
    # keywords = [x.pattern.value for x in alphabet_patterns] + all_relations
    keywords = [x.pattern.value for x in alphabet_patterns]
    keywords_lower = map(lambda x: x.lower(), keywords)
    keywords_upper = map(lambda x: x.upper(), keywords)
    keywords_comprehensive = list(chain(keywords_lower, keywords_upper))
    return keywords_comprehensive


# Create a single, reusable transformer
_parser = Lark(
    load_data_file("kestrel.frontend", "kestrel.lark"),
    parser="lalr",
    transformer=_KestrelT(
        entity_map=get_mapping(
            "entity", "kestrel.mapping", os.path.join("entityname", "stix.yaml")
        ),
        property_map=get_mapping(
            "property", "kestrel.mapping", os.path.join("entityattribute", "stix.yaml")
        ),
    ),
)


def parse_kestrel(stmts):
    return _parser.parse(stmts)
