import logging
from functools import reduce
from typing import Optional, Union

from typeguard import typechecked

from kestrel.exceptions import UnsupportedOperatorError
from kestrel.ir.filter import (
    BoolExp,
    ExpOp,
    FComparison,
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
    Offset,
    ProjectAttrs,
    ProjectEntity,
    Sort,
    SortDirection,
)


_logger = logging.getLogger(__name__)


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


# SQL comparison operator functions
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
    # UNSUPPORTED BY OpenSearch SQL: StrCompOp.MATCHES: "REGEXP",
    # UNSUPPORTED BY OpenSearch SQL: StrCompOp.NMATCHES: "NOT REGEXP",
    ListOp.IN: "IN",
    ListOp.NIN: "NOT IN",
}


@typechecked
class OpenSearchTranslator:
    def __init__(
        self,
        timefmt: str,
        timestamp: str,
        select_from: str,
        data_model_map: dict,
        schema: dict,
    ):
        # Time format string for datasource
        self.timefmt = timefmt

        # Primary timestamp field in target table
        self.timestamp = timestamp

        # Query clauses
        self.table: str = select_from
        self.filt: Optional[Filter] = None
        self.entity: Optional[str] = None
        self.project: Optional[ProjectAttrs] = None
        self.limit: int = 0
        self.offset: int = 0
        self.order_by: str = ""
        self.sort_dir = SortDirection.DESC

        # Data model mapping: should be ocsf -> native
        self.from_ocsf_map = data_model_map

        # Index "schema" (field name -> type)
        self.schema = schema

    @typechecked
    def _render_comp(self, comp: FComparison) -> str:
        if isinstance(comp, StrComparison):
            # Need to quote string values
            value = f"'{comp.value}'"
        elif isinstance(comp, ListComparison):
            # SQL uses parens for lists
            value = tuple(comp.value)
        else:
            value = comp.value
        # Need to map OCSF filter field to native
        prefix = f"{self.entity}." if self.entity else ""
        ocsf_field = f"{prefix}{comp.field}"
        field = self.from_ocsf_map.get(ocsf_field, comp.field)
        _logger.debug("Mapped field '%s' to '%s'", ocsf_field, field)
        try:
            result = f"{field} {comp2func[comp.op]} {value}"
        except KeyError:
            raise UnsupportedOperatorError(comp.op.value)
        return result

    @typechecked
    def _render_multi_comp(self, comps: MultiComp) -> str:
        op = _and if comps.op == ExpOp.AND else _or
        return reduce(op, map(self._render_comp, comps.comps))

    @typechecked
    def _render_exp(self, exp: BoolExp) -> str:
        if isinstance(exp.lhs, BoolExp):
            lhs = self._render_exp(exp.lhs)
        elif isinstance(exp.lhs, MultiComp):
            lhs = self._render_multi_comp(exp.lhs)
        else:
            lhs = self._render_comp(exp.lhs)
        if isinstance(exp.rhs, BoolExp):
            rhs = self._render_exp(exp.rhs)
        elif isinstance(exp.rhs, MultiComp):
            rhs = self._render_multi_comp(exp.rhs)
        else:
            rhs = self._render_comp(exp.rhs)
        return _and(lhs, rhs) if exp.op == ExpOp.AND else _or(lhs, rhs)

    @typechecked
    def _render_filter(self) -> Optional[str]:
        if not self.filt:
            return None
        if self.filt.timerange.start:
            # Convert the timerange to the appropriate pair of comparisons
            start_comp = StrComparison(
                self.timestamp, ">=", self.filt.timerange.start.strftime(self.timefmt)
            )
            stop_comp = StrComparison(
                self.timestamp, "<", self.filt.timerange.stop.strftime(self.timefmt)
            )
            # AND them together
            time_exp = BoolExp(start_comp, ExpOp.AND, stop_comp)
            # AND that with any existing filter expression
            exp = BoolExp(self.filt.exp, ExpOp.AND, time_exp)
        else:
            exp = self.filt.exp
        if isinstance(exp, BoolExp):
            comp = self._render_exp(exp)
        elif isinstance(exp, MultiComp):
            comp = self._render_multi_comp(exp)
        else:
            comp = self._render_comp(exp)
        return comp

    def add_Filter(self, filt: Filter) -> None:
        # Just save filter and compile it later
        # Probably need the entity projection set first
        self.filt = filt

    def add_ProjectAttrs(self, proj: ProjectAttrs) -> None:
        # Just save projection and compile it later
        self.project = proj

    def _get_ocsf_cols(self):
        prefix = f"{self.entity}." if self.entity else ""
        if not self.project:
            ocsf_cols = [k for k in self.from_ocsf_map.keys() if k.startswith(prefix)]
        else:
            ocsf_cols = [f"{prefix}{col}" for col in self.project.attrs]
        _logger.debug("OCSF fields: %s", ocsf_cols)
        return ocsf_cols

    def _render_proj(self):
        fields = {
            self.from_ocsf_map.get(col, col): col for col in self._get_ocsf_cols()
        }
        _logger.debug("Fields: %s", fields)
        proj = [
            f"`{k}` AS `{v.partition('.')[2]}`" if "." in v else v
            for k, v in fields.items()
        ]
        _logger.debug("Set projection to %s", proj)
        return proj

    def add_ProjectEntity(self, proj: ProjectEntity) -> None:
        self.entity = proj.entity_type
        _logger.debug("Set base entity to '%s'", self.entity)

    def add_Limit(self, lim: Limit) -> None:
        self.limit = lim.num

    def add_Offset(self, offset: Offset) -> None:
        self.offset = offset.num

    def add_Sort(self, sort: Sort) -> None:
        self.order_by = sort.attribute
        self.sort_dir = sort.direction

    def add_instruction(self, i: Instruction) -> None:
        inst_name = i.instruction
        method_name = f"add_{inst_name}"
        try:
            method = getattr(self, method_name)
        except AttributeError as e:
            raise NotImplementedError(f"OpenSearchTranslator.{method_name}")
        method(i)

    def result(self) -> str:
        stages = ["SELECT"]
        cols = ", ".join(self._render_proj())
        stages.append(f"{cols}")
        stages.append(f"FROM {self.table}")
        where = self._render_filter()
        if where:
            stages.append(f"WHERE {where}")
        if self.order_by:
            stages.append(f"ORDER BY {self.order_by} {self.sort_dir.value}")
        if self.limit:
            # https://opensearch.org/docs/latest/search-plugins/sql/sql/basic/#limit
            if self.offset:
                stages.append(f"LIMIT {self.offset}, {self.limit}")
            else:
                stages.append(f"LIMIT {self.limit}")
        sql = " ".join(stages)
        _logger.debug("SQL: %s", sql)
        return sql
