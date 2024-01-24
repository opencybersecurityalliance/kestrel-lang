import logging
import atexit

from typing import Iterable
from typeguard import typechecked
from contextlib import AbstractContextManager
from uuid import UUID, uuid4
from pandas import DataFrame

from kestrel.ir.graph import IRGraph
from kestrel.frontend.parser import parse_kestrel
from kestrel.cache import AbstractCache, SqliteCache
from kestrel.interface.datasource import AbstractDataSourceInterface
from kestrel.interface.datasource.utils import get_interface_by_name


_logger = logging.getLogger(__name__)


@typechecked
class Session(AbstractContextManager):
    """Kestrel huntflow execution session"""

    def __init__(self):
        self.session_id: UUID = uuid4()
        self.irgraph: IRGraph = IRGraph()
        self.cache: AbstractCache = SqliteCache()

        # Datasource interfaces in this session
        # Cache is a special datasource interface and should always be added
        # TODO: other datasource interfaces to initialize/add if exist
        self.interfaces: Iterable[AbstractDataSourceInterface] = [self.cache]

    def execute(self, huntflow_block: str) -> Iterable[DataFrame]:
        """Execute a Kestrel huntflow block.

        Execute a Kestrel statement or multiple consecutive statements (a
        huntflow block) This method has the context of already executed
        huntflow blocks in this session, so all existing variables can be
        referred in the new huntflow block.

        Parameters:
            huntflow_block: the new huntflow block to be executed

        Yields:
            Evaluated result per Return instruction in the huntflow block
        """
        # TODO: return type generalization

        irgraph_new = parse_kestrel(huntflow_block)
        self.irgraph.update(irgraph_new)

        for ret in irgraph_new.get_returns():
            ret_df = None
            while ret_df is None:
                for g in self.irgraph.find_dependent_subgraphs_of_node(ret, self.cache):
                    interface = get_interface_by_name(g.interface, self.interfaces)
                    for iid, df in interface.evaluate_graph(g).items():
                        if g.interface != self.cache.name:
                            self.cache[iid] = df
                        if iid == ret.id:
                            ret_df = df
            else:
                yield ret_df

    def do_complete(self, huntflow_block: str, cursor_pos: int):
        """Kestrel code auto-completion.

        Parameters:
            huntflow_block: Kestrel code
            cursor_pos: the position to start completion (index in ``huntflow_block``)

        Returns:
            A list of suggested strings to complete the code
        """
        raise NotImplementedError()

    def close(self):
        """Explicitly close the session.

        This may be executed by a context manager or when the program exits.
        """
        # Note there are two conditions that trigger this function, so it is probably executed twice
        # Be careful to write the logic in this function to avoid deleting nonexist files/dirs
        if self.cache:
            del self.cache
            self.cache = None

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
