from functools import reduce
from typing import Callable, Union

from typeguard import typechecked

from kestrel.ir.filter import (
    BoolExp,
    ExpOp,
    FComparison,
    IntComparison,
    ListComparison,
    ListOp,
    MultiComp,
    NumCompOp,
    StrComparison,
    StrCompOp,
)
from kestrel.ir.instructions import (
    Filter,
    Instruction,
    Limit,
    ProjectAttrs,
    ProjectEntity,
)


Value = Union[
    int,
    float,
    str,
    list,
]


@typechecked
def _and(lhs: str, rhs: Value) -> str:
    return " AND ".join((lhs, rhs))


@typechecked
def _or(lhs: str, rhs: Value) -> str:
    return " OR ".join((lhs, rhs))


# Kusto comparison operator functions
comp2func = {
    NumCompOp.EQ: "=",
    NumCompOp.NEQ: "<>",
    NumCompOp.LT: "<",
    NumCompOp.LE: "<=",
    NumCompOp.GT: ">",
    NumCompOp.GE: ">=",
    StrCompOp.EQ: "=",
    StrCompOp.NEQ: "<>",
    StrCompOp.LIKE: "LIKE",
    StrCompOp.NLIKE: "NOT LIKE",
    StrCompOp.MATCHES: "REGEXP",
    StrCompOp.NMATCHES: "NOT REGEXP",
    ListOp.IN: "IN",
    ListOp.NIN: "NOT IN",
}


@typechecked
def _render_comp(comp: FComparison) -> str:
    if isinstance(comp, StrComparison):
        # Need to quote string values
        value = f"'{comp.value}'"
    elif isinstance(comp, ListComparison):
        # KQL uses parens for lists, like SQL
        value = tuple(comp.value)
    else:
        value = comp.value
    result = f"{comp.field} {comp2func[comp.op]} {value}"
    return result


@typechecked
def _render_multi_comp(comps: MultiComp) -> str:
    op = _and if comps.op == ExpOp.AND else _or
    return reduce(op, map(_render_comp, comps.comps))


@typechecked
class OpenSearchTranslator:
    def __init__(
        self,
        timefmt: Callable,
        timestamp: str,
        select_from: str,
    ):
        # Time formatting function for datasource
        self.timefmt = timefmt

        # Primary timestamp field in target table
        self.timestamp = timestamp

        # Query clauses
        self.table: str = select_from
        self.where: str = ""
        self.project: list[str] = []
        self.limit: int = 0

    def _render_exp(self, exp: BoolExp) -> str:
        if isinstance(exp.lhs, BoolExp):
            lhs = self._render_exp(exp.lhs)
        elif isinstance(exp.lhs, MultiComp):
            lhs = _render_multi_comp(exp.lhs)
        else:
            lhs = _render_comp(exp.lhs)
        if isinstance(exp.rhs, BoolExp):
            rhs = self._render_exp(exp.rhs)
        elif isinstance(exp.rhs, MultiComp):
            rhs = _render_multi_comp(exp.rhs)
        else:
            rhs = _render_comp(exp.rhs)
        return _and(lhs, rhs) if exp.op == ExpOp.AND else _or(lhs, rhs)

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
        elif isinstance(exp, MultiComp):
            comp = _render_multi_comp(exp)
        else:
            comp = _render_comp(exp)
        self.where = comp

    def add_ProjectAttrs(self, proj: ProjectAttrs) -> None:
        cols = [str(col) for col in proj.attrs]
        self.project = cols

    def add_ProjectEntity(self, proj: ProjectEntity) -> None:
        pass  # TODO

    def add_Limit(self, lim: Limit) -> None:
        self.limit = lim.num

    def add_instruction(self, i: Instruction) -> None:
        inst_name = i.instruction
        method_name = f"add_{inst_name}"
        method = getattr(self, method_name)
        if not method:
            raise NotImplementedError(f"OpenSearchTranslator.{method_name}")
        method(i)

    def result(self) -> str:
        stages = ["SELECT"]
        if self.project:
            cols = ", ".join(self.project)
            stages.append(f"{cols}")
        else:
            stages.append("*")
        stages.append(f"FROM {self.table}")
        if self.where:
            stages.append(f"WHERE {self.where}")
        if self.limit:
            stages.append(f"LIMIT {self.limit}")
        return " ".join(stages)
