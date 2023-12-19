import pytest
import networkx.utils
from collections import Counter
from pandas import DataFrame

from kestrel.ir.instructions import (
    Variable,
    DataSource,
    Reference,
    Return,
    Filter,
    Construct,
    ProjectAttrs,
    ProjectEntity,
    Instruction,
    TransformingInstruction,
    CACHE_INTERFACE_IDENTIFIER,
)
from kestrel.ir.filter import StrComparison, StrCompOp
from kestrel.ir.graph import IRGraph
from kestrel.frontend.parser import parse_kestrel
from kestrel.cache import InMemoryCache


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


def test_find_dependent_subgraphs_of_node_just_cache():
    huntflow = """
p1 = NEW process [ {"name": "cmd.exe", "pid": 123}
                 , {"name": "explorer.exe", "pid": 99}
                 , {"name": "firefox.exe", "pid": 201}
                 , {"name": "chrome.exe", "pid": 205}
                 ]

browsers = p1 WHERE name = 'firefox.exe' OR name = 'chrome.exe'

DISP browsers ATTR name
"""
    graph = parse_kestrel(huntflow)
    c = InMemoryCache()
    ret = graph.get_returns()[0]
    gs = graph.find_dependent_subgraphs_of_node(ret, c)
    assert len(gs) == 1
    assert len(gs[0]) == 6
    assert Counter(map(type, gs[0].nodes())) == Counter([Filter, Variable, Variable, Construct, ProjectAttrs, Return])
    assert gs[0].interface == CACHE_INTERFACE_IDENTIFIER


def test_find_dependent_subgraphs_of_node():
    huntflow = """
p1 = NEW process [ {"name": "cmd.exe", "pid": 123}
                 , {"name": "explorer.exe", "pid": 99}
                 , {"name": "firefox.exe", "pid": 201}
                 , {"name": "chrome.exe", "pid": 205}
                 ]

browsers = p1 WHERE name = 'firefox.exe' OR name = 'chrome.exe'

p2 = GET process FROM elastic://edr1
     WHERE name = "cmd.exe"
     LAST 5 DAYS

p21 = p2 WHERE parent.name = "winword.exe"

p3 = GET process FROM stixshifter://edr2
     WHERE parent_ref.name = "powershell.exe"
     LAST 24 HOURS

p31 = p3 WHERE parent.name = "excel.exe"

# not supported in parser yet, manually add nodes
#p4 = p21 WHERE pid = p1.pid
#p5 = p31 WHERE pid = p4.pid
"""
    graph = parse_kestrel(huntflow)

    proj1 = ProjectAttrs(["pid"])
    graph.add_node(proj1, graph.get_variable("p1"))
    filt1 = Filter(StrComparison("pid", StrCompOp.EQ, "ref"))
    graph.add_node(filt1, graph.get_variable("p21"))
    graph.add_edge(proj1, filt1)
    p4 = Variable("p4")
    graph.add_node(p4, filt1)

    proj2 = ProjectAttrs(["pid"])
    graph.add_node(proj2, p4)
    filt2 = Filter(StrComparison("pid", StrCompOp.EQ, "ref"))
    graph.add_node(filt2, graph.get_variable("p31"))
    graph.add_edge(proj2, filt2)
    p5 = Variable("p5")
    graph.add_node(p5, filt2)

    stmt = "DISP p5 ATTR pid, name, cmd_line"
    graph.update(parse_kestrel(stmt))

    ret = graph.get_returns()[0]

    c = InMemoryCache()
    gs = graph.find_dependent_subgraphs_of_node(ret, c)
    assert len(gs) == 3

    assert len(gs[0]) == 3
    assert set(map(type, gs[0].nodes())) == {Variable, ProjectAttrs, Construct}
    assert proj1 == gs[0].get_nodes_by_type(ProjectAttrs)[0]

    assert len(gs[1]) == 6
    assert Counter(map(type, gs[1].nodes())) == Counter([Filter, Filter, Variable, Variable, ProjectEntity, DataSource])

    assert len(gs[2]) == 6
    assert Counter(map(type, gs[2].nodes())) == Counter([Filter, Filter, Variable, Variable, ProjectEntity, DataSource])

    c.evaluate_graph(gs[0])
    assert proj1.id in c
    assert graph.get_variable("p1").id in c
    assert len(c) == 2
    gs = graph.find_dependent_subgraphs_of_node(ret, c)
    assert len(gs) == 2

    assert len(gs[0]) == 10
    assert proj1 in gs[0]
    assert proj2 in gs[0]
    assert graph.get_variable("p2") in gs[0]
    assert graph.get_variable("p21") in gs[0]
    assert p4 in gs[0]

    assert len(gs[1]) == 6
    assert Counter(map(type, gs[1].nodes())) == Counter([Filter, Filter, Variable, Variable, ProjectEntity, DataSource])

    c[proj2.id] = DataFrame()
    gs = graph.find_dependent_subgraphs_of_node(ret, c)
    assert len(gs) == 1

    assert len(gs[0]) == 11
    assert proj2.id in c
    assert proj2 in gs[0]
    assert graph.get_variable("p31") in gs[0]
    assert p5 in gs[0]
    assert ret in gs[0]
