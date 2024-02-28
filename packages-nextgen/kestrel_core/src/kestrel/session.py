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
from kestrel.interface.datasource import AbstractDataSourceInterface
from kestrel.interface.datasource.manager import DataSourceManager
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
        self.interfaces: Iterable[AbstractDataSourceInterface] = [self.cache]

        # Load data sources and add to list
        data_source_manager = DataSourceManager()
        self.interfaces.extend(data_source_manager.interfaces())

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

        for ret in irgraph_new.get_returns():
            is_explain = isinstance(irgraph_new.get_trunk_n_branches(ret)[0], Explain)
            is_complete = False
            display = GraphExplanation([])
            cache = self.cache.get_virtual_copy() if is_explain else self.cache
            while not is_complete:
                for g in self.irgraph.find_dependent_subgraphs_of_node(ret, cache):
                    interface = get_interface_by_name(g.interface, self.interfaces)
                    # intermediate result dictionary
                    ird = (
                        interface.explain_graph(g)
                        if is_explain
                        else interface.evaluate_graph(g)
                    )
                    for iid, _display in ird.items():
                        if is_explain:
                            display.graphlets.append(_display)
                        else:
                            display = _display
                        if g.interface != cache.name:
                            cache[iid] = True
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
        if self.cache:
            del self.cache
            self.cache = None

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
