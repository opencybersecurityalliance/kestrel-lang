from __future__ import annotations
from typeguard import typechecked
from typing import (
    Iterable,
    Tuple,
    Mapping,
    Union,
    Optional,
)
from collections import defaultdict
from itertools import combinations
from uuid import UUID
import networkx
import json

from kestrel.ir.instructions import (
    Instruction,
    TransformingInstruction,
    SourceInstruction,
    Variable,
    Source,
    Reference,
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
    DuplicatedSourceInstruction,
    MultiInterfacesInGraph,
)


@typechecked
def compose(g: IRGraph, h: IRGraph) -> IRGraph:
    g.update(h)
    return g


@typechecked
def union(g: IRGraph, h: IRGraph) -> IRGraph:
    return compose(g, h)


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

    def add_node(
        self, node: Instruction, dependent_node: Union[Instruction, None] = None
    ) -> Instruction:
        """General adding node/instruction operation

        Parameters:
            node: the instruction to add
            dependent_node: the dependent instruction if node is a TransformingInstruction

        Returns:
            The node added
        """
        if node not in self:
            if isinstance(node, TransformingInstruction):
                self.add_node_with_dependent_node(node, dependent_node)
            else:
                self._add_single_node(node)
        return node

    def _add_single_node(self, node: Instruction, deref: bool = True) -> Instruction:
        # test in self.nodes() is important
        # there could be a Reference node already in graph, not to deref
        if node not in self:
            if isinstance(node, SourceInstruction):
                if isinstance(node, Reference) and deref:
                    try:
                        v = self.get_variable(node.name)
                    except:
                        node = self._add_sourceinstruction(node)
                    else:
                        node = v
                else:
                    node = self._add_sourceinstruction(node)
            else:
                super().add_node(node)
        return node

    def copy(self):
        """Copy the IRGraph with all nodes as reference (not deepcopy)"""
        g = IRGraph()
        g.update(self)
        return g

    def deepcopy(self):
        """Copy the IRGraph with all nodes copied as new objects"""
        g = IRGraph()
        o2n = {n: n.deepcopy() for n in self.nodes()}
        for u, v in self.edges():
            g.add_edge(o2n[u], o2n[v])
        return g

    def _get_sourceinstruction(self, node: SourceInstruction) -> SourceInstruction:
        xs = self.get_nodes_by_type(SourceInstruction)
        xs = [s for s in xs if s.is_same_as(node)]
        if xs:
            if len(xs) > 1:
                raise DuplicatedSourceInstruction(node)
            else:
                return xs.pop()
        else:
            raise InstructionNotFound(node)

    def _add_sourceinstruction(self, node: SourceInstruction) -> SourceInstruction:
        try:
            s = self._get_sourceinstruction(node)
        except InstructionNotFound:
            super().add_node(node)
        else:
            node = s
        return node

    def add_nodes_from(self, nodes: Iterable[Instruction], deref: bool = True):
        """Add nodes in a list

        Parameters:
            nodes: the list of nodes/instructions to add
            deref: whether to deref Reference node
        """
        for node in nodes:
            self._add_single_node(node, deref)

    def add_edge(self, u: Instruction, v: Instruction, deref: bool = False):
        """Add edge (add node if not exist)

        Parameters:
            u: the source of the edge
            v: the target of the edge
            deref: whether to deref Reference node
        """
        ux = self._add_single_node(u, deref)
        vx = self._add_single_node(v, deref)
        super().add_edge(ux, vx)

    def add_edges_from(
        self, edges: Iterable[Tuple[Instruction, Instruction]], deref: bool = False
    ):
        """Add edges in a list

        Parameters:
            edges: the edges to add
            deref: whether to deref Reference node
        """
        for u, v in edges:
            self.add_edge(u, v, deref)

    def get_node_by_id(self, ux: Union[UUID, str]) -> Instruction:
        """Get node by ID

        Parameters:
            ux: node ID

        Returns:
            The Kestrel instruction (node in IRGraph)
        """
        u = UUID(ux) if isinstance(ux, str) else ux
        try:
            return next(filter(lambda n: n.id == u, self.nodes()))
        except StopIteration:
            raise InstructionNotFound(u)

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

        This method returns a list of variables, equivalent to *Symbol Table* used in traditional (non-graph-IR) language compilers. Shadowed variables (replaced by new variables with same names) will not be returned.

        Returns:
            The list of all Kestrel variables in this huntflow.
        """
        var_names = {v.name for v in self.get_nodes_by_type(Variable)}
        return [self.get_variable(var_name) for var_name in var_names]

    def get_variable(self, var_name: str) -> Variable:
        """Get a Kestrel variable by its name

        Parameters:
            var_name: variable name

        Returns:
            The Kestrel variable given its name
        """
        xs = self.get_nodes_by_type_and_attributes(Variable, {"name": var_name})
        if xs:
            if len({x.version for x in xs}) < len(xs):
                raise DuplicatedVariable(var_name)
            else:
                xs.sort(key=lambda x: x.version)
                return xs[-1]
        else:
            raise VariableNotFound(var_name)

    def add_variable(
        self, vx: Union[str, Variable], dependent_node: Instruction
    ) -> Variable:
        """Create new variable (if needed) and add to IRGraph

        Parameters:
            vx: variable name (str) or already created node (Variable)
            dependent_node: the instruction to which the variable refer

        Returns:
            The variable node created/added
        """
        if dependent_node not in self:
            raise InstructionNotFound(dependent_node)

        v = Variable(vx) if isinstance(vx, str) else vx
        if v not in self:
            try:
                ve = self.get_variable(v.name)
            except VariableNotFound:
                pass
            else:
                v.version = ve.version + 1

            # add_edge will add node v
            self.add_edge(dependent_node, v)
        return v

    def get_sources(self) -> Iterable[Source]:
        """Get all datasources

        Returns:
            The list of data sources
        """
        return self.get_nodes_by_type(Source)

    def get_source(self, interface: str, datasource: str) -> Source:
        """Get a Kestrel datasource by its URI

        Parameters:
            interface: the datasource interface name
            datasource: the datasource name under the interface

        Returns:
            The datasource
        """
        xs = self.get_nodes_by_type_and_attributes(
            Source, {"interface": interface, "datasource": datasource}
        )
        if xs:
            if len(xs) > 1:
                raise DuplicatedSourceInstruction(interface, datasource)
            else:
                return xs.pop()
        else:
            raise SourceNotFound(interface, datasource)

    def add_source(
        self, sx: Union[str, Source], default_interface: Optional[str] = None
    ) -> Source:
        """Create new datasource (if needed) and add to IRGraph if not exist

        Parameters:
            sx: the full URI of the datasource (str) or already created node (Source)
            default_interface: default interface name

        Returns:
            The Source node found or added
        """
        sy = source_from_uri(sx, default_interface) if isinstance(sx, str) else sx
        return self.add_node(sy)

    def add_node_with_dependent_node(
        self, node: Instruction, dependent_node: Instruction
    ) -> Instruction:
        """Add node to graph with a dependent node

        Parameters:
            node: the node/instruction to add
            dependent_node: the dependent node that should exist in the graph

        Return:
            The node added
        """
        if dependent_node not in self:
            raise InstructionNotFound(dependent_node)
        if node not in self:
            if isinstance(node, Variable):
                # require special setup
                self.add_variable(node, dependent_node)
            else:
                # add_edge will add node first
                self.add_edge(dependent_node, node)
        return node

    def update(self, ng: IRGraph):
        """Extend the current IRGraph with a new IRGraph

        Parameters:
            ng: the new IRGraph to merge/combine/union
        """
        # After we add new variable nodes, we can no longer rely on
        # self.get_variable() to get variables for de-referencing.
        # Save the original variables first.
        original_variables = {v.name: v for v in self.get_variables()}

        # prepare new variables from ng before merge
        for nv in ng.get_nodes_by_type(Variable):
            if nv.name in original_variables:
                nv.version += original_variables[nv.name].version + 1

        edges = []
        for u, v in ng.edges():
            # deref all Reference edge in read-only mode
            # do not do it during adding edges/nodes (variables in self will change)
            if isinstance(u, Reference):
                try:
                    w = self.get_variable(u.name)
                except:
                    w = self._add_sourceinstruction(u)
            else:
                w = u
            edges.append((w, v))

        # merge all edges (and add nodes if needed)
        self.add_edges_from(edges)

    def duplicate_dependent_subgraph_of_node(self, node: Instruction) -> IRGraph:
        """Find and copy the dependent subgraph of a node (including the node)

        Parameters:
            node: instruction node to start

        Returns:
            A copy of the dependent subgraph (including the input node)
        """
        nodes = networkx.ancestors(self, node)
        nodes.add(node)
        return self.subgraph(nodes).copy()

    def find_cached_dependent_subgraph_of_node(
        self, node: Instruction, cache: Cache
    ) -> IRGraph:
        """Return the cached dependent graph of the a node

        Discard nodes and subgraphs before any cached Variable nodes.

        Returns:
            The pruned IRGraph without nodes before cached Variable nodes
        """
        g = self.duplicate_dependent_subgraph_of_node(node)
        in_edges = [g.in_edges(n) for n in g.get_variables() if n.id in cache]
        g.remove_edges_from(set().union(*in_edges))

        # important last step to discard any unconnected nodes/subgraphs prior to the dropped edges
        return g.duplicate_dependent_subgraph_of_node(node)

    def find_simple_dependent_subgraphs_of_node(
        self, node: Return, cache: Cache
    ) -> Iterable[IRGraphSoleInterface]:
        """Segment dependent graph of a node and return subgraphs that do not have further dependency

        To evaluate a node, one needs to evaluate all nodes in its dependent
        graph. However, not all nodes can be evaluated at once. Some require
        more basic dependent subgraphs to be evaluated first. This method
        segments the dependent graph of a node and return the subgraphs that
        are IRGraphSoleInterface. One can evaluate the returns, cache them, and
        call this function again. After iterations of return and evaluation of
        the dependent subgraphs, the node can finally be evaluated in the last
        return, which will just be a IRGraphSoleInterface at that time.

        TODO: analytics node support

        Parameters:
            node: a Return instruction node
            cache: Kestrel cache for the session

        Returns:
            List of simple subgraphs, each of which has zero or one interface

        """

        simple_dependent_subgraphs = []
        cached_dependent_graph = self.find_cached_dependent_subgraph_of_node(
            node, cache
        )

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
                source_affected_nodes.add(source)
                affected_nodes_by_interface[interface].update(source_affected_nodes)

        # find all nodes not affected by any interface
        # put them (may not be fully connected) into one IRGraphSoleInterface
        interface_affected_nodes = set().union(*affected_nodes_by_interface.values())
        non_interface_nodes = cached_dependent_graph.nodes() - interface_affected_nodes
        if non_interface_nodes:
            simple_dependent_subgraphs.append(
                cached_dependent_graph.subgraph(non_interface_nodes).copy()
            )

        # find all nodes that are affected by two or more interfaces
        shared_affected_nodes = set().union(
            *[
                set.intersection(
                    affected_nodes_by_interface[ix], affected_nodes_by_interface[iy]
                )
                for ix, iy in combinations(affected_nodes_by_interface.keys(), 2)
            ]
        )

        # per interface:
        # - find nodes affected only by each interface
        # - get their subgraph
        # - put such subgraph into IRGraphSoleInterface
        for interface, affected_nodes in affected_nodes_by_interface.items():
            unshared_nodes = affected_nodes - shared_affected_nodes
            if len(unshared_nodes) > 1:
                simple_dependent_subgraphs.append(
                    IRGraphSoleInterface(
                        cached_dependent_graph.subgraph(unshared_nodes).copy()
                    )
                )

        return simple_dependent_subgraphs

    def to_dict(self) -> Mapping[str, Iterable[Mapping]]:
        """Serialize to a Python dictionary (D3 graph format)

        Returns:
            The graph in a Python dictionary to be dumped as JSON string
        """
        nodes = [n.to_dict() for n in self.nodes()]
        links = [{"source": str(u.id), "target": str(v.id)} for (u, v) in self.edges()]
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
        edges = graph_in_dict["links"]
        for n in nodes:
            self._add_single_node(instruction_from_dict(n), False)
        for e in edges:
            try:
                u = self.get_node_by_id(e["source"])
                v = self.get_node_by_id(e["target"])
            except InstructionNotFound as err:
                raise InvalidSeralizedGraph()
            else:
                self.add_edge(u, v)


@typechecked
class IRGraphSoleInterface(IRGraph):
    """Sole-Interface IRGraph

    Sole-interface IRGraph is an IRGraph either:
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

    def _add_single_node(self, node: Instruction):
        if isinstance(node, Source):
            if self.interface and node.interface != self.interface:
                raise MultiInterfacesInGraph([self.interface, node.interface])
        super()._add_single_node(node)
