import logging
from typing import Iterable, Mapping, Optional
from uuid import UUID

from dateutil.parser import parse as dt_parser
from pandas import DataFrame, read_sql
from sqlalchemy import create_engine, table, text
from sqlalchemy.dialects import sqlite
from typeguard import typechecked

from kestrel.cache.base import Cache
from kestrel.interface.datasource.codegen.sql import SqlTranslator
from kestrel.ir.graph import IRGraphSoleInterface
from kestrel.ir.instructions import (
    Construct,
    Filter,
    Instruction,
    Return,
    SourceInstruction,
    TransformingInstruction,
    Variable,
)

_logger = logging.getLogger(__name__)


@typechecked
class SqliteTranslator(SqlTranslator):
    def __init__(self):
        super().__init__(
            sqlite.dialect(), dt_parser, "time"
        )  # FIXME: need mapping for timestamp?


@typechecked
def _set_from(translator: SqliteTranslator, table_name: str):
    """Utility method to set the table for a SQL query.

    This is used to handle Construct instructions.
    """
    translator.query = translator.query.select_from(table(table_name))


@typechecked
class SqliteCache(Cache):
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
                self.store(instruction_id, data)

    def __del__(self):
        self.connection.close()

    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        result = read_sql(instruction_id.hex, self.connection)
        return result

    def __delitem__(self, instruction_id: UUID):
        self.connection.execute(text(f'DROP TABLE "{instruction_id.hex}"'))

    def _to_sql(self, df: DataFrame, name: str):
        df.to_sql(name, con=self.connection, if_exists="replace", index=False)

    def store(
        self,
        instruction_id: UUID,
        data: DataFrame,
    ):
        self._to_sql(data, instruction_id.hex)

    def evaluate_graph(
        self,
        graph: IRGraphSoleInterface,
        instructions_to_evaluate: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, DataFrame]:
        if not instructions_to_evaluate:
            instructions_to_evaluate = graph.get_sink_nodes()  # get_variables()
        stacks = []
        for inst in instructions_to_evaluate:
            stacks.append(self._visit(graph, inst))
        mapping = {}
        for stack in stacks:
            tail = stack[-1]
            mapping[tail.id] = self._evaluate_instruction_stack(stack)
        _logger.debug("mapping: %s", mapping)
        return mapping

    def _visit(
        self,
        graph: IRGraphSoleInterface,
        instruction: Instruction,
        stack: Optional[list[Instruction]] = None,
    ) -> list[Instruction]:
        """
        Depth-first visit of nodes in graph from variable to variable or variable to source

        Returns:
            stack of Instructions visited
        """
        if not stack:
            stack = []
        # TODO: handle multiple predecessors of a node
        _logger.debug("_visit: %s", instruction)
        if isinstance(instruction, SourceInstruction) or (
            isinstance(instruction, Variable) and len(stack) > 0
        ):
            # Need to first check if stack is empty since we start with var
            # Since it's non-empty, this var should terminate the chain
            stack.append(instruction)
            return stack

        stack = self._visit(graph, next(graph.predecessors(instruction)))
        stack.append(instruction)
        return stack

    def _evaluate_instruction_stack(self, stack: list[Instruction]) -> DataFrame:
        translator = SqliteTranslator()
        df = None
        previous_instruction = None
        for instruction in stack:
            _logger.debug("_eval: %s", instruction)
            if isinstance(instruction, Construct):
                pass  # Handled by the following Variable assignment
            elif isinstance(instruction, Variable):
                # This means assignment
                if isinstance(previous_instruction, Construct):
                    df = DataFrame(previous_instruction.data)
                    self.store(instruction.id, df)
                    _set_from(translator, instruction.id.hex)
            elif isinstance(instruction, Return):
                stmt = translator.result()
                _logger.debug("%s -> %s", instruction, stmt)
                df = read_sql(stmt, self.connection)
            elif isinstance(instruction, TransformingInstruction):
                translator.add_instruction(instruction)
            previous_instruction = instruction
        return df
