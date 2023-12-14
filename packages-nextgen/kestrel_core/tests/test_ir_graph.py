import pytest
import networkx.utils
from pandas import DataFrame

from kestrel.ir.instructions import (
    Variable,
    DataSource,
    Reference,
    Return,
    Instruction,
    TransformingInstruction,
)
from kestrel.ir.graph import IRGraph
from kestrel.cache.inmemory import InMemoryCache


def test_add_get_datasource():
    g = IRGraph()
    g.add_datasource("stixshifter://abc")

    s = g.add_datasource(DataSource("stixshifter://abc"))
    assert len(g) == 1

    s2 = DataSource("stixshifter://abcd")
    g.add_datasource(s2)
    assert len(g) == 2

    assert set(g.get_datasources()) == {s, s2}
    g.get_datasource("stixshifter", "abc") == s


def test_add_same_node():
    g = IRGraph()
    n = Instruction()
    s = g.add_node(n)
    s = g.add_node(n)
    assert len(g) == 1


def test_get_node_by_id():
    g = IRGraph()
    n = Instruction()
    s = g.add_node(n)
    assert g.get_node_by_id(n.id) == n


def test_get_nodes_by_type_and_attributes():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
    v1 = g.add_variable("asdf", s)
    v2 = g.add_variable("qwer", s)
    v3 = g.add_variable("123", s)
    ns = g.get_nodes_by_type_and_attributes(Variable, {"name": "asdf"})
    assert ns == [v1]


def test_get_returns():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
    g.add_node(Return(), s)
    g.add_node(Return(), s)
    g.add_node(Return(), s)
    assert len(g.get_returns()) == 3
    assert len(g.get_sink_nodes()) == 3


def test_add_variable():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
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

    assert v1.version == 0
    assert v2.version == 1
    assert v3.version == 2
    assert len(g) == 4
    assert len(g.edges()) == 3


def test_get_variables():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
    v1 = g.add_variable("asdf", s)
    v2 = g.add_variable("asdf", s)
    v3 = g.add_variable("asdf", s)
    vs = g.get_variables()
    assert len(vs) == 1
    assert vs[0].name == "asdf"


def test_add_get_reference():
    g = IRGraph()
    s = g.add_node(DataSource("ss://ee"))
    g.add_node(Variable("asdf"), s)
    g.add_node(Reference("asdf"))
    q1 = g.add_node(Reference("qwer"))
    q2 = g.add_node(Reference("qwer"))
    g.add_node(Variable("qwer"), s)
    g.add_node(Reference("qwer"))
    assert len(g) == 4
    assert len(g.edges()) == 2

    assert q1 == q2
    assert g.get_reference("qwer") == q1
    refs = g.get_references()
    assert refs == [q1]


def test_copy_graph():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
    g2 = g.copy()
    assert s in g2
    for n in g2.nodes():
        n.datasource = "eee"
    assert s in g
    assert s.datasource == "eee"


def test_deepcopy_graph():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
    g2 = g.deepcopy()
    assert len(g2.nodes()) == 1
    s2 = list(g2.nodes())[0]
    s2.datasource = "eee"
    assert s.datasource == "abc"
    assert s2.datasource == "eee"


def test_update_graph():
    g = IRGraph()
    s = g.add_datasource("stixshifter://abc")
    v1 = g.add_variable("asdf", s)
    v2 = g.add_variable("asdf", s)
    v3 = g.add_variable("asdf", s)

    g2 = IRGraph()
    s2 = g2.add_datasource("stixshifter://abc")
    v4 = g2.add_variable("asdf", g2.add_node(Reference("asdf")))
    v5 = g2.add_variable("asdf", g2.add_node(TransformingInstruction(), s2))

    assert v1.version == 0
    assert v2.version == 1
    assert v3.version == 2
    assert v4.version == 0
    assert v5.version == 1
    assert len(g) == 4
    assert len(g2) == 5

    g.update(g2)
    assert v1.version == 0
    assert v2.version == 1
    assert v3.version == 2
    assert v4.version == 3
    assert v5.version == 4
    assert len(g) == 7
    assert s2 not in g
    assert not g.get_references()
    assert (v3, v4) in g.edges()
    assert g.in_degree(v4) == 1
    assert g.out_degree(v4) == 0


def test_serialization_deserialization():
    g1 = IRGraph()
    s = g1.add_node(DataSource("ss://ee"))
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

    a1 = g.add_node(DataSource("ss://ee"))
    a2 = g.add_node(Variable("asdf"), a1)
    a3 = g.add_node(Instruction())
    g.add_edge(a2, a3)
    a4 = g.add_node(Variable("qwer"), a3)

    b1 = g.add_node(DataSource("ss://eee"))
    b2 = g.add_node(Variable("asdfe"), b1)
    b3 = g.add_node(Instruction())
    g.add_edge(b2, b3)
    b4 = g.add_node(Variable("qwere"), b3)

    c1 = g.add_node(Instruction())
    g.add_edge(a4, c1)
    g.add_edge(b4, c1)
    c2 = g.add_node(Variable("zxcv"), c1)

    g2 = g.find_cached_dependent_subgraph_of_node(c2, InMemoryCache())
    assert networkx.utils.graphs_equal(g, g2)

    g3 = g.find_cached_dependent_subgraph_of_node(c2, InMemoryCache({a2.id: DataFrame(), b2.id: DataFrame()}))
    g.remove_node(a1)
    g.remove_node(b1)
    assert networkx.utils.graphs_equal(g, g3)
