import sys
from typeguard import typechecked


"""Entrance to invoke any backward compatibility patch

This module is for developers to quickly locate backward compatibility pathes
in Kestrel code and remove them through time.
"""


@typechecked
def is_python_older_than_minor_version(minor: int) -> bool:
    return sys.version_info.minor < minor
