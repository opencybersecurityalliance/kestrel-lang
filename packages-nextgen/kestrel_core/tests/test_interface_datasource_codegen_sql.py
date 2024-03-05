from datetime import datetime
from dateutil import parser

from kestrel.interface.codegen.sql import SqlTranslator
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
)

# Use sqlite3 for testing
import sqlalchemy

import pytest


def _dt(timestr: str) -> datetime:
    return parser.parse(timestr)


def _time2string(ts: datetime) -> str:
    return ts.strftime('%Y-%m-%dT%H:%M:%S.%f')


def _remove_nl(s):
    return s.replace('\n', '')


@pytest.mark.parametrize(
    "iseq, sql", [
        # Try a simple filter
        ([Filter(IntComparison('foo', NumCompOp.GE, 0))],
         "SELECT * FROM my_table WHERE foo >= ?"),
        # Try a simple filter with sorting
        ([Filter(IntComparison('foo', NumCompOp.GE, 0)), Sort('bar')],
         "SELECT * FROM my_table WHERE foo >= ? ORDER BY bar DESC"),
        # Simple filter plus time range
        ([Filter(IntComparison('foo', NumCompOp.GE, 0), timerange=TimeRange(_dt('2023-12-06T08:17:00Z'), _dt('2023-12-07T08:17:00Z')))],
         "SELECT * FROM my_table WHERE foo >= ? AND timestamp >= ? AND timestamp < ?"),
        # sqlalchemy's sqlite dialect seems to always add the offset
        ([Limit(3), ProjectAttrs(['foo', 'bar', 'baz']), Filter(StrComparison('foo', StrCompOp.EQ, 'abc'))],
         "SELECT foo, bar, baz FROM my_table WHERE foo = ? LIMIT ? OFFSET ?"),
        # Same as above but reverse order
        ([Filter(StrComparison('foo', StrCompOp.EQ, 'abc')), ProjectAttrs(['foo', 'bar', 'baz']), Limit(3)],
         "SELECT foo, bar, baz FROM my_table WHERE foo = ? LIMIT ? OFFSET ?"),
        ([Filter(ListComparison('foo', ListOp.NIN, ['abc', 'def']))],
         "SELECT * FROM my_table WHERE (foo NOT IN (__[POSTCOMPILE_foo_1]))"), # POSTCOMPILE is some SQLAlchemy-ism
        ([Filter(StrComparison('foo', StrCompOp.MATCHES, '.*abc.*'))],
         "SELECT * FROM my_table WHERE foo REGEXP ?"),
        ([Filter(StrComparison('foo', StrCompOp.NMATCHES, '.*abc.*'))],
         "SELECT * FROM my_table WHERE foo NOT REGEXP ?"),
        ([Filter(MultiComp(ExpOp.OR, [IntComparison('foo', NumCompOp.EQ, 1), IntComparison('bar', NumCompOp.EQ, 1)]))],
         "SELECT * FROM my_table WHERE foo = ? OR bar = ?"),
        ([Filter(MultiComp(ExpOp.AND, [IntComparison('foo', NumCompOp.EQ, 1), IntComparison('bar', NumCompOp.EQ, 1)]))],
         "SELECT * FROM my_table WHERE foo = ? AND bar = ?"),
        ([Limit(1000), Offset(2000)],
         "SELECT * FROM my_table LIMIT ? OFFSET ?"),
    ]
)
def test_sql_translator(iseq, sql):
    trans = SqlTranslator(sqlalchemy.dialects.sqlite.dialect(), _time2string, "timestamp", sqlalchemy.table("my_table"))
    for i in iseq:
        trans.add_instruction(i)
    result = trans.result()
    assert _remove_nl(str(result)) == sql
