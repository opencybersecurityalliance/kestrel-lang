import logging
from typing import Iterable, List, Mapping, Optional
from uuid import UUID

from dateutil.parser import parse as dt_parser
from pandas import DataFrame, read_sql
from sqlalchemy import create_engine, table, text
from sqlalchemy.dialects import sqlite
from typeguard import typechecked

from kestrel.cache.base import AbstractCache
from kestrel.interface.datasource.codegen.sql import SqlTranslator
from kestrel.ir.graph import IRGraphEvaluable
from kestrel.ir.instructions import (
    Construct,
    Instruction,
    Return,
    Variable,
    Filter,
    SourceInstruction,
    TransformingInstruction,
    SolePredecessorTransformingInstruction,
)

from kestrel.exceptions import (
    InevaluableInstruction,
)

_logger = logging.getLogger(__name__)


@typechecked
class SqliteTranslator(SqlTranslator):
    def __init__(self, select_from: str):
        super().__init__(
            sqlite.dialect(), dt_parser, "time", select_from
        )  # FIXME: need mapping for timestamp?


@typechecked
class SqliteCache(AbstractCache):
    def __init__(
        self,
        initial_cache: Optional[Mapping[UUID, DataFrame]] = None,
        session_id: Optional[UUID] = None,
    ):
        super().__init__()

        basename = self.session_id or "cache"
        path = f"{basename}.db"

        # for an absolute file path, the three slashes are followed by the absolute path
        # for a relative path, it's also three slashes?
        self.engine = create_engine(f"sqlite:///{path}")
        self.connection = self.engine.connect()

        if initial_cache:
            for instruction_id, data in initial_cache.items():
                self[instruction_id] = data

    def __del__(self):
        self.connection.close()

    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        return read_sql(self.cache_catalog[instruction_id], self.connection)

    def __delitem__(self, instruction_id: UUID):
        table = self.cache_catalog[instruction_id]
        self.connection.execute(text(f'DROP TABLE "{table}"'))
        del self.cache_catalog[instruction_id]

    def __setitem__(
        self,
        instruction_id: UUID,
        data: DataFrame,
    ):
        table = instruction_id.hex
        self.cache_catalog[instruction_id] = table
        data.to_sql(
            table, con=self.connection, if_exists="replace", index=False
        )

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
            mapping[instruction.id] = read_sql(translator.result(), self.connection)
        _logger.debug("mapping: %s", mapping)
        return mapping

    def _evaluate_instruction_in_graph(
        self,
        graph: IRGraphEvaluable,
        instruction: Instruction,
    ) -> SqliteTranslator:
        _logger.debug("_eval: %s", instruction)

        if instruction.id in self:
            translator = SqliteTranslator(self.cache_catalog[instruction.id])

        elif isinstance(instruction, SourceInstruction):
            if isinstance(instruction, Construct):
                self[instruction.id] = DataFrame(instruction.data)
                translator = SqliteTranslator(self.cache_catalog[instruction.id])
            else:
                raise NotImplementedError(f"Unknown instruction type: {instruction}")

        elif isinstance(instruction, TransformingInstruction):

            trunk, r2n = graph.get_trunk_n_branches(instruction)
            translator = self._evaluate_instruction_in_graph(graph, trunk)

            if isinstance(instruction, SolePredecessorTransformingInstruction):
                if not isinstance(instruction, (Return, Variable)):
                    translator.add_instruction(instruction)

            elif isinstance(instruction, Filter):
                translator = self._evaluate_instruction_in_graph(graph, trunk)
                translator.add_instruction(instruction)

            else:
                raise NotImplementedError(f"Unknown instruction type: {instruction}")

        else:
            raise NotImplementedError(f"Unknown instruction type: {instruction}")

        return translator
