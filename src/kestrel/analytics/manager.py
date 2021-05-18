import importlib
import pkgutil
import inspect
import sys
from kestrel.analytics import AbstractAnalyticsInterface
from kestrel.exceptions import (
    AnalyticsInterfaceNotFound,
    InvalidAnalyticsInterfaceImplementation,
    ConflictingAnalyticsInterfaceScheme,
)


class AnalyticsManager:
    def __init__(self):
        self.scheme_to_interface = {}
        interfaces = _load_analytics_interfaces()
        for i in interfaces:
            self.scheme_to_interface.update({s: i for s in i.schemes()})

    def schemes(self):
        return list(self.scheme_to_interface.keys())

    def list_analytics_from_scheme(self, scheme):
        scheme = scheme.lower()
        if scheme not in self.scheme_to_interface:
            raise AnalyticsInterfaceNotFound(scheme)
        return self.scheme_to_interface[scheme].list_analytics()

    def execute(self, uri, argument_variables, session_id, parameters):
        scheme = uri.split("://")[0]
        scheme = scheme.lower()
        if scheme not in self.scheme_to_interface:
            raise AnalyticsInterfaceNotFound(scheme)
        rs = self.scheme_to_interface[scheme].execute(
            uri, argument_variables, session_id, parameters
        )
        return rs


def _list_analytics_interfaces():
    pkg_names = map(lambda x: x.name, pkgutil.iter_modules())
    itf_names = filter(lambda x: x.startswith("kestrel_analytics_"), pkg_names)
    return list(itf_names)


def _load_analytics_interfaces():
    interface_names = _list_analytics_interfaces()
    interfaces = []
    for interface_name in interface_names:
        importlib.import_module(interface_name)
        cls = inspect.getmembers(sys.modules[interface_name], _is_interface_class)
        if not cls:
            raise InvalidAnalyticsInterfaceImplementation(
                f'no interface class found in "{interface_name}"'
            )
        elif len(cls) > 1:
            raise InvalidAnalyticsInterfaceImplementation(
                f'more than one interface class found in "{interface_name}"'
            )
        else:
            interface = cls[0][1]
            interface_conflict, scheme_conflict = _find_scheme_conflict(
                interface, interfaces
            )
            if interface_conflict:
                raise ConflictingAnalyticsInterfaceScheme(
                    interface, interface_conflict, scheme_conflict
                )
            interfaces.append(interface)
    return interfaces


def _is_interface_class(obj):
    return inspect.isclass(obj) and obj.__bases__[0] == AbstractAnalyticsInterface


def _find_scheme_conflict(new_interface, interfaces):
    for interface in interfaces:
        for scheme_new in new_interface.schemes():
            for scheme_old in interface.schemes():
                if scheme_new == scheme_old:
                    return interface, scheme_new
    return None, None
