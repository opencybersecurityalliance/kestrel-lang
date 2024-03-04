import pytest
from pandas import DataFrame
from uuid import uuid4

from kestrel.cache import InMemoryCache
from kestrel.cache.inmemory import InMemoryCacheVirtual
from kestrel.ir.graph import IRGraph, IRGraphEvaluable
from kestrel.frontend.parser import parse_kestrel


def test_inmemory_cache_set_get_del():
    c = InMemoryCache()
    idx = uuid4()
    df = DataFrame([1, 2, 3])
    c[idx] = df
    assert df.equals(c[idx])
    del c[idx]
    assert idx not in c


def test_inmemory_cache_constructor():
    ids = [uuid4() for i in range(5)]
    df = DataFrame([1, 2, 3])
    c = InMemoryCache({x:df for x in ids})
    for u in ids:
        assert df.equals(c[u])
    for u in ids:
        del c[u]
        assert u not in c


def test_eval_new_filter_disp():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name = 'firefox.exe' OR name = 'chrome.exe'
DISP browsers ATTR name, pid
"""
    graph = IRGraphEvaluable(parse_kestrel(stmt))
    c = InMemoryCache()
    mapping = c.evaluate_graph(graph)

    # check the return is correct
    rets = graph.get_returns()
    assert len(rets) == 1
    df = mapping[rets[0].id]
    assert df.to_dict("records") == [ {"name": "firefox.exe", "pid": 201}
                                    , {"name": "chrome.exe", "pid": 205}
                                    ]
    # check whether `proclist` is cached
    proclist = graph.get_variable("proclist")
    assert c[proclist.id].to_dict("records") == [ {"name": "cmd.exe", "pid": 123}
                                                , {"name": "explorer.exe", "pid": 99}
                                                , {"name": "firefox.exe", "pid": 201}
                                                , {"name": "chrome.exe", "pid": 205}
                                                ]
    # check whether `browsers` is cached
    browsers = graph.get_variable("browsers")
    assert c[browsers.id].to_dict("records") == [ {"name": "firefox.exe", "pid": 201}
                                                , {"name": "chrome.exe", "pid": 205}
                                                ]


def test_eval_filter_with_ref():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name = 'firefox.exe' OR name = 'chrome.exe'
specials = proclist WHERE pid IN [123, 201]
p2 = proclist WHERE pid = browsers.pid and name = specials.name
DISP p2 ATTR name, pid
"""
    graph = IRGraphEvaluable(parse_kestrel(stmt))
    c = InMemoryCache()
    mapping = c.evaluate_graph(graph)

    # check the return is correct
    rets = graph.get_returns()
    assert len(rets) == 1
    df = mapping[rets[0].id]
    assert df.to_dict("records") == [ {"name": "firefox.exe", "pid": 201} ]

def test_get_virtual_copy():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name = 'firefox.exe' OR name = 'chrome.exe'
"""
    graph = IRGraphEvaluable(parse_kestrel(stmt))
    c = InMemoryCache()
    mapping = c.evaluate_graph(graph)
    v = c.get_virtual_copy()
    new_entry = uuid4()
    v[new_entry] = True

    # v[new_entry] calls the right method
    assert isinstance(v, InMemoryCacheVirtual)
    assert v[new_entry].startswith("virtual")

    # v[new_entry] does not hit v.cache
    assert len(c.cache) == 2
    assert len(v.cache) == 2 

    # the two cache_catalog are different
    assert new_entry not in c
    assert new_entry in v
    del v[new_entry]
    assert new_entry not in v
    for u in c:
        del v[u]
    assert len(v) == 0
    assert len(c) == 2
