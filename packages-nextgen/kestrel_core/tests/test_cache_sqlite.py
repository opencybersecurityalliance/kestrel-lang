from uuid import uuid4
from pandas import DataFrame

from kestrel.cache.sqlite import SqliteCache
from kestrel.ir.graph import IRGraphEvaluable
from kestrel.frontend.parser import parse_kestrel


def test_sqlite_cache_set_get_del():
    c = SqliteCache()
    idx = uuid4()
    df = DataFrame({'foo': [1, 2, 3]})
    c[idx] = df
    assert df.equals(c[idx])
    del c[idx]
    assert idx not in c


def test_sqlite_cache_constructor():
    ids = [uuid4() for i in range(5)]
    df = DataFrame({'foo': [1, 2, 3]})
    c = SqliteCache({x:df for x in ids})
    for u in ids:
        assert df.equals(c[u])
    for u in ids:
        del c[u]
        assert u not in c


def test_eval_new_disp():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
DISP proclist ATTR name
"""
    graph = IRGraphEvaluable(parse_kestrel(stmt))
    c = SqliteCache()
    mapping = c.evaluate_graph(graph)

    # check the return is correct
    rets = graph.get_returns()
    assert len(rets) == 1
    df = mapping[rets[0].id]
    assert df.to_dict("records") == [ {"name": "cmd.exe"}
                                    , {"name": "explorer.exe"}
                                    , {"name": "firefox.exe"}
                                    , {"name": "chrome.exe"}
                                    ]
    # check whether `proclist` is cached
    proclist = graph.get_variable("proclist")
    assert c[proclist.id].to_dict("records") == [ {"name": "cmd.exe", "pid": 123}
                                                , {"name": "explorer.exe", "pid": 99}
                                                , {"name": "firefox.exe", "pid": 201}
                                                , {"name": "chrome.exe", "pid": 205}
                                                ]


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
    c = SqliteCache()
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


def test_eval_two_returns():
    stmt = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name != "cmd.exe"
DISP browsers
DISP browsers ATTR pid
"""
    graph = parse_kestrel(stmt)
    c = SqliteCache()
    rets = graph.get_returns()

    # first DISP
    gs = graph.find_dependent_subgraphs_of_node(rets[0], c)
    assert len(gs) == 1
    mapping = c.evaluate_graph(gs[0])
    df1 = DataFrame([ {"name": "explorer.exe", "pid": 99}
                    , {"name": "firefox.exe", "pid": 201}
                    , {"name": "chrome.exe", "pid": 205}
                    ])
    assert len(mapping) == 1
    assert df1.equals(mapping[rets[0].id])

    # second DISP
    gs = graph.find_dependent_subgraphs_of_node(rets[1], c)
    assert len(gs) == 1
    mapping = c.evaluate_graph(gs[0])
    df2 = DataFrame([ {"pid": 99}
                    , {"pid": 201}
                    , {"pid": 205}
                    ])
    assert len(mapping) == 1
    assert df2.equals(mapping[rets[1].id])
