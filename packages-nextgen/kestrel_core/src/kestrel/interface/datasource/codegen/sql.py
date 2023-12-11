from typing import Callable

from sqlalchemy import and_, column, not_, or_, select, table
from sqlalchemy.engine import Compiled, default
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList
from sqlalchemy.sql.expression import ColumnOperators
from sqlalchemy.sql.selectable import Select
from typeguard import typechecked

from kestrel.ir.filter import (
    BoolExp,
    ExpOp,
    FComparison,
    ListOp,
    NumCompOp,
    StrComparison,
    StrCompOp,
)
from kestrel.ir.instructions import (
    DataSource,
    Filter,
    Instruction,
    Limit,
    ProjectAttrs,
    ProjectEntity,
)


# SQLAlchemy comparison operator functions
comp2func = {
    NumCompOp.EQ: ColumnOperators.__eq__,
    NumCompOp.NEQ: ColumnOperators.__ne__,
    NumCompOp.LT: ColumnOperators.__lt__,
    NumCompOp.LE: ColumnOperators.__le__,
    NumCompOp.GT: ColumnOperators.__gt__,
    NumCompOp.GE: ColumnOperators.__ge__,
    StrCompOp.EQ: ColumnOperators.__eq__,
    StrCompOp.NEQ: ColumnOperators.__ne__,
    StrCompOp.LIKE: ColumnOperators.like,
    StrCompOp.NLIKE: ColumnOperators.not_like,
    StrCompOp.MATCHES: ColumnOperators.regexp_match,
    StrCompOp.NMATCHES: ColumnOperators.regexp_match,  # Caller must negate
    ListOp.IN: ColumnOperators.in_,
    ListOp.NIN: ColumnOperators.not_in,
}


@typechecked
def _render_comp(comp: FComparison) -> BinaryExpression:
    col = column(comp.field)
    if comp.op == StrCompOp.NMATCHES:
        return ~comp2func[comp.op](col, comp.value)
    return comp2func[comp.op](col, comp.value)


@typechecked
class SqlTranslator:
    def __init__(
        self,
        dialect: default.DefaultDialect,
        timefmt: Callable,
        timestamp: str,
    ):
        # SQLAlchemy Dialect object (e.g. from sqlalchemy.dialects import sqlite; sqlite.dialect())
        self.dialect = dialect

        # Time formatting function for datasource
        self.timefmt = timefmt

        # Primary timestamp field in target table
        self.timestamp = timestamp

        # SQLAlchemy statement object
        self.query: Select = select()  # Dummy default

    def _render_exp(self, exp: BoolExp) -> BooleanClauseList:
        if isinstance(exp.lhs, BoolExp):
            lhs = self._render_exp(exp.lhs)
        else:
            lhs = _render_comp(exp.lhs)
        if isinstance(exp.rhs, BoolExp):
            rhs = self._render_exp(exp.rhs)
        else:
            rhs = _render_comp(exp.rhs)
        return and_(lhs, rhs) if exp.op == ExpOp.AND else or_(lhs, rhs)

    def add_DataSource(self, source: DataSource) -> None:
        self.query = self.query.select_from(table(source.datasource))

    def add_Filter(self, filt: Filter) -> None:
        if filt.timerange.start:
            # Convert the timerange to the appropriate pair of comparisons
            start_comp = StrComparison(
                self.timestamp, ">=", self.timefmt(filt.timerange.start)
            )
            stop_comp = StrComparison(
                self.timestamp, "<", self.timefmt(filt.timerange.stop)
            )
            # AND them together
            time_exp = BoolExp(start_comp, ExpOp.AND, stop_comp)
            # AND that with any existing filter expression
            exp = BoolExp(filt.exp, ExpOp.AND, time_exp)
        else:
            exp = filt.exp
        if isinstance(exp, BoolExp):
            comp = self._render_exp(exp)
        else:
            comp = _render_comp(exp)
        self.query = self.query.where(comp)

    def add_ProjectAttrs(self, proj: ProjectAttrs) -> None:
        cols = [column(col) for col in proj.attrs]
        self.query = self.query.with_only_columns(*cols)  # TODO: mapping?

    def add_ProjectEntity(self, proj: ProjectEntity) -> None:
        self.query = self.query.with_only_columns(
            column(proj.entity_type)
        )  # TODO: mapping?

    def add_Limit(self, lim: Limit) -> None:
        self.query = self.query.limit(lim.num)

    def add_instruction(self, i: Instruction) -> None:
        inst_name = i.instruction
        method_name = f"add_{inst_name}"
        method = getattr(self, method_name)
        if not method:
            raise NotImplementedError(f"SqlTranslator.{method_name}")
        method(i)

    def result(self) -> Compiled:
        # If there was no projection, we need to add '*' explicitly
        if len(self.query.selected_columns) == 0:
            self.query = self.query.with_only_columns("*")
        return self.query.compile(
            dialect=self.dialect, compile_kwargs={"render_postcompile": True}
        )
