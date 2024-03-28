import logging
from functools import reduce
from typing import Callable, Iterable, Mapping, Optional
from uuid import UUID

from pandas import DataFrame, read_sql
import sqlalchemy
from sqlalchemy import and_, column, or_
from sqlalchemy.sql.elements import BooleanClauseList
from sqlalchemy.sql.expression import ColumnClause
from typeguard import typechecked

from kestrel.display import GraphletExplanation
from kestrel.interface import AbstractInterface
from kestrel.interface.codegen.sql import SqlTranslator, comp2func
from kestrel.ir.filter import (
    BoolExp,
    ExpOp,
    FComparison,
    MultiComp,
    StrComparison,
    StrCompOp,
)
from kestrel.ir.graph import IRGraphEvaluable
from kestrel.ir.instructions import (
    DataSource,
    Filter,
    Instruction,
    ProjectAttrs,
    ProjectEntity,
    Return,
    SolePredecessorTransformingInstruction,
    SourceInstruction,
    TransformingInstruction,
    Variable,
)
from kestrel.mapping.data_model import (
    translate_comparison_to_native,
    translate_dataframe,
    translate_projection_to_native,
)

from kestrel_interface_sqlalchemy.config import load_config


_logger = logging.getLogger(__name__)


@typechecked
class SQLAlchemyTranslator(SqlTranslator):
    def __init__(
        self,
        dialect: sqlalchemy.engine.default.DefaultDialect,
        timefmt: Callable,
        timestamp: str,
        from_obj: sqlalchemy.FromClause,
        dmm: dict,
    ):
        super().__init__(dialect, timefmt, timestamp, from_obj)
        self.dmm = dmm
        self.proj = None
        self.entity_type = None

    @typechecked
    def _render_comp(self, comp: FComparison):
        prefix = (
            f"{self.entity_type}."
            if (self.entity_type and comp.field != self.timestamp)
            else ""
        )
        ocsf_field = f"{prefix}{comp.field}"
        comps = translate_comparison_to_native(
            self.dmm, ocsf_field, comp.op, comp.value
        )
        translated_comps = []
        for comp in comps:
            field, op, value = comp
            col: ColumnClause = column(field)
            if op == StrCompOp.NMATCHES:
                tmp = ~comp2func[op](col, value)
            else:
                tmp = comp2func[op](col, value)
            translated_comps.append(tmp)
        return reduce(or_, translated_comps)

    @typechecked
    def _render_multi_comp(self, comps: MultiComp):
        op = and_ if comps.op == ExpOp.AND else or_
        return reduce(op, map(self._render_comp, comps.comps))

    # This is copied verbatim from sql.py but we need to supply our own _render_comp
    def _render_exp(self, exp: BoolExp) -> BooleanClauseList:
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
        return and_(lhs, rhs) if exp.op == ExpOp.AND else or_(lhs, rhs)

    @typechecked
    def _add_filter(self) -> Optional[str]:
        if not self.filt:
            return None
        filt = self.filt
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
            comp = self._render_multi_comp(exp)
        else:
            comp = self._render_comp(exp)
        self.query = self.query.where(comp)

    def add_Filter(self, filt: Filter) -> None:
        # Just save filter and compile it later
        # Probably need the entity projection set first
        self.filt = filt

    def add_ProjectAttrs(self, proj: ProjectAttrs) -> None:
        self.proj = proj

    def add_ProjectEntity(self, proj: ProjectEntity) -> None:
        self.entity_type = proj.entity_type

    def result(self) -> sqlalchemy.Compiled:
        proj = self.proj.attrs if self.proj else None
        pairs = translate_projection_to_native(self.dmm, self.entity_type, proj)
        cols = [sqlalchemy.column(i).label(j) for i, j in pairs]
        self._add_filter()
        self.query = self.query.with_only_columns(*cols)  # TODO: mapping?
        return self.query.compile(dialect=self.dialect)


class SQLAlchemyInterface(AbstractInterface):
    def __init__(
        self,
        serialized_cache_catalog: Optional[str] = None,
        session_id: Optional[UUID] = None,
    ):
        _logger.debug("SQLAlchemyInterface: loading config")
        super().__init__(serialized_cache_catalog, session_id)
        self.config = load_config()
        self.schemas: dict = {}  # Schema per table (index)
        self.engines: dict = {}  # Map of conn name -> engine
        self.conns: dict = {}  # Map of conn name -> connection
        for info in self.config.tables.values():
            name = info.connection
            conn_info = self.config.connections[name]
            if name not in self.engines:
                self.engines[name] = sqlalchemy.create_engine(conn_info.url)
            if name not in self.conns:
                engine = self.engines[name]
                self.conns[name] = engine.connect()
            _logger.debug("SQLAlchemyInterface: configured %s", name)

    @staticmethod
    def schemes() -> Iterable[str]:
        return ["sqlalchemy"]

    def store(
        self,
        instruction_id: UUID,
        data: DataFrame,
    ):
        raise NotImplementedError("SQLAlchemyInterface.store")  # TEMP

    def evaluate_graph(
        self,
        graph: IRGraphEvaluable,
        instructions_to_evaluate: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, DataFrame]:
        mapping = {}
        if not instructions_to_evaluate:
            instructions_to_evaluate = graph.get_sink_nodes()
        for instruction in instructions_to_evaluate:
            translator = self._evaluate_instruction_in_graph(graph, instruction)
            # TODO: may catch error in case evaluation starts from incomplete SQL
            sql = translator.result()
            _logger.debug("SQL query generated: %s", sql)
            # Get the "from" table for this query
            tables = translator.query.selectable.get_final_froms()
            table = tables[0].name  # TODO: what if there's more than 1?
            # Get the data source's SQLAlchemy connection object
            conn = self.conns[self.config.tables[table].connection]
            df = read_sql(sql, conn)
            dmm = translator.dmm[
                translator.entity_type
            ]  # TODO: need a method for this?
            mapping[instruction.id] = translate_dataframe(df, dmm)
        return mapping

    def explain_graph(
        self,
        graph: IRGraphEvaluable,
        instructions_to_explain: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, GraphletExplanation]:
        mapping = {}
        if not instructions_to_explain:
            instructions_to_explain = graph.get_sink_nodes()
        for instruction in instructions_to_explain:
            translator = self._evaluate_instruction_in_graph(graph, instruction)
            dep_graph = graph.duplicate_dependent_subgraph_of_node(instruction)
            graph_dict = dep_graph.to_dict()
            query_stmt = translator.result()
            mapping[instruction.id] = GraphletExplanation(graph_dict, query_stmt)
        return mapping

    def _evaluate_instruction_in_graph(
        self,
        graph: IRGraphEvaluable,
        instruction: Instruction,
    ) -> SQLAlchemyTranslator:
        _logger.debug("instruction: %s", str(instruction))
        translator = None
        if isinstance(instruction, TransformingInstruction):
            trunk, _r2n = graph.get_trunk_n_branches(instruction)
            translator = self._evaluate_instruction_in_graph(graph, trunk)

            if isinstance(instruction, SolePredecessorTransformingInstruction):
                if isinstance(instruction, Return):
                    pass
                elif isinstance(instruction, Variable):
                    pass
                else:
                    translator.add_instruction(instruction)

            elif isinstance(instruction, Filter):
                translator.add_instruction(instruction)

            else:
                raise NotImplementedError(f"Unknown instruction type: {instruction}")

        elif isinstance(instruction, SourceInstruction):
            if isinstance(instruction, DataSource):
                ds = self.config.tables[instruction.datasource]
                connection = ds.connection
                dialect = self.engines[connection].dialect
                translator = SQLAlchemyTranslator(
                    dialect,
                    lambda dt: dt.strftime(ds.timestamp_format),
                    ds.timestamp,
                    sqlalchemy.table(instruction.datasource),
                    ds.data_model_map,
                )
            else:
                raise NotImplementedError(f"Unhandled instruction type: {instruction}")

        return translator
