from copy import copy
from pandas import DataFrame
from typeguard import typechecked
from uuid import UUID
from typing import (
    Mapping,
    MutableMapping,
    Optional,
    Iterable,
    Any,
)

from kestrel.cache.base import AbstractCache
from kestrel.ir.graph import IRGraphEvaluable
from kestrel.display import GraphletExplanation, NativeQuery
from kestrel.ir.instructions import (
    Instruction,
    Return,
    Explain,
    Variable,
    Filter,
    SourceInstruction,
    TransformingInstruction,
)
from kestrel.interface.codegen.dataframe import (
    evaluate_source_instruction,
    evaluate_transforming_instruction,
)


@typechecked
class InMemoryCache(AbstractCache):
    def __init__(
        self,
        initial_cache: Mapping[UUID, DataFrame] = {},
        session_id: Optional[UUID] = None,
    ):
        super().__init__(session_id)
        self.cache: MutableMapping[UUID, DataFrame] = {}

        # update() will call __setitem__() internally
        self.update(initial_cache)

    def __del__(self):
        del self.cache

    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        return self.cache[self.cache_catalog[instruction_id]]

    def __delitem__(self, instruction_id: UUID):
        del self.cache[self.cache_catalog[instruction_id]]
        del self.cache_catalog[instruction_id]

    def __setitem__(
        self,
        instruction_id: UUID,
        data: DataFrame,
    ):
        self.cache_catalog[instruction_id] = instruction_id.hex
        self.cache[self.cache_catalog[instruction_id]] = data

    def get_virtual_copy(self) -> AbstractCache:
        v = copy(self)
        v.cache_catalog = copy(self.cache_catalog)
        v.__class__ = InMemoryCacheVirtual
        return v

    def evaluate_graph(
        self,
        graph: IRGraphEvaluable,
        instructions_to_evaluate: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, DataFrame]:
        mapping = {}
        if not instructions_to_evaluate:
            instructions_to_evaluate = graph.get_sink_nodes()
        for instruction in instructions_to_evaluate:
            df = self._evaluate_instruction_in_graph(graph, instruction)
            self[instruction.id] = df
            mapping[instruction.id] = df
        return mapping

    def explain_graph(
        self,
        graph: IRGraphEvaluable,
        instructions_to_explain: Optional[Iterable[Instruction]] = None,
    ) -> Mapping[UUID, GraphletExplanation]:
        mapping = {}
        if not instructions_to_evaluate:
            instructions_to_evaluate = graph.get_sink_nodes()
        for instruction in instructions_to_evaluate:
            dep_graph = graph.duplicate_dependent_subgraph_of_node(instruction)
            graph_dict = dep_graph.to_dict()
            query = NativeQuery("DataFrame", "")
            mapping[instruction.id] = GraphletExplanation(graph_dict, query)
        return mapping

    def _evaluate_instruction_in_graph(
        self, graph: IRGraphEvaluable, instruction: Instruction
    ) -> DataFrame:
        if instruction.id in self:
            df = self[instruction.id]
        elif isinstance(instruction, SourceInstruction):
            df = evaluate_source_instruction(instruction)
        elif isinstance(instruction, TransformingInstruction):
            trunk, r2n = graph.get_trunk_n_branches(instruction)
            df = self._evaluate_instruction_in_graph(graph, trunk)
            if isinstance(instruction, (Return, Explain)):
                pass
            elif isinstance(instruction, Variable):
                self[instruction.id] = df
            else:
                if isinstance(instruction, Filter):
                    # replace each ReferenceValue with a list of values
                    instruction.resolve_references(
                        lambda x: list(
                            self._evaluate_instruction_in_graph(graph, r2n[x]).iloc[
                                :, 0
                            ]
                        )
                    )
                df = evaluate_transforming_instruction(instruction, df)
        else:
            raise NotImplementedError(f"Unknown instruction type: {instruction}")
        return df


@typechecked
class InMemoryCacheVirtual(InMemoryCache):
    def __getitem__(self, instruction_id: UUID) -> Any:
        return self.cache_catalog[instruction_id]

    def __delitem__(self, instruction_id: UUID):
        del self.cache_catalog[instruction_id]

    def __setitem__(self, instruction_id: UUID, data: Any):
        self.cache_catalog[instruction_id] = "virtual" + instruction_id.hex
