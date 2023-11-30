from kestrel.cache.abc import AbstractCache
from kestrel.interface.datasource import AbstractDataSourceInterface


class Cache(AbstractDataSourceInterface, AbstractCache):
    """Every concrete Kestrel cache class should be a subclass of this."""

    ...
