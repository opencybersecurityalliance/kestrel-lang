import logging
import atexit

from typing import Mapping
from typeguard import typechecked
from contextlib import AbstractContextManager
from uuid import UUID, uuid4

from kestrel.ir.graph import IRGraph
from kestrel.frontend.parser import parse_kestrel
from kestrel.cache import AbstractCache, SqliteCache
from kestrel.ir.instructions import Variable, CACHE_INTERFACE_IDENTIFIER
from kestrel.interface.datasource import AbstractDataSourceInterface


_logger = logging.getLogger(__name__)


@typechecked
class Session(AbstractContextManager):
    """Kestrel huntflow execution session"""

    def __init__(self):
        self.session_id: UUID = uuid4()
        self.irgraph: IRGraph = IRGraph()
        self.cache: AbstractCache = SqliteCache()

        # interface mapper
        # Select a datasource interface given its name
        # Note that cache is a special datasource interface and should always be added
        # TODO: other datasource interfaces to initialize/add if exist
        self.im: Mapping[str, AbstractDataSourceInterface] = {
            CACHE_INTERFACE_IDENTIFIER: self.cache
        }

    def execute(self, huntflow_block: str):
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
        irgraph_new = parse_kestrel(huntflow_block)
        self.irgraph.update(irgraph_new)

        for ret in irgraph_new.get_returns():
            while ret.id not in self.cache:
                for g in self.irgraph.find_dependent_subgraphs_of_node(ret, self.cache):
                    for iid, df in self.im[g.interface].evaluate_graph(g).items():
                        if g.interface != CACHE_INTERFACE_IDENTIFIER:
                            self.cache[iid] = df
            else:
                yield self.cache[ret.id]

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
