from abc import ABC

import importlib
import pkgutil
import logging
import inspect
import sys

from kestrel.exceptions import KestrelError


_logger = logging.getLogger(__name__)


class InterfaceManager:
    def __init__(
        self,
        module_name_prefix: str,
        interface_class: ABC,
        nonexist_interface_exception: KestrelError,
        invalid_interface_exception: KestrelError,
        conflict_interface_exception: KestrelError,
    ):
        self.scheme_to_interface: dict[str, ABC] = {}
        self.nonexist_interface_exception = nonexist_interface_exception

        for iface_cls in _load_interfaces(
            module_name_prefix,
            interface_class,
            invalid_interface_exception,
            conflict_interface_exception,
        ).values():
            iface = iface_cls()
            _logger.debug("Loading data source interface '%s' (%s)", iface.name, iface)
            self.scheme_to_interface[iface.name] = iface

    def interfaces(self):
        return list(self.scheme_to_interface.values())

    def schemes(self):
        return list(self.scheme_to_interface.keys())


def _load_interfaces(
    module_name_prefix,
    interface_class,
    invalid_interface_exception,
    conflict_interface_exception,
):
    is_interface = _is_class(interface_class)
    interface_names = _list_interfaces(module_name_prefix)
    interfaces = {}
    for interface_name in interface_names:
        mod = importlib.import_module(interface_name)
        _logger.debug("Imported %s from interface name %s", mod, interface_name)
        cls = inspect.getmembers(sys.modules[interface_name], is_interface)
        if not cls:
            raise invalid_interface_exception(
                f'no interface class found in "{interface_name}"'
            )
        elif len(cls) > 1:
            raise invalid_interface_exception(
                f'more than one interface class found in "{interface_name}"'
            )
        else:
            interface = cls[0][1]
            interface_conflict, scheme_conflict = _search_scheme_conflict(
                interface, interfaces.values()
            )
            if interface_conflict:
                raise conflict_interface_exception(
                    interface, interface_conflict, scheme_conflict
                )
            interfaces[interface_name] = interface
    return interfaces


def _list_interfaces(module_name_prefix):
    pkg_names = [x.name for x in pkgutil.iter_modules()]
    itf_names = [pkg for pkg in pkg_names if pkg.startswith(module_name_prefix)]
    return list(itf_names)


def _is_class(cls):
    return lambda obj: inspect.isclass(obj) and obj.__bases__[0] == cls


def _search_scheme_conflict(new_interface, interfaces):
    for interface in interfaces:
        for scheme_new in new_interface.schemes():
            for scheme_old in interface.schemes():
                if scheme_new == scheme_old:
                    return interface, scheme_new
    return None, None
