import importlib
import pkgutil
import logging
import inspect
import sys

_logger = logging.getLogger(__name__)


class InterfaceManager:
    def __init__(
        self,
        config,
        config_root_key,
        default_schema_config_path,
        module_name_prefix,
        interface_class,
        nonexist_interface_exception,
        invalid_interface_exception,
        conflict_interface_exception,
    ):
        self.scheme_to_interface = {}
        self.scheme_to_interface_name = {}
        config[config_root_key] = {}
        self.config = config
        self.config_root_key = config_root_key
        self.default_schema_config_path = default_schema_config_path
        self.nonexist_interface_exception = nonexist_interface_exception

        for name, itf in _load_interfaces(
            module_name_prefix,
            interface_class,
            invalid_interface_exception,
            conflict_interface_exception,
        ).items():
            self.scheme_to_interface.update({s: itf for s in itf.schemes()})
            self.scheme_to_interface_name.update({s: name for s in itf.schemes()})
            self.config[self.config_root_key][name] = {}

    def schemes(self):
        return list(self.scheme_to_interface.keys())

    def _parse_and_complete_uri(self, uri):
        default_schema = self._get_default_schema()
        scheme, splitter, path = uri.rpartition("://")
        if not scheme:
            scheme = default_schema
            if not splitter:
                uri = default_schema + "://" + uri
            else:
                uri = default_schema + uri
        return scheme, uri

    def _get_interface_with_config(self, scheme):
        scheme = scheme.lower()
        if scheme not in self.scheme_to_interface:
            raise self.nonexist_interface_exception(scheme)
        if scheme not in self.scheme_to_interface_name:
            raise self.nonexist_interface_exception(scheme)
        interface_name = self.scheme_to_interface_name[scheme]
        interface_config = self.config[self.config_root_key][interface_name]
        interface = self.scheme_to_interface[scheme]
        return interface, interface_config

    def _get_default_schema(self):
        # this method is required to handle dynamic config changes
        # where the default schema is changed on the fly
        partial_config_path = self.config
        for path_component in self.default_schema_config_path:
            partial_config_path = partial_config_path[path_component]
        default_schema = partial_config_path

        if default_schema not in self.scheme_to_interface:
            _logger.error(f"default datasource schema {default_schema} not found.")
            raise self.nonexist_interface_exception(default_schema)

        return default_schema


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
        importlib.import_module(interface_name)
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
    pkg_names = map(lambda x: x.name, pkgutil.iter_modules())
    itf_names = filter(lambda x: x.startswith(module_name_prefix), pkg_names)
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
