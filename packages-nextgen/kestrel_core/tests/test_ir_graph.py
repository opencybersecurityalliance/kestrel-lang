import pytest
import networkx.utils

from kestrel.ir.instructions import (
    source_from_uri,
    Variable,
    Instruction,
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
    assert v1.deceased
    assert v2.deceased
    assert not v3.deceased
    assert len(g) == 4
    assert len(g.edges()) == 3


def test_add_node():
    g = IRGraph()
    s = g.add_node(source_from_uri("ss://ee"))
    g.add_node(Variable("asdf"), s)
    assert len(g) == 2
    assert len(g.edges()) == 1


def test_serialization_deserialization():
    g1 = IRGraph()
    s = g1.add_node(source_from_uri("ss://ee"))
    v = g1.add_node(Variable("asdf"), s)
    j = g1.to_json()
    g2 = IRGraph(j)
    assert s in g2.nodes()
    assert v in g2.nodes()
    assert len(g2) == 2
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
