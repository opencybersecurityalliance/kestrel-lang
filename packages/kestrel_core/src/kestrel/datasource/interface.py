"""The abstract interface for building a data source interface for Kestrel.

A Kestrel data source interface is a Python package with the following rules:

- The package name should use prefix ``kestrel_datasource_``.

- The package should have one and only one root level class inherited from
  :class:`AbstractDataSourceInterface`.

  - There is no restriction on package structure for the package.

  - There is no restriction on interface class name.

  - The interface class should inhert :class:`AbstractDataSourceInterface`.

  - The interface class should be importable from the package directly, i.e.,
    it needs to be imported into ``__init__.py`` of the package.

  - Zero class inherited from :class:`AbstractDataSourceInterface` will
    result in an exception.

  - Multiple classes inherited from :class:`AbstractDataSourceInterface` will
    result in an exception.

"""

from abc import ABC, abstractmethod

MODULE_PREFIX = "kestrel_datasource_"


class AbstractDataSourceInterface(ABC):
    """The abstract class for building a data source interface.

    Why do we design the interface this way? Actually we do not need a class
    for building the interface since all methods are static. However, in
    Python, we need to have a class if we'd like to enforce developers to
    implement the methods when developing a concrete interface. This is done by
    using both ``@staticmethod`` and ``@abstractmethod`` decorators for all
    methods/functions. When using an interface, Kestrel runtime will not
    instantiate an object from an interface class but use the static methods
    directly. This may not look beautiful in design, and hope we have
    something comparable to ``typeclass`` in Haskell for non-OOP interface
    abstraction in the future.

    """

    @staticmethod
    @abstractmethod
    def schemes():
        """``scheme`` (the URI prefix before ``://``) of the data source
        interface.

        Every data source interface should have at least one *unique* scheme to
        use at the beginning of the data source URI. To develop a new data
        source, one needs to check public Kestrel data source packages to name a new
        one that is not taken. Note that scheme defined here should be in
        lowercase, and Kestrel data source manager will normalize schemes of
        incoming URIs into lowercase.

        Returns:
            [str]: A list of schemes; A URI with one of the scheme will be
            processed by this interface.

        """
        return []

    @staticmethod
    @abstractmethod
    def list_data_sources(config):
        """List data source names accessible from this interface.

        Args:
            config (dict): a layered list/dict that contains config for the
              interface and can be edited/updated by the interface.

        Returns:
            [str]: A list of data source names accessible from this interface.

        """
        return []

    @staticmethod
    @abstractmethod
    def query(uri, pattern, session_id, config, store=None, limit=None):
        """Sending a data query to a specific data source.

        If the store of the session is modified and directly gets the data
        loaded into a ``query_id``, it should return
        :attr:`kestrel.datasource.ReturnFromStore`.

        If the interface uses local files as intermediate/temporary storage
        before loading it to the store, it should return
        :attr:`kestrel.datasource.ReturnFromFile`.

        Args:
            uri (str): the full URI including the scheme and data source name.

            pattern (str): the pattern to query (currently we support STIX).

            session_id (str): id of the session, may be useful for analytics
              directly writing into the store.

            config (dict): a layered list/dict that contains config for the
              interface and can be edited/updated by the interface.

            store (firepit.SqlStorage): The internal store used by the session

            limit (Optional[int]): limit on the number of records to return;
              None if there is no limit

        Returns:
            kestrel.datasource.retstruct.AbstractReturnStruct: returned data.
            Currently there are two choices:
            :attr:`kestrel.datasource.ReturnFromFile` and
            :attr:`kestrel.datasource.ReturnFromStore`.

        """
        return None
