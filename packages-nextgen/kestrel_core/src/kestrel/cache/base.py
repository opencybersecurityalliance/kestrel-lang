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
    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        """Get the dataframe for the cached instruction

        Parameters:
            instruction_id: id of the instruction

        Returns:
            dataframe of the given (likely Variable) instruction
        """
        ...

    @abstractmethod
    def __delitem__(self, instruction_id: UUID):
        """Delete cached item

        Parameters:
            instruction_id: id of the instruction
        """
        ...

    @abstractmethod
    def __iter__(self) -> DataFrame:
        """Return cached values (dataframes)

        Returns:
            dataframes in iterator
        """
        ...

    def __len__(self) -> int:
        """How many items are cached"""
        return len(self.cache_catalog)
