from pandas import DataFrame
from uuid import UUID
from typing import (
    Mapping,
    Union,
)

from kestrel.cache.base import Cache
from kestrel.ir.graph import IRGraphSoleInterface


class InMemoryCache(Cache):
    def __init__(self, initial_cache: Union[None, Mapping[UUID, DataFrame]] = None):
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
        session_id: Union[None, UUID] = None,
    ):
        self.cache[instruction_id] = data
        self.cache_catalog[instruction_id] = instruction_id

    def evaluate_graph(
        self, g: IRGraphSoleInterface, all_variables_in_return: bool = False
    ) -> Mapping[UUID, DataFrame]:
        ...
