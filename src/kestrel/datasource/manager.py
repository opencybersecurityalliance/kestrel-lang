import importlib
import pkgutil
import logging
import inspect
import sys
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.exceptions import (
    DataSourceInterfaceNotFound,
    InvalidDataSourceInterfaceImplementation,
    ConflictingDataSourceInterfaceScheme,
)

_logger = logging.getLogger(__name__)


class DataSourceManager:
    def __init__(self, config):
        self.scheme_to_interface = {}
        self.scheme_to_interface_name = {}
        config["datasources"] = {}
        self.config = config

        for n, i in _load_data_source_interfaces().items():
            self.scheme_to_interface.update({s: i for s in i.schemes()})
            self.scheme_to_interface_name.update({s: n for s in i.schemes()})
            self.config["datasources"][n] = {}

        # important state keeper, needed in Session()
        self.queried_data_sources = [None]

        default_schema = self.config["language"]["default_datasource_schema"]
        if default_schema not in self.scheme_to_interface:
            _logger.error(f"default datasource schema {default_schema} not found.")
            raise DataSourceInterfaceNotFound(default_schema)

    def schemes(self):
        return list(self.scheme_to_interface.keys())

    def list_data_sources_from_scheme(self, scheme):
        i, c = self._get_interface_with_config(scheme)
        return self.i.list_data_sources(c)

    def query(self, uri, pattern, session_id):
        default_schema = self.config["language"]["default_datasource_schema"]
        scheme, splitter, path = uri.rpartition("://")
        if not scheme:
            scheme = default_schema
            if not splitter:
                uri = default_schema + "://" + uri
            else:
                uri = default_schema + uri
        i, c = self._get_interface_with_config(scheme)
        rs = i.query(uri, pattern, session_id, c)
        self.queried_data_sources.append(uri)
        return rs

    def _get_interface_with_config(self, scheme):
        scheme = scheme.lower()
        if scheme not in self.scheme_to_interface:
            raise DataSourceInterfaceNotFound(scheme)
        if scheme not in self.scheme_to_interface_name:
            raise DataSourceInterfaceNotFound(scheme)
        interface_name = self.scheme_to_interface_name[scheme]
        interface_config = self.config["datasources"][interface_name]
        interface = self.scheme_to_interface[scheme]
        return interface, interface_config


def _list_data_source_interfaces():
    pkg_names = map(lambda x: x.name, pkgutil.iter_modules())
    itf_names = filter(lambda x: x.startswith("kestrel_datasource_"), pkg_names)
    return list(itf_names)


def _load_data_source_interfaces():
    interface_names = _list_data_source_interfaces()
    interfaces = {}
    for interface_name in interface_names:
        importlib.import_module(interface_name)
        cls = inspect.getmembers(sys.modules[interface_name], _is_interface_class)
        if not cls:
            raise InvalidDataSourceInterfaceImplementation(
                f'no interface class found in "{interface_name}"'
            )
        elif len(cls) > 1:
            raise InvalidDataSourceInterfaceImplementation(
                f'more than one interface class found in "{interface_name}"'
            )
        else:
            interface = cls[0][1]
            interface_conflict, scheme_conflict = _find_scheme_conflict(
                interface, interfaces.values()
            )
            if interface_conflict:
                raise ConflictingDataSourceInterfaceScheme(
                    interface, interface_conflict, scheme_conflict
                )
            interfaces[interface_name] = interface
    return interfaces


def _is_interface_class(obj):
    return inspect.isclass(obj) and obj.__bases__[0] == AbstractDataSourceInterface


def _find_scheme_conflict(new_interface, interfaces):
    for interface in interfaces:
        for scheme_new in new_interface.schemes():
            for scheme_old in interface.schemes():
                if scheme_new == scheme_old:
                    return interface, scheme_new
    return None, None
