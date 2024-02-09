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
    ProjectAttrs,
    ProjectEntity,
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
         "SELECT * FROM my_table WHERE foo >= 0"),
        # Simple filter plus time range
        ([Filter(IntComparison('foo', NumCompOp.GE, 0), timerange=TimeRange(_dt('2023-12-06T08:17:00Z'), _dt('2023-12-07T08:17:00Z')))],
         "SELECT * FROM my_table WHERE foo >= 0 AND timestamp >= '2023-12-06T08:17:00.000000Z' AND timestamp < '2023-12-07T08:17:00.000000Z'"),
        # Add a limit and projection
        ([Limit(3), ProjectAttrs(['foo', 'bar', 'baz']), Filter(StrComparison('foo', StrCompOp.EQ, 'abc'))],
         "SELECT foo, bar, baz FROM my_table WHERE foo = 'abc' LIMIT 3"),
        # Same as above but reverse order
        ([Filter(StrComparison('foo', StrCompOp.EQ, 'abc')), ProjectAttrs(['foo', 'bar', 'baz']), Limit(3)],
         "SELECT foo, bar, baz FROM my_table WHERE foo = 'abc' LIMIT 3"),
        ([Filter(ListComparison('foo', ListOp.NIN, ['abc', 'def']))],
         "SELECT * FROM my_table WHERE foo NOT IN ('abc', 'def')"),
        ([Filter(StrComparison('foo', StrCompOp.MATCHES, '.*abc.*'))],
         "SELECT * FROM my_table WHERE foo REGEXP '.*abc.*'"),
        ([Filter(StrComparison('foo', StrCompOp.NMATCHES, '.*abc.*'))],
         "SELECT * FROM my_table WHERE foo NOT REGEXP '.*abc.*'"),
        ([Filter(MultiComp(ExpOp.OR, [IntComparison('foo', NumCompOp.EQ, 1), IntComparison('bar', NumCompOp.EQ, 1)]))],
         "SELECT * FROM my_table WHERE foo = 1 OR bar = 1"),
        ([Filter(MultiComp(ExpOp.AND, [IntComparison('foo', NumCompOp.EQ, 1), IntComparison('bar', NumCompOp.EQ, 1)]))],
         "SELECT * FROM my_table WHERE foo = 1 AND bar = 1"),
    ]
)
def test_opensearch_translator(iseq, sql):
    trans = OpenSearchTranslator(TIMEFMT, "timestamp", "my_table")
    for i in iseq:
        trans.add_instruction(i)
    result = trans.result()
    assert _remove_nl(str(result)) == sql
