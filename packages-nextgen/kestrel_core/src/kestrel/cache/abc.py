from abc import ABC, abstractmethod
from pandas import DataFrame
from uuid import UUID


class AbstractCache(ABC):
    """Abstract cache class for typing purpose

    This class is for internal typing use to avoid circular import.

    Use Cache from kestrel.cache.base to subclass concrete cache class.
    """

    def __contains__(self, instruction_id: UUID) -> bool:
        """Whether an instruction result is in the cache

        Parameters:

            instruction_id: id of the instruction
        """
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
    def __delitem__(self, instruction_id: UUID):
        """Delete cached item

        Parameters:
            instruction_id: id of the instruction
        """
        ...
