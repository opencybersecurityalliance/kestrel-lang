import json
import pytest
from datetime import datetime, timedelta, timezone

from kestrel.frontend.parser import parse_kestrel
from kestrel.ir.graph import IRGraph
from kestrel.ir.filter import ReferenceValue
from kestrel.ir.instructions import (
    Construct,
    DataSource,
    Filter,
    Limit,
    Offset,
    ProjectAttrs,
    ProjectEntity,
    Reference,
    Sort,
    Variable,
)


@pytest.mark.parametrize(
    "stmt", [
        "x = GET thing FROM if://ds WHERE foo = 'bar'",
        "x = GET thing FROM if://ds WHERE foo > 0",
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
    assert len(graph.get_nodes_by_type(DataSource)) == 1
    assert len(graph.get_nodes_by_type(Filter)) == 1

    # Ensure result is serializable
    _ = graph.to_json()


def test_parser_get_timespan_relative():
    stmt = "x = GET url FROM if://ds WHERE value = 'http://example.com/' LAST 5h"
    graph = parse_kestrel(stmt)
    filt_list = graph.get_nodes_by_type(Filter)
    assert len(filt_list) == 1
    filt = filt_list[0]
    delta = filt.timerange.stop - filt.timerange.start
    assert delta == timedelta(hours=5)


def test_parser_get_timespan_absolute():
    stmt = ("x = GET url FROM if://ds WHERE value = 'http://example.com/'"
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
        ("x = GET url FROM if://ds WHERE value = 'http://example.com/' LIMIT 1", 1),
        ("x = GET url FROM if://ds WHERE value = 'http://example.com/' LAST 3d LIMIT 2", 2),
        (("x = GET url FROM if://ds WHERE value = 'http://example.com/'"
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
    filter_node = parse_tree.get_nodes_by_type(Filter).pop()
    return filter_node.exp


def test_parser_mapping_single_comparison_to_single_value():
    # test for attributes in the form entity_name:property_name
    stmt = "x = GET process FROM if://ds WHERE process:pid = 123"
    parse_filter = get_parsed_filter_exp(stmt)
    assert parse_filter.field == 'process.pid'
    # test when entity name is not included in the attributes
    stmt = "x = GET process FROM if://ds WHERE pid = 123"
    parse_filter = get_parsed_filter_exp(stmt)
    assert parse_filter.field == 'process.pid'


def test_parser_mapping_single_comparison_to_multiple_values():
    stmt = "x = GET process FROM if://ds WHERE binary_ref.name = 'cmd.exe'"
    parse_filter = get_parsed_filter_exp(stmt)
    comps = parse_filter.comps
    assert isinstance(comps, list) and len(comps) == 2
    fields = [x.field for x in comps]
    assert ("process.file.name" in fields and "process.file.path" in fields)


def test_parser_mapping_multiple_comparison_to_multiple_values():
    stmt = ("x = GET process FROM if://ds"
            " WHERE binary_ref.name = 'name' OR name = 'bam' AND parent_ref.name = 'boom'")
    parse_filter = get_parsed_filter_exp(stmt)
    comps1 = parse_filter.lhs.comps
    assert isinstance(comps1, list) and len(comps1) == 2
    fields1 = [x.field for x in comps1]
    assert ("process.file.name" in fields1 and
            "process.file.path" in fields1)
    field2 = parse_filter.rhs.lhs.field
    assert field2 == 'process.name'
    field3 = parse_filter.rhs.rhs.field
    assert field3 == 'process.parent_process.name'


def test_parser_new_json():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
"""
    graph = parse_kestrel(stmt)
    cs = graph.get_nodes_by_type(Construct)
    assert len(cs) == 1
    construct = cs[0]
    df = [ {"name": "cmd.exe", "pid": 123}
         , {"name": "explorer.exe", "pid": 99}
         , {"name": "firefox.exe", "pid": 201}
         , {"name": "chrome.exe", "pid": 205}
         ]
    assert df == construct.data
    vs = graph.get_variables()
    assert len(vs) == 1
    assert vs[0].name == "proclist"


@pytest.mark.parametrize(
    "stmt, node_cnt", [
        ("x = y WHERE name = 'bar'", 3),
        ("x = y WHERE name > 1.5", 3),
        (r"x = y WHERE name = r'C:\TMP'", 3),
        ("x = y WHERE name = 'bar' OR pid != 42", 3),
        ("x = y WHERE name = 'bar' AND pid IN (1, 2, 3)", 3),
        ("x = y WHERE name = 'bar' AND pid IN (1)", 3),
        ("x = y WHERE name = 'bar' SORT BY name ASC LIMIT 3", 5),
        ("x = y WHERE name = 'bar' SORT BY name ASC LIMIT 3 OFFSET 9", 6),
    ]
)
def test_parser_expression(stmt, node_cnt):
    """
    This test isn't meant to be comprehensive, but checks basic transformer functionality.

    This will need to be updated as we build out the new Transformer
    """

    graph = parse_kestrel(stmt)
    assert len(graph) == node_cnt
    assert len(graph.get_nodes_by_type(Variable)) == 1
    assert len(graph.get_nodes_by_type(Reference)) == 1
    assert len(graph.get_nodes_by_type(Filter)) == 1
    assert len(graph.get_nodes_by_type(Sort)) in (0, 1)
    assert len(graph.get_nodes_by_type(Limit)) in (0, 1)
    assert len(graph.get_nodes_by_type(Offset)) in (0, 1)


def test_three_statements_in_a_line():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name = 'firefox.exe' OR name = 'chrome.exe'
DISP browsers ATTR name, pid
"""
    graph = parse_kestrel(stmt)
    assert len(graph) == 6
    c = graph.get_nodes_by_type(Construct)[0]
    assert {"proclist", "browsers"} == {v.name for v in graph.get_variables()}
    proclist = graph.get_variable("proclist")
    browsers = graph.get_variable("browsers")
    proj = graph.get_nodes_by_type(ProjectAttrs)[0]
    assert proj.attrs == ['name', 'pid']
    ft = graph.get_nodes_by_type(Filter)[0]
    assert ft.exp.to_dict() == {"lhs": {"field": "name", "op": "=", "value": "firefox.exe"}, "op": "OR", "rhs": {"field": "name", "op": "=", "value": "chrome.exe"}}
    ret = graph.get_returns()[0]
    assert len(graph.edges) == 5
    assert (c, proclist) in graph.edges
    assert (proclist, ft) in graph.edges
    assert (ft, browsers) in graph.edges
    assert (browsers, proj) in graph.edges
    assert (proj, ret) in graph.edges


@pytest.mark.parametrize(
    "stmt, node_cnt, expected", [
        ("x = y WHERE foo = z.foo", 5, [ReferenceValue("z", "foo")]),
        ("x = y WHERE foo > 1.5", 3, []),
        ("x = y WHERE foo = 'bar' OR baz = z.baz", 5, [ReferenceValue("z", "baz")]),
        ("x = y WHERE (foo = 'bar' OR baz = z.baz) AND (fox = w.fox AND bbb = z.bbb)", 8, [ReferenceValue("z", "baz"), ReferenceValue("w", "fox"), ReferenceValue("z", "bbb")]),
        ("x = GET process FROM s://x WHERE foo = z.foo", 6, [ReferenceValue("z", "foo")]),
        ("x = GET file FROM s://y WHERE foo > 1.5", 4, []),
        ("x = GET file FROM c://x WHERE foo = 'bar' OR baz = z.baz", 6, [ReferenceValue("z", "baz")]),
        ("x = GET user FROM s://x WHERE (foo = 'bar' OR baz = z.baz) AND (fox = w.fox AND bbb = z.bbb)", 9, [ReferenceValue("z", "baz"), ReferenceValue("w", "fox"), ReferenceValue("z", "bbb")]),
    ]
)
def test_reference_branch(stmt, node_cnt, expected):
    graph = parse_kestrel(stmt)
    assert len(graph) == node_cnt
    filter_nodes = graph.get_nodes_by_type(Filter)
    assert len(filter_nodes) == 1
    filter_node = filter_nodes[0]
    for rv in expected:
        r = graph.get_reference(rv.reference)
        assert r
        projs = [p for p in graph.successors(r) if isinstance(p, ProjectAttrs) and p.attrs == [rv.attribute]]
        assert projs and len(projs) == 1
        proj = projs[0]
        assert proj
        assert list(graph.successors(proj)) == [filter_node]


def test_parser_disp_after_new():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
DISP proclist ATTR name, pid LIMIT 2 OFFSET 3
"""
    graph = parse_kestrel(stmt)
    assert len(graph) == 6
    c = graph.get_nodes_by_type(Construct)[0]
    assert {"proclist"} == {v.name for v in graph.get_variables()}
    proclist = graph.get_variable("proclist")
    proj = graph.get_nodes_by_type(ProjectAttrs)[0]
    assert proj.attrs == ['name', 'pid']
    limit = graph.get_nodes_by_type(Limit)[0]
    assert limit.num == 2
    offset = graph.get_nodes_by_type(Offset)[0]
    assert offset.num == 3
    ret = graph.get_returns()[0]
    assert len(graph.edges) == 5
    assert (c, proclist) in graph.edges
    assert (proclist, proj) in graph.edges
    assert (proj, limit) in graph.edges
    assert (limit, offset) in graph.edges
    assert (offset, ret) in graph.edges
