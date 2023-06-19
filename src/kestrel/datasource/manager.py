from kestrel.absinterface import InterfaceManager
from kestrel.datasource import MODULE_PREFIX, AbstractDataSourceInterface
from kestrel.exceptions import (
    DataSourceInterfaceNotFound,
    InvalidDataSourceInterfaceImplementation,
    ConflictingDataSourceInterfaceScheme,
)


class DataSourceManager(InterfaceManager):
    def __init__(self, config):
        super().__init__(
            config,
            "datasources",
            ["language", "default_datasource_schema"],
            MODULE_PREFIX,
            AbstractDataSourceInterface,
            DataSourceInterfaceNotFound,
            InvalidDataSourceInterfaceImplementation,
            ConflictingDataSourceInterfaceScheme,
        )

        # important state keeper, required in Session()
        self.queried_data_sources = [None]

    def list_data_sources_from_scheme(self, scheme):
        i, c = self._get_interface_with_config(scheme)
        return i.list_data_sources(c)

    def query(self, uri, pattern, session_id, store, limit=None):
        scheme, uri = self._parse_and_complete_uri(uri)
        i, c = self._get_interface_with_config(scheme)
        rs = i.query(uri, pattern, session_id, c, store, limit)
        self.queried_data_sources.append(uri)
        return rs
