from datetime import datetime
from dateutil import parser

from kestrel.interface.datasource.codegen.sql import SqlTranslator
from kestrel.ir.filter import (
    BoolExp,
    ExpOp,
    FComparison,
    IntComparison,
    ListOp,
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

# Use sqlite3 for testing
from sqlalchemy.dialects import sqlite

import pytest


def _dt(timestr: str) -> datetime:
    return parser.parse(timestr)


def _time2string(ts: datetime) -> str:
    return ts.strftime('%Y-%m-%dT%H:%M:%S.%f')


def _remove_nl(s):
    return s.replace('\n', '')


@pytest.mark.parametrize(
    "iseq, sql", [
        ([DataSource(interface='sqlite3', datasource='my_table')],
         "SELECT * FROM my_table"),
        # Try a simple filter
        ([Filter(IntComparison('foo', NumCompOp.GE, 0)), DataSource(interface='sqlite3', datasource='my_table')],
         "SELECT * FROM my_table WHERE foo >= ?"),
        # Simple filter plus time range
        ([Filter(IntComparison('foo', NumCompOp.GE, 0), timerange=TimeRange(_dt('2023-12-06T08:17:00Z'), _dt('2023-12-07T08:17:00Z'))),
          DataSource(interface='sqlite3', datasource='my_table')],
         "SELECT * FROM my_table WHERE foo >= ? AND timestamp >= ? AND timestamp < ?"),
        # Time range only, no other field comparisons  <- Not valid?
        #([Filter(timerange=TimeRange(_dt('2023-12-06T08:17:00Z'), _dt('2023-12-07T08:17:00Z'))),
        #  DataSource(interface='sqlite3', datasource='my_table')],
        # "SELECT * FROM my_table WHERE timestamp >= ? AND timestamp < ?"),
        # sqlalchemy's sqlite dialect seems to always add the offset
        ([Limit(3), ProjectAttrs(['foo', 'bar', 'baz']), Filter(StrComparison('foo', StrCompOp.EQ, 'abc')), DataSource(interface='sqlite3', datasource='my_table')],
         "SELECT foo, bar, baz FROM my_table WHERE foo = ? LIMIT ? OFFSET ?"),
        # Same as above but reverse order
        ([DataSource(interface='sqlite3', datasource='my_table'), Filter(StrComparison('foo', StrCompOp.EQ, 'abc')), ProjectAttrs(['foo', 'bar', 'baz']), Limit(3)],
         "SELECT foo, bar, baz FROM my_table WHERE foo = ? LIMIT ? OFFSET ?"),
    ]
)
def test_sql_translator(iseq, sql):
    trans = SqlTranslator(sqlite.dialect(), _time2string, 'timestamp')
    for i in iseq:
        trans.add_instruction(i)
    result = trans.result()
    assert _remove_nl(str(result)) == sql
