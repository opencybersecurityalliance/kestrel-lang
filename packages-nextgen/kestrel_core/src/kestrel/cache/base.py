from pandas import DataFrame
from typing import MutableMapping
from uuid import UUID
from abc import abstractmethod

from kestrel.interface.datasource import AbstractDataSourceInterface


class AbstractCache(AbstractDataSourceInterface, MutableMapping):
    """Base class for Kestrel cache

    Additional @abstractmethod from AbstractDataSourceInterface:

        - __setitem__()

        - evaluate_graph()
    """

    @abstractmethod
    def __del__(self):
        """Delete the cache and release memory/disk space"""
        ...

    @abstractmethod
    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        """Get the dataframe for the cached instruction

        Parameters:
            instruction_id: id of the instruction

        Returns:
            dataframe of the given (likely Variable) instruction
        """
        ...

    @abstractmethod
    def __setitem__(self, instruction_id: UUID, data: DataFrame):
        """Store the dataframe of an instruction into cache

        Parameters:

            instruction_id: id of the instruction

            data: data associated with the instruction
        """
        ...

    @abstractmethod
    def __delitem__(self, instruction_id: UUID):
        """Delete cached item

        Parameters:
            instruction_id: id of the instruction
        """
        ...

    def store(self, instruction_id: UUID, data: DataFrame):
        self[instruction_id] = data

    def __contain__(self, instruction_id: UUID) -> bool:
        """Whether the evaluated instruction is cached

        Parameters:
            instruction_id: id of the instruction
        """
        return instruction_id in self.cache_catalog

    def __iter__(self) -> UUID:
        """Return UUIDs of instructions cached

        Returns:
            UUIDs in iterator
        """
        return iter(self.cache_catalog)

    def __len__(self) -> int:
        """How many items are cached"""
        return len(self.cache_catalog)
