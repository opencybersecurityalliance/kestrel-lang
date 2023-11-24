import json
from abc import ABC, abstractmethod
from pandas import DataFrame
from uuid import UUID
from typing import (
    Mapping,
    Union,
)

from kestrel.ir.instructions import Reference
from kestrel.ir.graph import IRGraphSoleInterface
from kestrel.exceptions import (
    UnresolvedReference,
    InvalidSerializedDatasourceInterfaceCacheCatalog,
)
from kestrel.config import InterfaceConfig


class AbstractDataSourceInterface(ABC):
    """Abstract class for datasource interface

    Concepts:

    - Think an interface as a datalake
    - Think a datasource as a table in the datalake

    Attributes:

        datasources: map a datasource name to datalake table name

        cache: map a cached item (instruction.id) to datalake table name
    """

    def __init__(
        self, config: InterfaceConfig, serialized_cache_catalog: Union[None, str] = None
    ):
        self.datasources: Mapping[str, str] = {}
        self.cache: Mapping[UUID, str] = {}
        self.__init_from_config(config)

        if serialized_interface_catalog:
            try:
                self.cache = json.loads(serialized_cache_catalog)
            except:
                raise InvalidSerializedDatasourceInterfaceCacheCatalog()

    def __init_from_config(self, config: InterfaceConfig):
        # TODO: fill self.datasources from config
        # TODO: create attributes like self.connection from config
        ...

    def __contains__(self, instruction_id: UUID) -> bool:
        """Whether a datasource is in the interface

        Parameters:
            instruction_id: id of the instruction
        """
        return instruction_id in self.cache

    @abstractmethod
    def create(
        self, datasource: str, df: DataFrame, session_id: Union[None, UUID] = None
    ):
        """Create datasource (table) given a dataframe

        In the implementation, recommend use `session_id` in the table
        name/path to isolate intermediate results of one session from another.

        Need to update self.cache at the end.
        """
        ...

    @abstractmethod
    def evaluate_graph(
        self, g: IRGraphSoleInterface, all_variables_in_return: bool = False
    ) -> Mapping[UUID, DataFrame]:
        """Evaluate the IRGraph

        Parameters:
            g: The IRGraph with zero or one interface
            all_variables_in_return: include evaluation results on all variables in return

        Returns:
            By default, return the dataframes for each sink node in the graph.
            If all_variables_in_return == True, also include dataframes for
            each variable node in the return.
        """
        # requirement: g should not have any Reference node
        refs = self.get_nodes_by_type(Reference)
        if refs:
            raise UnresolvedReference(refs)

    def cache_catalog_to_json(self) -> str:
        """Serialize the cache catalog to a JSON string"""
        return json.dumps(self.cache)
