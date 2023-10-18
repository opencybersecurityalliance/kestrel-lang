"""The abstract interface for building an analytics interface for Kestrel.

A Kestrel analytics interface is a Python package with the following rules:

- The package name should use prefix ``kestrel_analytics_``.

- The package should have one and only one root level class inherited from
  :class:`AbstractAnalyticsInterface`.

  - There is no restriction on package structure for the package.

  - There is no restriction on interface class name.

  - The interface class should inhert :class:`AbstractAnalyticsInterface`.

  - The interface class should be importable from the package directly, i.e.,
    it needs to be imported into ``__init__.py`` of the package.

  - Zero class inherited from :class:`AbstractAnalyticsInterface` will
    result in an exception.

  - Multiple classes inherited from :class:`AbstractAnalyticsInterface` will
    result in an exception.

"""

from abc import ABC, abstractmethod

MODULE_PREFIX = "kestrel_analytics_"


class AbstractAnalyticsInterface(ABC):
    """The abstract class for building an analytics interface."""

    @staticmethod
    @abstractmethod
    def schemes():
        """``scheme`` (the URI prefix before ``://``) of the analytics interface.

        Every analytics interface should have at least one *unique* scheme to
        use at the beginning of the analytics URI. To develop a new analytics
        interface, one needs to check public Kestrel analytics packages to name a
        new one that is not taken. Note that scheme defined here should be in
        lowercase, and Kestrel analytics manager will normalize schemes of incoming
        URIs into lowercase.

        Returns:
            [str]: A list of schemes; A URI with one of the scheme will be
            processed by this interface.

        """
        return []

    @staticmethod
    @abstractmethod
    def list_analytics(config):
        """List analytics names accessible from this interface.

        Args:
            config (dict): a layered list/dict that contains config for the
              interface and can be edited/updated by the interface.

        Returns:
            [str]: A list of analytics names accessible from this interface.

        """
        return []

    @staticmethod
    @abstractmethod
    def execute(uri, argument_variables, config, session_id=None, parameters=None):
        """Execute an analytics.

        An analytics updates argument variables in place with revised
        attributes or additional attributes computed. Therefore, there is no
        need to return any variable, but the optional display object can be
        returned if the analytics generate anything to be shown by the
        front-end, e.g., a visualization analytics.

        When realizing the execute() method of an analytics interface, one
        needs to realize the following functionalities:

            #. Execute the specified analytics.
            #. Keep track of input/output Kestrel variables
            #. Kestrel variable update (in most cases, this is done by the
               analytics interface; in some cases, an analytics may directly
               update the store).
            #. Prepare returned display object.

        Args:
            uri (str): the full URI including the scheme and analytics name.

            argument_variables ([kestrel.symboltable.variable.VarStruct]): the list of Kestrel variables as arguments.

            config (dict): a layered list/dict that contains config for the
              interface and can be edited/updated by the interface.

            session_id (str): id of the session, may be useful for analytics directly writing into the store.

            parameters (dict): analytics execution parameters in key-value pairs ``{"str":"str"}``.

        Returns:
            kestrel.codegen.display.AbstractDisplay: returned display or None.

        """
        return None
