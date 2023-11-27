# parse Kestrel syntax, apply frontend mapping, transform to IR

from kestrel.frontend.compile import _KestrelT
from kestrel.utils import load_data_file
from lark import Lark
import logging
import os
import yaml

_logger = logging.getLogger(__name__)

frontend_mapping = {}


def get_mapping(mapping_type, mapping_package, mapping_filepath):
    global frontend_mapping
    mapping = frontend_mapping.get(mapping_type)
    if mapping is not None:
        return mapping
    try:
        mapping_str = load_data_file(mapping_package, mapping_filepath)
        mapping = yaml.safe_load(mapping_str)
        frontend_mapping[mapping_type] = mapping
        _logger.info(f"Loaded {mapping_type} mapping "
                     f"{mapping_package}.{mapping_filepath}")
    except Exception as ex:
        _logger.error(f"Failed to load {mapping_type} mapping "
                      f"{mapping_package}.{mapping_filepath}: {ex}")
        mapping = None
    return mapping


# Create a single, reusable transformer
_parser = Lark(
    load_data_file("kestrel.frontend", "kestrel.lark"),
    parser="lalr",
    transformer=_KestrelT(
        entity_map=get_mapping(
            "entity",
            "kestrel.frontend",
            os.path.join("mapping", "entity", "stix.yaml")),
        property_map=get_mapping(
            "property",
            "kestrel.frontend",
            os.path.join("mapping", "property", "stix.yaml"))
    ),
)


def parse_kestrel(stmts):
    return _parser.parse(stmts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parse_tree = parse_kestrel("x = GET thing FROM if://ds WHERE foo = 'bar'")
    _logger.info(f"{parse_tree.to_json()}")
    parse_tree = parse_kestrel(
        "x = GET process FROM if://ds WHERE process:binary_ref.name = 'foo'")
    _logger.info(f"{parse_tree.to_json()}")
    parse_tree = parse_kestrel(
        "x = GET ipv4-addr FROM if://ds WHERE ipv4-addr:value = '192.168.22.3'")
    _logger.info(f"{parse_tree.to_json()}")
