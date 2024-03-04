from __future__ import annotations
from typeguard import typechecked
from typing import Any, Iterable, Tuple, Mapping, MutableMapping, Union, Optional
from collections import defaultdict
from itertools import combinations
from uuid import UUID
import networkx
import json
from kestrel.ir.instructions import (
    Instruction,
    TransformingInstruction,
    SolePredecessorTransformingInstruction,
    IntermediateInstruction,
    SourceInstruction,
    Variable,
    DataSource,
    Reference,
    Return,
    Filter,
    ProjectAttrs,
    instruction_from_dict,
)
from kestrel.ir.filter import ReferenceValue
from kestrel.exceptions import (
    InstructionNotFound,
    InvalidSeralizedGraph,
    VariableNotFound,
    ReferenceNotFound,
    DataSourceNotFound,
    DuplicatedVariable,
    DuplicatedReference,
    DuplicatedDataSource,
    DuplicatedSingletonInstruction,
    MultiInterfacesInGraph,
    MultiSourcesInGraph,
    InevaluableInstruction,
    LargerThanOneIndegreeInstruction,
    DuplicatedReferenceInFilter,
    MissingReferenceInFilter,
    DanglingReferenceInFilter,
    DanglingFilter,
)
from kestrel.config.internal import CACHE_INTERFACE_IDENTIFIER


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
        self,
        node: Instruction,
        dependent_node: Optional[Instruction] = None,
        deref: bool = True,
    ) -> Instruction:
        """General adding node/instruction operation

        Parameters:
            node: the instruction to add
            dependent_node: the dependent instruction if node is a TransformingInstruction
            deref: whether to dereference Reference instruction (only useful for if node is Reference)

        Returns:
            The node added
        """
        if node not in self:
            if isinstance(node, TransformingInstruction):
                node = self._add_node_with_dependent_node(node, dependent_node)
            else:
                node = self._add_node(node, deref)
        return node

    def add_nodes_from(self, nodes: Iterable[Instruction], deref: bool = True):
        """Add nodes in a list

        Parameters:
            nodes: the list of nodes/instructions to add
            deref: whether to deref Reference node
        """
        for node in nodes:
            self._add_node(node, deref)

    def add_edge(self, u: Instruction, v: Instruction, deref: bool = False):
        """Add edge (add node if not exist)

        Parameters:
            u: the source of the edge
            v: the target of the edge
            deref: whether to deref Reference node
        """
        ux = self._add_node(u, deref)
        vx = self._add_node(v, deref)
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

    def copy(self):
        """Copy the IRGraph with all nodes as reference (not deepcopy)

        Support subclass of IRGraph to be copied.
        """
        g = IRGraph()
        g.update(self)

        # subclass support
        if type(g) != type(self):
            g = type(self)(g)

        return g

    def deepcopy(self):
        """Copy the IRGraph with all nodes copied as new objects

        Support subclass of IRGraph to be deep copied.
        """
        g = IRGraph()
        o2n = {n: n.deepcopy() for n in self.nodes()}
        for u, v in self.edges():
            g.add_edge(o2n[u], o2n[v])
        g.add_nodes_from([o2n[n] for n in self.nodes() if self.degree(n) == 0])

        # subclass support
        if type(g) != type(self):
            g = type(self)(g)

        return g

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
        self, ntype: type, attr2val: Mapping[str, Union[str, bool, int]]
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

    def get_variables(self) -> Iterable[Variable]:
        """Get all variables

        This method returns a list of variables, equivalent to *Symbol Table* used in traditional (non-graph-IR) language compilers. Shadowed variables (replaced by new variables with same names) will not be returned.

        Returns:
            The list of all Kestrel variables in this huntflow.
        """
        var_names = {v.name for v in self.get_nodes_by_type(Variable)}
        return [self.get_variable(var_name) for var_name in var_names]

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
        v = Variable(vx) if isinstance(vx, str) else vx
        return self.add_node(v, dependent_node)

    def get_reference(self, ref_name: str) -> Reference:
        """Get a Kestrel reference by its name

        Parameters:
            ref_name: reference name

        Returns:
            The Reference node
        """
        xs = self.get_nodes_by_type_and_attributes(Reference, {"name": ref_name})
        if xs:
            if len(xs) > 1:
                raise DuplicatedReference(ref_name)
            else:
                return xs.pop()
        else:
            raise ReferenceNotFound(ref_name)

    def get_references(self) -> Iterable[Reference]:
        """Get all references

        Returns:
            The list of reference nodes
        """
        ref_names = {r.name for r in self.get_nodes_by_type(Reference)}
        return [self.get_reference(ref_name) for ref_name in ref_names]

    def add_reference(
        self, rx: Union[str, Reference], deref: bool = True
    ) -> Union[Reference, Variable]:
        """Create or add new reference node to IRGraph

        The reference node will be derefed if the flag is specified.

        Parameters:
            rx: reference name (str) or already created node (Reference)
            deref: whether to deref when adding node

        Returns:
            The reference node created/added
        """
        r = Reference(rx) if isinstance(rx, str) else rx
        return self.add_node(r, deref)

    def get_datasource(self, interface: str, datasource: str) -> DataSource:
        """Get a Kestrel datasource by its URI

        Parameters:
            interface: the datasource interface name
            datasource: the datasource name under the interface

        Returns:
            The datasource
        """
        xs = self.get_nodes_by_type_and_attributes(
            DataSource, {"interface": interface, "datasource": datasource}
        )
        if xs:
            if len(xs) > 1:
                raise DuplicatedDataSource(interface, datasource)
            else:
                return xs.pop()
        else:
            raise DataSourceNotFound(interface, datasource)

    def get_datasources(self) -> Iterable[DataSource]:
        """Get all datasources

        Returns:
            The list of data sources
        """
        xs = self.get_nodes_by_type(DataSource)

        # to check for duplicated datasources

        return xs

    def add_datasource(
        self, sx: Union[str, DataSource], default_interface: Optional[str] = None
    ) -> DataSource:
        """Create new datasource (if needed) and add to IRGraph if not exist

        Parameters:
            sx: the full URI of the datasource (str) or already created node (DataSource)
            default_interface: default interface name

        Returns:
            The DataSource node found or added
        """
        s = DataSource(sx, default_interface) if isinstance(sx, str) else sx
        return self.add_node(s)

    def get_returns(self) -> Iterable[Return]:
        """Get all return nodes

        Returns:
            The list of return nodes
        """
        return sorted(self.get_nodes_by_type(Return), key=lambda x: x.sequence)

    def get_max_return_sequence(self) -> int:
        """Get the largest sequence number of all Returns

        Returns:
            The largest sequence number of all Return instruction
        """
        return max(map(lambda x: x.sequence, self.get_returns()), default=-1)

    def add_return(self, dependent_node: Instruction) -> Return:
        """Create new Return instruction and add to IRGraph

        Parameters:
            dependent_node: the instruction to hold return

        Returns:
            The return node created/added
        """
        return self.add_node(Return(), dependent_node)

    def get_sink_nodes(self) -> Iterable[Instruction]:
        """Get all sink nodes (node with no successors)

        Returns:
            The list of sink nodes
        """
        return [n for n in self.nodes() if self.out_degree(n) == 0]

    def get_trunk_n_branches(
        self, node: TransformingInstruction
    ) -> (Instruction, Mapping[ReferenceValue, Instruction]):
        """Get the trunk and branches paths for instruction

        For trunk path, return the tail node; for each branch, return the tail
        node of the branchin mapping from reference to node.

        Parameters:
            node: the instruction node

        Returns:
            (tail node for trunk, ref to branch tail node mapping)
        """
        ps = list(self.predecessors(node))
        pps = [(p, pp) for p in self.predecessors(node) for pp in self.predecessors(p)]

        # may need to add a patch in find_dependent_subgraphs_of_node()
        # for each new case added in the if/elif, e.g., FIlter
        if isinstance(node, SolePredecessorTransformingInstruction):
            if len(ps) > 1:
                raise LargerThanOneIndegreeInstruction()
            else:
                return ps[0], {}
        elif isinstance(node, Filter):
            r2n = {}
            for rv in node.get_references():
                ppfs = [
                    (p, pp)
                    for p, pp in pps
                    if isinstance(p, ProjectAttrs)
                    and isinstance(pp, (Variable, Reference))
                    and p.attrs == [rv.attribute]
                    and pp.name == rv.reference
                ]
                if not ppfs:
                    raise MissingReferenceInFilter(rv, node, pps)
                elif len(ppfs) > 1:
                    raise DuplicatedReferenceInFilter(rv, node, pps)
                else:
                    p = ppfs[0][0]
                    r2n[rv] = p
                    ps.remove(p)
            if len(ps) == 0:
                raise DanglingFilter()
            elif len(ps) > 1:
                raise DanglingReferenceInFilter(ps)
            return ps[0], r2n
        else:
            raise NotImplementedError(f"unknown instruction type: {node}")

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
        # should not use ng.get_variable(),
        # which does not cover all overridden variables
        for nv in ng.get_nodes_by_type(Variable):
            if nv.name in original_variables:
                nv.version += original_variables[nv.name].version + 1

        # prepare return sequence from ng before merge
        return_max_sequence = self.get_max_return_sequence()
        for nr in ng.get_returns():
            nr.sequence += return_max_sequence + 1

        # add refs first to deref correctly
        # if any reference exist, it should be derefed before adding any variable
        o2n_refs = {n: self._add_node(n) for n in ng.get_references()}
        # add all nodes with dedup singleton node, e.g., SourceInstruction
        o2n_nonrefs = {n: self._add_node(n) for n in ng.nodes() if n not in o2n_refs}

        # overall old to new node mapping
        o2n = {}
        o2n.update(o2n_refs)
        o2n.update(o2n_nonrefs)

        # add all edges
        self.add_edges_from([(o2n[u], o2n[v]) for (u, v) in ng.edges()])

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
        self, node: Instruction, cache: MutableMapping[UUID, Any]
    ) -> IRGraph:
        """Return the cached dependent graph of the a node

        Discard nodes and subgraphs before any cached nodes, e.g., Variables.

        Parameters:
            node: instruction node to start
            cache: any type of node cache, e.g., content, SQL statement

        Returns:
            The pruned IRGraph without nodes before cached Variable nodes
        """
        g = self.duplicate_dependent_subgraph_of_node(node)
        in_edges = [g.in_edges(n) for n in g.nodes() if n.id in cache]
        g.remove_edges_from(set().union(*in_edges))

        # important last step to discard any unconnected nodes/subgraphs prior to the dropped edges
        return g.duplicate_dependent_subgraph_of_node(node)

    def find_dependent_subgraphs_of_node(
        self,
        node: Instruction,
        cache: MutableMapping[UUID, Any],
    ) -> Iterable[IRGraphEvaluable]:
        """Find dependency subgraphs that do not have further dependency

        To evaluate a node, one needs to evaluate all nodes in its dependent
        graph. However, not all nodes can be evaluated at once (e.g., impacted
        by multiple interfaces). Some require more basic dependent subgraphs to
        be evaluated first. This method segments the dependent graph of a node
        and return the subgraphs that are IRGraphEvaluable. One can evaluate
        the returns, cache them, and call this method again. After iterations
        of return and evaluation of returned dependent subgraphs, the node can
        finally be evaluated in the last return, which will just be a
        IRGraphEvaluable at that time.

        TODO: analytics node support

        Parameters:
            node: the instruction/node to generate dependent subgraphs for
            cache: any type of node cache, e.g., content, SQL statement

        Returns:
            A list of subgraphs that do not have further dependency
        """
        _CII = CACHE_INTERFACE_IDENTIFIER

        # the base graph to segment
        g = self.find_cached_dependent_subgraph_of_node(node, cache)

        # Mapping: {interface name: [impacted nodes]}
        a2ns = defaultdict(set)
        for n in g.get_nodes_by_type(SourceInstruction):
            a2ns[n.interface].add(n)
            a2ns[n.interface].update(networkx.descendants(g, n))

        # all predecessor nodes to any interface impacted nodes
        pns = set().union(*[set(g.predecessors(n)) for ns in a2ns.values() for n in ns])

        # add non-source nodes to cache as default execution environment
        # e.g., a path starting from a cached Variable
        # nodes directly preceeding an interface impacted node do not need evaluation
        cached_nodes = set([n for n in g.nodes() if n.id in cache])
        for n in cached_nodes - pns:
            a2ns[_CII].add(n)
            a2ns[_CII].update(networkx.descendants(g, n))

        # find all nodes that are affected by two or more interfaces
        shared_impacted_nodes = set().union(
            *[a2ns[ix] & a2ns[iy] for ix, iy in combinations(a2ns.keys(), 2)]
        )

        # unshared nodes for each interface
        a2uns = {k: v - shared_impacted_nodes for k, v in a2ns.items()}

        # handle direct predecessor node cached
        # such nodes are required in building dep graphs around interfaces
        # such nodes could be shared by multiple interfaces; can only handle now
        for interface in set(a2uns) - set([_CII]):
            ps = set().union(*[set(g.predecessors(n)) for n in a2uns[interface]])
            a2uns[interface].update(ps & cached_nodes)

        # a patch (corner case handling) for get_trunk_n_branches()
        # add Variable/Reference node if succeeded by ProjectAttrs and Filter,
        # which are in the dependent graph; the Variable is only needed by
        # get_trunk_n_branches() as an auxiliary node
        for interface in a2uns:
            auxs = []
            for n in a2uns[interface]:
                if isinstance(n, ProjectAttrs):
                    # need to search in `self`, not `g`, since the boundry of
                    # `g` is cut by the cache
                    p = next(self.predecessors(n))
                    s = next(g.successors(n))
                    if (
                        isinstance(s, Filter)
                        and isinstance(p, (Variable, Reference))
                        and s in a2uns[interface]
                    ):
                        auxs.append(p)
            a2uns[interface].update(auxs)

        # remove dep graphs with only one node
        # e.g., `ds://a` in "y = GET file FROM ds://a WHERE x = v.x"
        # when v.x not in cache
        dep_nodes = [ns for ns in a2uns.values() if len(ns) > 1]
        # need to search in `self` due to the patch for get_trunk_n_branches()
        dep_graphs = [
            IRGraphEvaluable(self.subgraph(ns)).deepcopy() for ns in dep_nodes
        ]

        return dep_graphs

    def find_simple_query_subgraphs(
        self, cache: MutableMapping[UUID, Any]
    ) -> Iterable[IRGraphSimpleQuery]:
        """Find dependency subgraphs those are IRGraphSimpleQuery

        Some interfaces, e.g., stix-shifter, build stateless query and do not
        support JOIN or sub query/SELECT, so they can only evaluate a simple
        SQL query around each source node. Use this method to prepare such tiny
        graph segments for evaluation by the interface. The remaining of the
        graph can be evaluated in cache.

        Parameters:
            cache: any type of node cache, e.g., content, SQL statement

        Returns:
            An iterator of simple-query subgraphs
        """
        for n in self.get_nodes_by_type(SourceInstruction):
            for g in self._find_paths_from_node_to_a_variable(n, cache):
                yield IRGraphSimpleQuery(g)

    def _find_paths_from_node_to_a_variable(
        self, node: Instruction, cache: MutableMapping[UUID, Any]
    ) -> Iterable[IRGraph]:
        """Find paths (linear IRGraph with directly attached cached nodes) from
        the starting node to its closest variables

        If the linear IRGraph has a dependent branch/path longer than a cached
        node, this linear IRGraph cannot be used to build a IRGraphSimpleQuery;
        it needs to generate a subquery for the branch.

        Parameters:
            node: the node to start path search
            cache: any type of node cache, e.g., content, SQL statement

        Returns:
            An iterator of paths
        """
        # check whether the node has other uncached incoming nodes
        # if no, this path can be a IRGraphSimpleQuery
        if len([n for n in self.predecessors(node) if n.id not in cache]) <= 1:
            # pcns: predecessor cached nodes
            pcns = [n for n in self.predecessors(node) if n.id in cache]
            for succ in self.successors(node):
                if isinstance(succ, Variable):
                    yield self.subgraph([succ, node] + pcns)
                else:
                    for succ_graph in self._find_paths_from_node_to_a_variable(
                        succ, cache
                    ):
                        yield self.subgraph(list(succ_graph.nodes()) + [node] + pcns)

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

    def _add_node(self, node: Instruction, deref: bool = True) -> Instruction:
        """Add just the node

        Dependency (if exists) not handled. Variable version and Return
        sequence intentionally not handled here (handled in
        _add_node_with_dependent_node()) for plain adding node opeartion used
        by update().

        Parameters:
            node: the node/instruction to add
            deref: whether to deref is a Reference node

        Returns:
            The node added or found or derefed
        """
        # test `node in self` is important
        # there could be a Reference node already in graph, not to deref
        if node not in self:
            if isinstance(node, IntermediateInstruction):
                if isinstance(node, Reference):
                    if deref:
                        try:
                            v = self.get_variable(node.name)
                        except VariableNotFound:
                            # deref failed, add Reference node directly
                            node = self._add_singleton_instruction(node)
                        else:
                            # deref succeed, no need to add node
                            node = v
                    else:
                        node = self._add_singleton_instruction(node)
                else:
                    raise NotImplementedError(
                        f"unknown IntermediateInstruction: {node}"
                    )
            elif isinstance(node, SourceInstruction):
                node = self._add_singleton_instruction(node)
            else:
                super().add_node(node)
        return node

    def _add_singleton_instruction(self, node: Instruction) -> Instruction:
        """Guard adding a singleton node

        1. Singleton nodes are nodes that only has one copy in graph

        2. A node that has no predecessors is a singleton node

        Parameters:
            node: the node/instruction to add

        Returns:
            The node added or found
        """
        xs = [
            x
            for x in self.nodes()
            if x.has_same_content_as(node) and self.in_degree(x) == 0
        ]
        if xs:
            if len(xs) > 1:
                raise DuplicatedSingletonInstruction(node)
            else:
                node = xs.pop()
        else:
            super().add_node(node)
        return node

    def _add_node_with_dependent_node(
        self, node: Instruction, dependent_node: Instruction
    ) -> Instruction:
        """Add node to graph with a dependent node

        Variable version and Return sequence are handled here.

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
                try:
                    ve = self.get_variable(node.name)
                except VariableNotFound:
                    node.version = 0
                else:
                    node.version = ve.version + 1
            if isinstance(node, Return):
                node.sequence = self.get_max_return_sequence() + 1
            # add_edge will add node first
            self.add_edge(dependent_node, node)
        return node

    def _from_dict(self, graph_in_dict: Mapping[str, Iterable[Mapping]]):
        """Deserialize from a Python dictionary (D3 graph format)

        This method is an implicit constructor from a serialized graph.

        Parameters:
            graph_in_dict: the serialized graph in Python dictionary
        """
        nodes = graph_in_dict["nodes"]
        edges = graph_in_dict["links"]
        for n in nodes:
            self._add_node(instruction_from_dict(n), False)
        for e in edges:
            try:
                u = self.get_node_by_id(e["source"])
                v = self.get_node_by_id(e["target"])
            except InstructionNotFound as err:
                raise InvalidSeralizedGraph()
            else:
                self.add_edge(u, v)


@typechecked
class IRGraphEvaluable(IRGraph):
    """Evaluable IRGraph

    An evaluable IRGraph is an IRGraph that

        1. Only has one interface

        2. No IntermediateInstruction node
    """

    def __init__(self, graph: Optional[IRGraph] = None):
        super().__init__()

        # need to initialize it before `self.update(graph)` below
        self.interface = None

        # update() will call _add_node() internally to set self.interface
        if graph:
            self.update(graph)

        # all source nodes are already cached (no SourceInstruction)
        if not self.interface:
            self.interface = CACHE_INTERFACE_IDENTIFIER

    def _add_node(self, node: Instruction, deref: bool = True) -> Instruction:
        if isinstance(node, IntermediateInstruction):
            raise InevaluableInstruction(node)
        elif isinstance(node, SourceInstruction):
            if self.interface:
                if node.interface != self.interface:
                    raise MultiInterfacesInGraph([self.interface, node.interface])
            else:
                self.interface = node.interface
        return super()._add_node(node, deref)


@typechecked
class IRGraphSimpleQuery(IRGraphEvaluable):
    """Simple Query IRGraph

    A simple query IRGraph is an evaluable IRGraph that

        1. It contains one source node

        2. It can be compiled into a simple (not nested/joined) SQL query
    """

    def __init__(self, graph: Optional[IRGraph] = None):
        if graph and len(graph.get_nodes_by_type(SourceInstruction)) > 1:
            raise MultiSourcesInGraph()
        super().__init__(graph)
