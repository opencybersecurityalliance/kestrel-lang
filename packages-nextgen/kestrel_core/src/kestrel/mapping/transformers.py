"""Kestrel Data Model Map value transformers"""

from typing import Callable


# Dict of "registered" transformers
_transformers = {}


def transformer(func: Callable) -> Callable:
    """A decorator for registering a transformer"""
    _transformers[func.__name__] = func
    return func


@transformer
def dirname(path: str) -> str:  # TODO: rename to winpath_dirname?
    """Get the directory part of `path`"""
    path_dir, _, _ = path.rpartition("\\")
    return path_dir


@transformer
def basename(path: str) -> str:  # TODO: rename to winpath_dirname?
    """Get the filename part of `path`"""
    _, _, path_file = path.rpartition("\\")
    return path_file


@transformer
def startswith(value: str) -> str:  # TODO: rename to winpath_startswith?
    return f"{value}\\%"


@transformer
def endswith(value: str) -> str:  # TODO: rename to winpath_endswith?
    return f"%\\{value}"


@transformer
def to_int(value) -> int:
    """Ensure `value` is an int"""
    try:
        return int(value)
    except ValueError:
        # Maybe it's a hexadecimal string?
        return int(value, 16)


@transformer
def to_str(value) -> str:
    """Ensure `value` is a str"""
    return str(value)


@transformer
def ip_version_to_network_layer(value: int) -> str:
    if value == 4:
        return "ipv4"
    elif value == 6:
        return "ipv6"
    elif value == 99:
        return "other"
    return "unknown"


@transformer
def network_layer_to_ip_version(val: str) -> int:
    value = val.lower()
    if value == "ipv4":
        return 4
    elif value == "ipv6":
        return 6
    elif value == "other":
        return 99
    return 0


def run_transformer(transformer_name: str, value):
    """Run the registered transformer with name `transformer_name` on `value`"""
    func = _transformers.get(transformer_name)
    if func:
        result = func(value)
    else:
        raise NameError(transformer_name)
    return result
