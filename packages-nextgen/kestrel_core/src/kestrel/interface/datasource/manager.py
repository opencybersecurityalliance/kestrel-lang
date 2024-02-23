from kestrel.exceptions import (
    DataSourceInterfaceNotFound,
    InvalidDataSourceInterfaceImplementation,
    ConflictingDataSourceInterfaceScheme,
)
from kestrel.interface.manager import InterfaceManager
from kestrel.interface.datasource.base import (
    MODULE_PREFIX,
    AbstractDataSourceInterface,
)


class DataSourceManager(InterfaceManager):
    def __init__(self):
        super().__init__(
            MODULE_PREFIX,
            AbstractDataSourceInterface,
            DataSourceInterfaceNotFound,
            InvalidDataSourceInterfaceImplementation,
            ConflictingDataSourceInterfaceScheme,
        )
