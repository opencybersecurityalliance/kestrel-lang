from __future__ import annotations
from typeguard import typechecked
from typing import (
    Iterable,
    Tuple,
    Mapping,
    Union,
    TypedDict,
)
from collections import defaultdict
from itertools import combinations
import networkx
import json

from kestrel.ir.instructions import (
    Instruction,
    Variable,
    Source,
    Return,
    instruction_from_dict,
    source_from_uri,
)
from kestrel.cache import Cache
from kestrel.exceptions import (
    InstructionNotFound,
    InvalidSeralizedGraph,
    VariableNotFound,
    SourceNotFound,
    DuplicatedVariable,
    DuplicatedDataSource,
    MultiInterfacesInGraph,
)


@typechecked
class IRGraph(networkx.DiGraph):
    def __init__(
        self, serialized_graph: Union[None, str, Mapping[str, Iterable[Mapping]]] = None
    ):
        super().__init__()
        if serialized_graph:
            if isinstance(serialized_graph, str):
                graph_in_dict = json.loads(serialized_graph)
            else:
                graph_in_dict = serialized_graph
            self._from_dict(graph_in_dict)

    def add_node(self, node: Instruction):
        super().add_node(node)

    def add_nodes_from(self, nodes: Iterable[Instruction]):
        super().add_nodes_from(nodes)

    def add_edge(self, u: Instruction, v: Instruction):
        super().add_edge(u, v)

    def add_edges_from(self, edges: Iterable[Tuple[Instruction, Instruction]]):
        super().add_edge(edges)

    def get_node_by_id(self, id_val: int) -> Instruction:
        """Get node by ID

        Parameters:
            id_val: node ID

        Returns:
            The Kestrel instruction (node in IRGraph)
        """
        try:
            return next(filter(lambda n: n.id == id_val, self.nodes()))
        except StopIteration:
            raise InstructionNotFound(id_val)

    def get_nodes_by_type(self, ntype: type) -> Iterable[Instruction]:
        """Get nodes by type

        Parameters:
            ntype: node/instruction type

        Returns:
            The list of nodes/instructions
        """
        return [n for n in self.nodes() if isinstance(n, ntype)]

    def get_nodes_by_type_and_attributes(
        self, ntype: type, attr2val: Mapping[str, Union[str, bool]]
    ) -> Iterable[Instruction]:
        """Get nodes by both type and attributes/values

        Parameters:
            ntype: node/instruction type
            attr2val: instruction attribute/value dictionary

        Returns:
            The list of nodes/instructions
        """
        nodes = self.get_nodes_by_type(ntype)
        return [
            n
            for n in nodes
            if all([getattr(n, k, None) == v for (k, v) in attr2val.items()])
        ]

    def get_variables(self) -> Iterable[Variable]:
        """Get all variables

        This method returns a list of variables, equivalent to *Symbol Table* used in traditional (non-graph-IR) language compilers.

        Returns:
            The list of all Kestrel variables in this huntflow.
        """
        return self.get_nodes_by_type(Variable)

    def get_variable(self, var_name: str) -> Variable:
        """Get a Kestrel variable by its name

        Parameters:
            var_name: variable name

        Returns:
            The Kestrel variable given its name
        """
        xs = self.get_nodes_by_type_and_attributes(
            Variable, {"name": var_name, "deceased": False}
        )
        if xs:
            if len(xs) > 1:
                raise DuplicatedVariable(var_name)
            else:
                return xs.pop()
        else:
            raise VariableNotFound(var_name)

    def add_variable(self, var_name: str, dependent_node: Instruction) -> Variable:
        """Create new variable and add to IRGraph

        Parameters:
            var_name: variable name
            dependent_node: the instruction to which the variable refer

        Returns:
            The new variable node created/added
        """
        try:
            ve = self.get_variable(var_name)
        except VariableNotFound:
            pass
        else:
            ve.deceased = True
        v = Variable(var_name)
        self.add_node(v)
        self.add_edge(dependent_node, v)
        return v

    def get_sources(self) -> Iterable[Source]:
        """Get all datasources

        Returns:
            The list of data sources
        """
        return self.get_nodes_by_type(Source)

    def get_source(self, interface: str, datasource: str) -> Souce:
        """Get a Kestrel datasource by its URI

        Parameters:
            interface: the datasource interface name
            datasource: the datasource name under the interface

        Returns:
            The datasource
        """
        xs = self.get_nodes_by_type_and_attributes(Source, {"interface", interface, "datasource": datasource})
        if xs:
            if len(xs) > 1:
                raise DuplicatedDataSource(interface, datasource)
            else:
                return xs.pop()
        else:
            raise SourceNotFound(interface, datasource)

    def add_source(self, uri: str, default_interface: Optional[str]=None) -> Source:
        """Create new datasource and add to IRGraph if not exist

        Parameters:
            uri: the full URI of the datasource
            default_interface: default interface name

        Returns:
            The Source node found or added
        """
        s = source_from_uri(uri, default_interface)
        try:
            _s = self.get_source(s.interface, s.datasource)
        except SourceNotFound:
            self.add_node(s)
        return _s

    def cached_dependent_graph_of_node(
        self, node: Instruction, cache: Cache
    ) -> IRGraph:
        """Return the cached dependent graph of the a node

        Discard nodes and subgraphs before any cached Variable nodes.

        Returns:
            The pruned IRGraph without nodes before cached Variable nodes
        """
        g = self.subgraph(networkx.ancestors(self, node)).copy()
        for n in g.get_variables():
            if n.id in cache:
                g.remove_edges_from(g.in_edges(n))

        # important last step to discard any unconnected nodes/subgraphs prior to the dropped edges
        return g.subgraph(networkx.ancestors(g, node))

    def find_simple_dependent_subgraphs_of_node(
        self, node: Return, cache: Cache
    ) -> Iterable[IRGraphSimple]:
        """Segment dependent graph of a node and return subgraphs that do not have further dependency

        To evaluate a node, one needs to evaluate all nodes in its dependent
        graph. However, not all nodes can be evaluated at once. Some require
        more basic dependent subgraphs to be evaluated first. This method
        segments the dependent graph of a node and return the subgraphs that
        are IRGraphSimple. One can evaluate the returns, cache them, and call
        this function again. After iterations of return and evaluation of the
        dependent subgraphs, the node can finally be evaluated in the last
        return, which will just be a IRGraphSimple at that time.

        TODO: analytics node support

        Parameters:
            node: a Return instruction node
            cache: Kestrel cache for the session

        Returns:
            List of simple subgraphs, each of which has zero or one interface

        """

        simple_dependent_subgraphs = []
        cached_dependent_graph = self.cached_dependent_graph_of_node(node, cache)

        interface2source = defaultdict(list)
        for source in cached_dependent_graph.get_nodes_by_type(Source):
            interface2source[source.interface].append(source)

        # find nodes affected by each interface
        affected_nodes_by_interface = defaultdict(set)
        for interface, sources in interface2source.items():
            for source in sources:
                source_affected_nodes = networkx.descendants(
                    cached_dependent_graph, source
                )
                affected_nodes_by_interface[interface].update(source_affected_nodes)

        # find all nodes not affected by any interface
        # put them (may not be fully connected) into one IRGraphSimple
        all_interface_affected_nodes = set()
        for nodes in affected_nodes_by_interface.values():
            all_interface_affected_nodes.update(nodes)
        non_interface_nodes = (
            cached_dependent_graph.nodes() - all_interface_affected_nodes
        )
        if non_interface_nodes:
            non_interface_subgraph = cached_dependent_graph.subgraph(
                non_interface_nodes
            )
            simple_dependent_subgraphs.append(non_interface_subgraph)

        # find all nodes that are affected by more than two interfaces
        shared_affected_nodes = set()
        for ix, iy in combinations(affected_nodes_by_interface.keys(), 2):
            shared_nodes_between_two = set.intersection(
                affected_nodes_by_interface[ix], affected_nodes_by_interface[iy]
            )
            shared_affected_nodes.update(shared_nodes_between_two)

        # per interface:
        # - find nodes affected only by each interface
        # - get their subgraph
        # - put such subgraph into IRGraphSimple
        for interface, affected_nodes in affected_nodes_by_interface:
            unshared_nodes = affected_nodes - shared_affected_nodes
            if len(unshared_nodes) > 1:
                sg = IRGraphSimple(cached_dependent_graph.subgraph(unshared_nodes))
                simple_dependent_subgraphs.append(sg)

        return simple_dependent_subgraphs

    def to_dict(self) -> Mapping[str : Iterable[Mapping]]:
        """Serialize to a Python dictionary (D3 graph format)

        Returns:
            The graph in a Python dictionary to be dumped as JSON string
        """
        nodes = [n.to_dict() for n in self.nodes()]
        links = [{"source": u.id, "target": v.id} for (u, v) in self.edges()]
        return {"nodes": nodes, "links": links}

    def to_json(self) -> str:
        """Serialize to a Python JSON string (D3 graph format)

        Returns:
            The graph in a Python JSON string
        """
        return json.dumps(self.to_dict())

    def _from_dict(self, graph_in_dict: Mapping[str, Iterable[Mapping]]):
        """Deserialize from a Python dictionary (D3 graph format)

        This method is an implicit constructor from a serialized graph.

        Parameters:
            graph_in_dict: the serialized graph in Python dictionary
        """
        nodes = graph_in_dict["nodes"]
        edges = graph_in_dict["edges"]
        for n in nodes:
            self.add_node(instruction_from_dict(n))
        for e in edges:
            try:
                u = self.get_node_by_id(e["source"])
                v = self.get_node_by_id(e["target"])
            except InstructionNotFound as err:
                raise InvalidSeralizedGraph()
            else:
                self.add_edge(u, v)


@typechecked
class IRGraphSimple(IRGraph):
    """Simple IRGraph

    Simple IRGraph is an IRGraph either:
    - It does not has any Source node
    - All its Source nodes share the same datasource interface

    """

    def __init__(self, graph: IRGraph):
        interfaces = {source.interface for source in graph.get_nodes_by_type(Source)}
        if len(interfaces) > 1:
            raise MultiInterfacesInGraph(interfaces)
        else:
            self = graph.copy()
            self.interface = interfaces.pop() if interfaces else None

    def add_node(self, node: Instruction):
        if isinstance(node, Source):
            if self.interface and node.interface != self.interface:
                raise MultiInterfacesInGraph([self.interface, node.interface])
        super().add_node(node)
