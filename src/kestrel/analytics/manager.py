from kestrel.absinterface import InterfaceManager
from kestrel.analytics import MODULE_PREFIX, AbstractAnalyticsInterface
from kestrel.exceptions import (
    AnalyticsInterfaceNotFound,
    InvalidAnalyticsInterfaceImplementation,
    ConflictingAnalyticsInterfaceScheme,
)


class AnalyticsManager(InterfaceManager):
    def __init__(self, config):
        super().__init__(
            config,
            "analytics",
            ["language", "default_analytics_schema"],
            MODULE_PREFIX,
            AbstractAnalyticsInterface,
            AnalyticsInterfaceNotFound,
            InvalidAnalyticsInterfaceImplementation,
            ConflictingAnalyticsInterfaceScheme,
        )

    def list_analytics_from_scheme(self, scheme):
        i, c = self._get_interface_with_config(scheme)
        return i.list_analytics(c)

    def execute(self, uri, argument_variables, session_id, parameters):
        scheme, uri = self._parse_and_complete_uri(uri)
        i, c = self._get_interface_with_config(scheme)
        rs = i.execute(uri, argument_variables, c, session_id, parameters)
        return rs
