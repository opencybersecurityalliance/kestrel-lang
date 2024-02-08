from typing import Iterable
from typeguard import typechecked

from kestrel.interface.datasource import AbstractDataSourceInterface
from kestrel.exceptions import (
    InterfaceNotFound,
    InterfaceNameCollision,
)


@typechecked
def get_interface_by_name(
    interface_name: str, interfaces: Iterable[AbstractDataSourceInterface]
):
    """Find an interface by its name

    Parameters:
        interface_name: the name of an interface
        interfaces: the list of interfaces

    Returns:
        The interface found
    """
    ifs = filter(lambda x: x.name == interface_name, interfaces)
    try:
        interface = next(ifs)
    except StopIteration:
        raise InterfaceNotFound(interface_name)
    else:
        try:
            next(ifs)
        except StopIteration:
            # expected behavior
            pass
        else:
            raise InterfaceNameCollision(interface_name)
    return interface
