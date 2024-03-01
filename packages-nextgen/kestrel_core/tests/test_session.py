import pytest
from kestrel import Session
from pandas import DataFrame

from kestrel.display import GraphExplanation
from kestrel.ir.instructions import Construct


def test_execute_in_cache():
    hf = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name != "cmd.exe"
DISP browsers
cmd = proclist WHERE name = "cmd.exe"
DISP cmd ATTR pid
"""
    b1 = DataFrame([ {"name": "explorer.exe", "pid": 99}
                   , {"name": "firefox.exe", "pid": 201}
                   , {"name": "chrome.exe", "pid": 205}
                   ])
    b2 = DataFrame([ {"pid": 123} ])
    with Session() as session:
        res = session.execute_to_generate(hf)
        assert b1.equals(next(res))
        assert b2.equals(next(res))
        with pytest.raises(StopIteration):
            next(res)

def test_explain_in_cache():
    hf = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
browsers = proclist WHERE name != "cmd.exe"
chrome = browsers WHERE pid = 205
EXPLAIN chrome
"""
    with Session() as session:
        ress = session.execute_to_generate(hf)
        res = next(ress)
        assert isinstance(res, GraphExplanation)
        assert len(res.graphlets) == 1
        ge = res.graphlets[0]
        assert ge.graph == session.irgraph.to_dict()
        construct = session.irgraph.get_nodes_by_type(Construct)[0]
        assert ge.query.language == "SQL"
        stmt = ge.query.statement.replace('"', '')
        assert stmt == f'SELECT * \nFROM (SELECT * \nFROM (SELECT * \nFROM (SELECT * \nFROM {construct.id.hex}) AS anon_3 \nWHERE name != \'cmd.exe\') AS anon_2 \nWHERE pid = 205) AS anon_1'
        with pytest.raises(StopIteration):
            next(ress)
