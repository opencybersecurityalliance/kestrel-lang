import pytest
from pandas import DataFrame

from kestrel.interface.codegen.dataframe import (
    evaluate_source_instruction,
    evaluate_transforming_instruction,
)

from kestrel.ir.instructions import (
    Construct,
    Variable,
    Filter,
    Limit,
    ProjectAttrs,
)

from kestrel.frontend.parser import parse_kestrel


def test_evaluate_Construct():
    data = [ {"name": "cmd.exe", "pid": 123}
           , {"name": "explorer.exe", "pid": 99}
           , {"name": "firefox.exe", "pid": 201}
           , {"name": "chrome.exe", "pid": 205}
           ]
    ins = Construct(data)
    df = evaluate_source_instruction(ins)
    assert df.equals(DataFrame(data))


def test_non_exist_eval():
    with pytest.raises(NotImplementedError):
        evaluate_transforming_instruction(Variable("asdf"), DataFrame())


def test_evaluate_Limit():
    data = [ {"name": "cmd.exe", "pid": 123}
           , {"name": "explorer.exe", "pid": 99}
           , {"name": "firefox.exe", "pid": 201}
           , {"name": "chrome.exe", "pid": 205}
           ]
    df = DataFrame(data)
    dfx = evaluate_transforming_instruction(Limit(2), df)
    assert dfx.equals(df.head(2))


def test_evaluate_ProjectAttrs():
    data = [ {"name": "cmd.exe", "pid": 123}
           , {"name": "explorer.exe", "pid": 99}
           , {"name": "firefox.exe", "pid": 201}
           , {"name": "chrome.exe", "pid": 205}
           ]
    df = DataFrame(data)
    dfx = evaluate_transforming_instruction(ProjectAttrs(["name"]), df)
    assert dfx.equals(df[["name"]])


def test_evaluate_Construct_Filter_ProjectAttrs():
    stmt = r"""
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name = 'firefox.exe' OR name = 'chrome.exe'
DISP browsers ATTR name, pid
p2 = proclist WHERE pid > 100
p3 = proclist WHERE name LIKE "c%.exe"
p4 = proclist WHERE name MATCHES r"^c\w{2}\.exe"
"""
    graph = parse_kestrel(stmt)
    c = graph.get_nodes_by_type(Construct)[0]
    df0 = evaluate_source_instruction(c)
    assert df0.to_dict("records") == [ {"name": "cmd.exe", "pid": 123}
                                     , {"name": "explorer.exe", "pid": 99}
                                     , {"name": "firefox.exe", "pid": 201}
                                     , {"name": "chrome.exe", "pid": 205}
                                     ]

    browsers = graph.get_variable("browsers")
    ft = next(graph.predecessors(browsers))
    dfx = evaluate_transforming_instruction(ft, df0)
    assert dfx.to_dict("records") == [ {"name": "firefox.exe", "pid": 201}
                                     , {"name": "chrome.exe", "pid": 205}
                                     ]
    proj = next(graph.successors(browsers))
    dfy = evaluate_transforming_instruction(proj, dfx)
    assert dfx.to_dict("records") == [ {"name": "firefox.exe", "pid": 201}
                                     , {"name": "chrome.exe", "pid": 205}
                                     ]

    ft = next(graph.predecessors(graph.get_variable("p2")))
    dfx = evaluate_transforming_instruction(ft, df0)
    assert dfx.to_dict("records") == [ {"name": "cmd.exe", "pid": 123}
                                     , {"name": "firefox.exe", "pid": 201}
                                     , {"name": "chrome.exe", "pid": 205}
                                     ]

    ft = next(graph.predecessors(graph.get_variable("p3")))
    dfx = evaluate_transforming_instruction(ft, df0)
    assert dfx.to_dict("records") == [ {"name": "cmd.exe", "pid": 123}
                                     , {"name": "chrome.exe", "pid": 205}
                                     ]

    ft = next(graph.predecessors(graph.get_variable("p4")))
    dfx = evaluate_transforming_instruction(ft, df0)
    assert dfx.to_dict("records") == [ {"name": "cmd.exe", "pid": 123} ]
