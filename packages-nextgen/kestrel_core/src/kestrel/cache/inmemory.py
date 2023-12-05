from pandas import DataFrame
from typeguard import typechecked
from uuid import UUID
from typing import (
    Mapping,
    Optional,
    Iterable,
)

from kestrel.cache.base import Cache
from kestrel.ir.graph import IRGraphSoleInterface
from kestrel.ir.instructions import (
    Instruction,
    Return,
    Variable,
    SourceInstruction,
    TransformingInstruction,
)
from kestrel.interface.datasource.codegen.dataframe import (
    evaluate_source_instruction,
    evaluate_transforming_instruction,
)


@typechecked
class InMemoryCache(Cache):
    def __init__(self, initial_cache: Optional[Mapping[UUID, DataFrame]] = None):
        super().__init__()
        self.cache: Mapping[UUID, DataFrame] = {}
        if initial_cache:
            for k, v in initial_cache.items():
                self.store(k, v)

    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        return self.cache[self.cache_catalog[instruction_id]]

    def __delitem__(self, instruction_id: UUID):
        del self.cache[instruction_id]
        del self.cache_catalog[instruction_id]

    def store(
        self,
        instruction_id: UUID,
        data: DataFrame,
        session_id: Optional[UUID] = None,
    ):
        self.cache[instruction_id] = data
        self.cache_catalog[instruction_id] = instruction_id

    def evaluate_graph(
        self,
        graph: IRGraphSoleInterface,
        instructions_to_evaluate: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, DataFrame]:
        if not instructions_to_evaluate:
            instructions_to_evaluate = graph.get_returns()
        mapping = {
            ins.id: self._evaluate_instruction_in_graph(graph, ins)
            for ins in instructions_to_evaluate
        }
        return mapping

    def _evaluate_instruction_in_graph(
        self, graph: IRGraphSoleInterface, instruction: Instruction
    ) -> DataFrame:
        # TODO: handle multiple predecessors of a node

        if isinstance(instruction, Return):
            df = self._evaluate_instruction_in_graph(
                graph, next(graph.predecessors(instruction))
            )
        elif isinstance(instruction, Variable):
            df = self._evaluate_instruction_in_graph(
                graph, next(graph.predecessors(instruction))
            )
            self.store(instruction.id, df)
        elif isinstance(instruction, SourceInstruction):
            df = evaluate_source_instruction(instruction)
        elif isinstance(instruction, TransformingInstruction):
            df0 = self._evaluate_instruction_in_graph(
                graph, next(graph.predecessors(instruction))
            )
            df = evaluate_transforming_instruction(instruction, df0)
        else:
            raise NotImplementedError(f"Unknown instruction type: {instruction}")
        return df
