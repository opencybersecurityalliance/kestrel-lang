import importlib
import pkgutil
import inspect
import sys
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.exceptions import (
    DataSourceInterfaceNotFound,
    InvalidDataSourceInterfaceImplementation,
    ConflictingDataSourceInterfaceScheme,
)


class DataSourceManager:
    def __init__(self):
        self.scheme_to_interface = {}
        interfaces = _load_data_source_interfaces()
        for i in interfaces:
            self.scheme_to_interface.update({s: i for s in i.schemes()})

        # important state keeper, needed in Session()
        self.queried_data_sources = [None]

    def schemes(self):
        return list(self.scheme_to_interface.keys())

    def list_data_sources_from_scheme(self, scheme):
        scheme = scheme.lower()
        if scheme not in self.scheme_to_interface:
            raise DataSourceInterfaceNotFound(scheme)
        return self.scheme_to_interface[scheme].list_data_sources()

    def query(self, uri, pattern, session_id):
        scheme = uri.split("://")[0]
        scheme = scheme.lower()
        if scheme not in self.scheme_to_interface:
            raise DataSourceInterfaceNotFound(scheme)
        rs = self.scheme_to_interface[scheme].query(uri, pattern, session_id)
        self.queried_data_sources.append(uri)
        return rs


def _list_data_source_interfaces():
    pkg_names = map(lambda x: x.name, pkgutil.iter_modules())
    itf_names = filter(lambda x: x.startswith("kestrel_datasource_"), pkg_names)
    return list(itf_names)


def _load_data_source_interfaces():
    interface_names = _list_data_source_interfaces()
    interfaces = []
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
                interface, interfaces
            )
            if interface_conflict:
                raise ConflictingDataSourceInterfaceScheme(
                    interface, interface_conflict, scheme_conflict
                )
            interfaces.append(interface)
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
