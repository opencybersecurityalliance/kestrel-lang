import pytest
import networkx.utils

from kestrel.ir.instructions import (
    source_from_uri,
    Variable,
    Reference,
    Instruction,
    TransformingInstruction,
)
from kestrel.ir.graph import IRGraph
from kestrel.cache import Cache


def test_add_source():
    g = IRGraph()
    g.add_source("stixshifter://abc")

    s = source_from_uri("stixshifter://abc")
    g.add_source(s)
    assert len(g) == 1

    s = source_from_uri("stixshifter://abcd")
    g.add_source(s)
    assert len(g) == 2


def test_add_same_node():
    g = IRGraph()
    n = Instruction()
    s = g._add_single_node(n)
    s = g._add_single_node(n)
    assert len(g) == 1


def test_add_variable():
    g = IRGraph()
    s = g.add_source("stixshifter://abc")
    v1 = g.add_variable("asdf", s)
    assert len(g) == 2
    assert len(g.edges()) == 1

    v2 = g.add_variable("asdf", s)
    assert len(g) == 3
    assert len(g.edges()) == 2

    v = Variable("asdf")
    v3 = g.add_variable(v, s)
    assert v == v3
    v4 = g.add_variable(v, s)
    assert v3 == v4

    assert v1.freshness == 0
    assert v2.freshness == 1
    assert v3.freshness == 2
    assert len(g) == 4
    assert len(g.edges()) == 3


def test_get_variables():
    g = IRGraph()
    s = g.add_source("stixshifter://abc")
    v1 = g.add_variable("asdf", s)
    v2 = g.add_variable("asdf", s)
    v3 = g.add_variable("asdf", s)
    vs = g.get_variables()
    assert len(vs) == 1
    assert vs[0].name == "asdf"


def test_add_reference():
    g = IRGraph()
    s = g.add_node(source_from_uri("ss://ee"))
    g.add_node(Variable("asdf"), s)
    g.add_node(Reference("asdf"))
    g.add_node(Reference("qwer"))
    g.add_node(Reference("qwer"))
    g.add_node(Variable("qwer"), s)
    g.add_node(Reference("qwer"))
    assert len(g) == 4
    assert len(g.edges()) == 2


def test_update_graph():
    g = IRGraph()
    s = g.add_source("stixshifter://abc")
    v1 = g.add_variable("asdf", s)
    v2 = g.add_variable("asdf", s)
    v3 = g.add_variable("asdf", s)

    g2 = IRGraph()
    s2 = g2.add_source("stixshifter://abc")
    v4 = g2.add_variable("asdf", g2.add_node(Reference("asdf")))
    v5 = g2.add_variable("asdf", g2.add_node(TransformingInstruction(), s2))

    assert v1.freshness == 0
    assert v2.freshness == 1
    assert v3.freshness == 2
    assert v4.freshness == 0
    assert v5.freshness == 1
    assert len(g) == 4
    assert len(g2) == 5

    g.update(g2)
    assert v1.freshness == 0
    assert v2.freshness == 1
    assert v3.freshness == 2
    assert v4.freshness == 3
    assert v5.freshness == 4
    assert len(g) == 7
    assert (v3, v4) in g.edges()
    assert g.in_degree(v4) == 1
    assert g.out_degree(v4) == 0


def test_serialization_deserialization():
    g1 = IRGraph()
    s = g1.add_node(source_from_uri("ss://ee"))
    r = g1.add_node(Reference("asdf"))
    v = g1.add_node(Variable("asdf"), s)
    j = g1.to_json()
    g2 = IRGraph(j)
    assert s in g2.nodes()
    assert v in g2.nodes()
    assert len(g2) == 3
    assert g2.edges() == {(s,v)}


def test_find_cached_dependent_subgraph_of_node():
    g = IRGraph()

    a1 = g.add_node(source_from_uri("ss://ee"))
    a2 = g.add_node(Variable("asdf"), a1)
    a3 = g.add_node(Instruction())
    g.add_edge(a2, a3)
    a4 = g.add_node(Variable("qwer"), a3)

    b1 = g.add_node(source_from_uri("ss://eee"))
    b2 = g.add_node(Variable("asdfe"), b1)
    b3 = g.add_node(Instruction())
    g.add_edge(b2, b3)
    b4 = g.add_node(Variable("qwere"), b3)

    c1 = g.add_node(Instruction())
    g.add_edge(a4, c1)
    g.add_edge(b4, c1)
    c2 = g.add_node(Variable("zxcv"), c1)

    g2 = g.find_cached_dependent_subgraph_of_node(c2, Cache())
    assert networkx.utils.graphs_equal(g, g2)

    g3 = g.find_cached_dependent_subgraph_of_node(c2, Cache({a2.id: object(), b2.id: object()}))
    g.remove_node(a1)
    g.remove_node(b1)
    assert networkx.utils.graphs_equal(g, g3)
