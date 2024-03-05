import logging
from contextlib import AbstractContextManager
from uuid import UUID, uuid4
from typing import Iterable
from typeguard import typechecked

from kestrel.display import Display, GraphExplanation
from kestrel.ir.graph import IRGraph
from kestrel.ir.instructions import Explain
from kestrel.frontend.parser import parse_kestrel
from kestrel.cache import AbstractCache, SqliteCache
from kestrel.config.internal import CACHE_INTERFACE_IDENTIFIER
from kestrel.interface import AbstractInterface, InterfaceManager


_logger = logging.getLogger(__name__)


@typechecked
class Session(AbstractContextManager):
    """Kestrel huntflow execution session"""

    def __init__(self):
        self.session_id = uuid4()
        self.irgraph = IRGraph()

        # load all interfaces; cache is a special interface
        cache = SqliteCache()
        self.interface_manager = InterfaceManager([cache])

    def execute(self, huntflow_block: str) -> Iterable[Display]:
        """Execute a Kestrel huntflow block.

        Execute a Kestrel statement or multiple consecutive statements (a
        huntflow block) This method has the context of already executed
        huntflow blocks in this session, so all existing variables can be
        referred in the new huntflow block.

        Parameters:
            huntflow_block: the new huntflow block to be executed

        Returns:
            Evaluated result per Return instruction
        """
        return list(self.execute_to_generate(huntflow_block))

    def execute_to_generate(self, huntflow_block: str) -> Iterable[Display]:
        """Execute a Kestrel huntflow and put results in a generator.

        Parameters:
            huntflow_block: the new huntflow block to be executed

        Yields:
            Evaluated result per Return instruction
        """

        irgraph_new = parse_kestrel(huntflow_block)
        self.irgraph.update(irgraph_new)

        # The current logic leads to caching results from non-cache and lastly
        # evaluate in cache.
        # TODO: may evaluate cache first, then push dependent variables to the
        # last interface to eval; this requires priority of interfaces
        for ret in irgraph_new.get_returns():
            pred = irgraph_new.get_trunk_n_branches(ret)[0]
            is_explain = isinstance(pred, Explain)
            is_complete = False
            display = GraphExplanation([])
            interface_manager = (
                self.interface_manager.copy_with_virtual_cache()
                if is_explain
                else self.interface_manager
            )
            cache = interface_manager[CACHE_INTERFACE_IDENTIFIER]
            while not is_complete:
                for g in self.irgraph.find_dependent_subgraphs_of_node(ret, cache):
                    interface = interface_manager[g.interface]
                    for iid, _display in (
                        interface.explain_graph(g)
                        if is_explain
                        else interface.evaluate_graph(g)
                    ).items():
                        if is_explain:
                            display.graphlets.append(_display)
                        else:
                            display = _display
                        if interface is not cache:
                            cache[iid] = display
                        if iid == ret.id:
                            is_complete = True
            else:
                yield display

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
        if CACHE_INTERFACE_IDENTIFIER in self.interface_manager:
            self.interface_manager.del_cache()

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
