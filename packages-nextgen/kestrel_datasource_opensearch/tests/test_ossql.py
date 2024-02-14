from datetime import datetime
from dateutil import parser

from kestrel_datasource_opensearch.ossql import OpenSearchTranslator
from kestrel.ir.filter import (
    BoolExp,
    ExpOp,
    FComparison,
    IntComparison,
    ListOp,
    ListComparison,
    MultiComp,
    NumCompOp,
    StrCompOp,
    StrComparison,
    TimeRange,
)
from kestrel.ir.instructions import (
    DataSource,
    Filter,
    Limit,
    Offset,
    ProjectAttrs,
    ProjectEntity,
    Sort,
    SortDirection,
)

import pytest


TIMEFMT = '%Y-%m-%dT%H:%M:%S.%fZ'


def _dt(timestr: str) -> datetime:
    return parser.parse(timestr)


def _remove_nl(s):
    return s.replace('\n', '')


@pytest.mark.parametrize(
    "iseq, sql", [
        # Try a simple filter
        ([Filter(IntComparison('foo', NumCompOp.GE, 0))],
         "SELECT {} FROM my_table WHERE foo >= 0"),
        # Try a simple filter with sorting
        ([Filter(IntComparison('foo', NumCompOp.GE, 0)), Sort('bar')],
         "SELECT {} FROM my_table WHERE foo >= 0 ORDER BY bar DESC"),
        # Simple filter plus time range
        ([Filter(IntComparison('foo', NumCompOp.GE, 0), timerange=TimeRange(_dt('2023-12-06T08:17:00Z'), _dt('2023-12-07T08:17:00Z')))],
         "SELECT {} FROM my_table WHERE foo >= 0 AND timestamp >= '2023-12-06T08:17:00.000000Z' AND timestamp < '2023-12-07T08:17:00.000000Z'"),
        # Add a limit and projection
        ([Limit(3), ProjectAttrs(['foo', 'bar', 'baz']), Filter(StrComparison('foo', StrCompOp.EQ, 'abc'))],
         "SELECT foo, bar, baz FROM my_table WHERE foo = 'abc' LIMIT 3"),
        # Same as above but reverse order
        ([Filter(StrComparison('foo', StrCompOp.EQ, 'abc')), ProjectAttrs(['foo', 'bar', 'baz']), Limit(3)],
         "SELECT foo, bar, baz FROM my_table WHERE foo = 'abc' LIMIT 3"),
        ([Filter(ListComparison('foo', ListOp.NIN, ['abc', 'def']))],
         "SELECT {} FROM my_table WHERE foo NOT IN ('abc', 'def')"),
        ([Filter(StrComparison('foo', StrCompOp.MATCHES, '.*abc.*'))],
         "SELECT {} FROM my_table WHERE foo REGEXP '.*abc.*'"),
        ([Filter(StrComparison('foo', StrCompOp.NMATCHES, '.*abc.*'))],
         "SELECT {} FROM my_table WHERE foo NOT REGEXP '.*abc.*'"),
        ([Filter(MultiComp(ExpOp.OR, [IntComparison('foo', NumCompOp.EQ, 1), IntComparison('bar', NumCompOp.EQ, 1)]))],
         "SELECT {} FROM my_table WHERE foo = 1 OR bar = 1"),
        ([Filter(MultiComp(ExpOp.AND, [IntComparison('foo', NumCompOp.EQ, 1), IntComparison('bar', NumCompOp.EQ, 1)]))],
         "SELECT {} FROM my_table WHERE foo = 1 AND bar = 1"),
        ([Limit(1000), Offset(2000)],
         "SELECT {} FROM my_table LIMIT 2000, 1000"),
        # Test entity projection
        ([Limit(3), Filter(StrComparison('cmd_line', StrCompOp.EQ, 'foo bar')), ProjectEntity('process')],
         "SELECT {} FROM my_table WHERE CommandLine = 'foo bar' LIMIT 3"),
    ]
)
def test_opensearch_translator(iseq, sql):
    data_model_map = {
        "process.cmd_line": "CommandLine",
        "process.file.path": "Image",
        "process.pid": "ProcessId",
        "actor.process.pid": "ParentProcessId",
    }
    schema = {
        "CommandLine": "text",
        "Image": "text",
        "ProcessId": "text",
        "ParentProcessId": "text",
    }
    cols = '`CommandLine` AS `cmd_line`, `Image` AS `file.path`, `ProcessId` AS `pid`'
    if ProjectEntity not in {type(i) for i in iseq}:
        cols += ', `ParentProcessId` AS `process.pid`'
    trans = OpenSearchTranslator(TIMEFMT, "timestamp", "my_table", data_model_map, schema)
    for i in iseq:
        trans.add_instruction(i)
    result = trans.result()
    assert _remove_nl(str(result)) == sql.format(cols)
