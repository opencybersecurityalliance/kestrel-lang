from __future__ import annotations
from pandas import DataFrame
from typing import MutableMapping
from uuid import UUID
from abc import abstractmethod

from kestrel.config.internal import CACHE_INTERFACE_IDENTIFIER
from kestrel.interface import AbstractInterface


class AbstractCache(AbstractInterface, MutableMapping):
    """Base class for Kestrel cache

    Additional @abstractmethod from AbstractInterface:

        - evaluate_graph()
    """

    @staticmethod
    def schemes() -> Iterable[str]:
        return [CACHE_INTERFACE_IDENTIFIER]

    @abstractmethod
    def __del__(self):
        """Delete the cache and release memory/disk space"""
        ...

    @abstractmethod
    def __getitem__(self, instruction_id: UUID) -> DataFrame:
        """Get the dataframe for the cached instruction

        This method will automatically support `uuid in cache`

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

    @abstractmethod
    def get_virtual_copy(self) -> AbstractCache:
        """Create a virtual cache object from this cache

        This method needs to reimplement __del__, __getitem__, __setitem__,
        __delitem__ to not actually hit the store media, e.g., SQLite.

        The virtual cache is useful for the implementation of the Explain()
        instruction, pretending the dependent graphs are evaluated, so the
        evaluation can continue towards the Return() instruction.

        Because Python invokes special methods from class methods, replacing
        the __getitem__, __setitem__, and __delitem__ in the object does not
        help. It is better to derive a subclass and replace __class__ of the
        object to the subclass to correctly invoke the new set of __xitem___.

        https://docs.python.org/3/reference/datamodel.html#special-lookup

        And Python garbage collector could clean up the virtual cache when
        not in use, so the __del__ method should be reimplemented to make
        sure the store media is not closed.
        """
        ...

    def store(self, instruction_id: UUID, data: DataFrame):
        self[instruction_id] = data

    def __iter__(self) -> UUID:
        """Return UUIDs of instructions cached

        Returns:
            UUIDs in iterator
        """
        return iter(self.cache_catalog)

    def __len__(self) -> int:
        """How many items are cached"""
        return len(self.cache_catalog)
