from datetime import datetime, timedelta, timezone

from kestrel.frontend.parser import parse_kestrel
from kestrel.ir.graph import IRGraph
from kestrel.ir.instructions import Filter, ProjectEntity, Source, Variable, Limit

import json
import pytest


@pytest.mark.parametrize(
    "stmt", [
        "x = GET thing FROM if://ds WHERE foo = 'bar'",
        "x = GET thing FROM if://ds WHERE foo > 1.5",
        r"x = GET thing FROM if://ds WHERE foo = r'C:\TMP'",
        "x = GET thing FROM if://ds WHERE foo = 'bar' OR baz != 42",
        "x = GET thing FROM if://ds WHERE foo = 'bar' AND baz IN (1, 2, 3)",
        "x = GET thing FROM if://ds WHERE foo = 'bar' AND baz IN (1)",
        "x = GET thing FROM if://ds WHERE foo = 'bar' AND baz IN (1) LAST 3 DAYS",
    ]
)
def test_parser_get_statements(stmt):
    """
    This test isn't meant to be comprehensive, but checks basic transformer functionality.

    This will need to be updated as we build out the new Transformer
    """

    graph = parse_kestrel(stmt)
    assert len(graph) == 4
    assert len(graph.get_nodes_by_type(Variable)) == 1
    assert len(graph.get_nodes_by_type(ProjectEntity)) == 1
    assert len(graph.get_nodes_by_type(Source)) == 1
    assert len(graph.get_nodes_by_type(Filter)) == 1

    # Ensure result is serializable
    _ = graph.to_json()


def test_parser_get_timespan_relative():
    stmt = "x = GET url FROM if://ds WHERE url = 'http://example.com/' LAST 5h"
    graph = parse_kestrel(stmt)
    filt_list = graph.get_nodes_by_type(Filter)
    assert len(filt_list) == 1
    filt = filt_list[0]
    delta = filt.timerange.stop - filt.timerange.start
    assert delta == timedelta(hours=5)


def test_parser_get_timespan_absolute():
    stmt = ("x = GET url FROM if://ds WHERE url = 'http://example.com/'"
            " START '2023-11-29T00:00:00Z' STOP '2023-11-29T05:00:00Z'")
    graph = parse_kestrel(stmt)
    filt_list = graph.get_nodes_by_type(Filter)
    assert len(filt_list) == 1
    filt = filt_list[0]
    delta = filt.timerange.stop - filt.timerange.start
    assert delta == timedelta(hours=5)
    assert filt.timerange.start == datetime(2023, 11, 29, 0, 0, tzinfo=timezone.utc)
    assert filt.timerange.stop == datetime(2023, 11, 29, 5, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "stmt, expected", [
        ("x = GET url FROM if://ds WHERE url = 'http://example.com/' LIMIT 1", 1),
        ("x = GET url FROM if://ds WHERE url = 'http://example.com/' LAST 3d LIMIT 2", 2),
        (("x = GET url FROM if://ds WHERE url = 'http://example.com/'"
          " START '2023-11-29T00:00:00Z' STOP '2023-11-29T05:00:00Z' LIMIT 3"), 3),
    ]
)
def test_parser_get_with_limit(stmt, expected):
    graph = parse_kestrel(stmt)
    limits = graph.get_nodes_by_type(Limit)
    assert len(limits) == 1
    limit = limits[0]
    assert limit.num == expected


def get_parsed_filter_exp(stmt):
    parse_tree = parse_kestrel(stmt)
    parse_tree_string = parse_tree.to_json()
    parse_tree_json = json.loads(parse_tree_string)
    parse_tree_nodes = parse_tree_json.get('nodes', [])
    assert isinstance(parse_tree_nodes, list) and len(parse_tree_nodes) > 1
    parse_filter_exp = parse_tree_nodes[1].get('exp', {})
    return parse_filter_exp


def test_parser_mapping_single_comparison_to_single_value():
    # test for attributes in the form entity_name:property_name
    stmt = "x = GET process FROM if://ds WHERE process:binary_ref.name = 'foo'"
    parse_filter = get_parsed_filter_exp(stmt)
    field = parse_filter.get('field', '')
    assert field == 'file.name'
    # test when entity name is not included in the attributes
    stmt = "x = GET process FROM if://ds WHERE binary_ref.name = 'foo'"
    parse_filter = get_parsed_filter_exp(stmt)
    field = parse_filter.get('field', '')
    assert field == 'file.name'


def test_parser_mapping_single_comparison_to_multiple_values():
    stmt = "x = GET ipv4-addr FROM if://ds WHERE value = '192.168.22.3'"
    parse_filter = get_parsed_filter_exp(stmt)
    comps = parse_filter.get('comps', '')
    assert isinstance(comps, list) and len(comps) == 3
    fields = [x.get('field') for x in comps]
    assert ("dst_endpoint.ip" in fields and "src_endpoint.ip" in fields and
            "device.ip" in fields)


def test_parser_mapping_multiple_comparison_to_multiple_values():
    stmt = "x = GET process FROM if://ds WHERE binary_ref.name = 'foo' "\
        "OR name = 'bam' AND parent_ref.name = 'boom'"
    parse_filter = get_parsed_filter_exp(stmt)
    field1 = parse_filter.get('lhs',{}).get('field', '')
    assert field1 == 'file.name'
    field2 = parse_filter.get('rhs',{}).get('lhs',{}).get('field', '')
    assert field2 == 'process.name'
    comps3 = parse_filter.get('rhs',{}).get('rhs',{}).get('comps', [])
    assert isinstance(comps3, list) and len(comps3) == 2
    fields3 = [x.get('field') for x in comps3]
    assert ("actor.process.name" in fields3 and
            "process.parent_process.name" in fields3)
