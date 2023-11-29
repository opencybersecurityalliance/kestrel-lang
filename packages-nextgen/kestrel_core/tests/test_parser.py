from datetime import datetime, timedelta, timezone

from kestrel.frontend.parser import parse_kestrel
from kestrel.ir.graph import IRGraph
from kestrel.ir.instructions import Filter, ProjectEntity, Source, Variable, Limit

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
