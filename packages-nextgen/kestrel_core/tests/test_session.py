import pytest
import os
from kestrel import Session
from pandas import DataFrame
from uuid import uuid4

from kestrel.display import GraphExplanation
from kestrel.ir.instructions import Construct
from kestrel.config.internal import CACHE_INTERFACE_IDENTIFIER
from kestrel.frontend.parser import parse_kestrel
from kestrel.cache import SqliteCache


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


def test_double_deref_in_cache():
    # When the Filter node is dereferred twice
    # The node should be deepcopied each time to avoid issue
    hf = """
proclist = NEW process [ {"name": "cmd.exe", "pid": 123}
                       , {"name": "explorer.exe", "pid": 99}
                       , {"name": "firefox.exe", "pid": 201}
                       , {"name": "chrome.exe", "pid": 205}
                       ]
px = proclist WHERE name != "cmd.exe" AND pid = 205
chrome = proclist WHERE pid IN px.pid
DISP chrome
DISP chrome
"""
    df = DataFrame([ {"name": "chrome.exe", "pid": 205} ])
    with Session() as session:
        res = session.execute_to_generate(hf)
        assert df.equals(next(res))
        assert df.equals(next(res))
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
        assert stmt == f'SELECT * \nFROM (SELECT * \nFROM (SELECT * \nFROM (SELECT * \nFROM {construct.id.hex}v) AS proclist \nWHERE name != \'cmd.exe\') AS browsers \nWHERE pid = 205) AS chrome'
        with pytest.raises(StopIteration):
            next(ress)


def test_multi_interface_explain():

    class DataLake(SqliteCache):
        @staticmethod
        def schemes():
            return ["datalake"]

    class Gateway(SqliteCache):
        @staticmethod
        def schemes():
            return ["gateway"]

    extra_db = []
    with Session() as session:
        stmt1 = """
procs = NEW process [ {"name": "cmd.exe", "pid": 123}
                    , {"name": "explorer.exe", "pid": 99}
                    , {"name": "firefox.exe", "pid": 201}
                    , {"name": "chrome.exe", "pid": 205}
                    ]
DISP procs
"""
        session.execute(stmt1)
        session.interface_manager[CACHE_INTERFACE_IDENTIFIER].__class__ = DataLake
        session.irgraph.get_nodes_by_type_and_attributes(Construct, {"interface": CACHE_INTERFACE_IDENTIFIER})[0].interface = "datalake"

        new_cache = SqliteCache(session_id = uuid4())
        extra_db.append(new_cache.db_path)
        session.interface_manager.interfaces.append(new_cache)
        stmt2 = """
nt = NEW network [ {"pid": 123, "source": "192.168.1.1", "destination": "1.1.1.1"}
                 , {"pid": 205, "source": "192.168.1.1", "destination": "1.1.1.2"}
                 ]
DISP nt
"""
        session.execute(stmt2)
        session.interface_manager[CACHE_INTERFACE_IDENTIFIER].__class__ = Gateway
        session.irgraph.get_nodes_by_type_and_attributes(Construct, {"interface": CACHE_INTERFACE_IDENTIFIER})[0].interface = "gateway"

        new_cache = SqliteCache(session_id = uuid4())
        extra_db.append(new_cache.db_path)
        session.interface_manager.interfaces.append(new_cache)
        stmt3 = """
domain = NEW domain [ {"ip": "1.1.1.1", "domain": "cloudflare.com"}
                    , {"ip": "1.1.1.2", "domain": "xyz.cloudflare.com"}
                    ]
DISP domain
"""
        session.execute(stmt3)

        stmt = """
p2 = procs WHERE name IN ("firefox.exe", "chrome.exe")
ntx = nt WHERE pid IN p2.pid
d2 = domain WHERE ip IN ntx.destination
EXPLAIN d2
DISP d2
"""
        ress = session.execute_to_generate(stmt)
        disp = next(ress)
        df_res = next(ress)

        with pytest.raises(StopIteration):
            next(ress)

        assert isinstance(disp, GraphExplanation)
        assert len(disp.graphlets) == 4

        assert len(disp.graphlets[0].graph["nodes"]) == 5
        query = disp.graphlets[0].query.statement.replace('"', '')
        procs = session.irgraph.get_variable("procs")
        c1 = next(session.irgraph.predecessors(procs))
        assert query == f"SELECT pid \nFROM (SELECT * \nFROM (SELECT * \nFROM {c1.id.hex}) AS procs \nWHERE name IN ('firefox.exe', 'chrome.exe')) AS p2"

        assert len(disp.graphlets[1].graph["nodes"]) == 2
        query = disp.graphlets[1].query.statement.replace('"', '')
        nt = session.irgraph.get_variable("nt")
        c2 = next(session.irgraph.predecessors(nt))
        assert query == f"SELECT * \nFROM (SELECT * \nFROM {c2.id.hex}) AS nt"

        # the current session.execute_to_generate() logic does not store
        # in cache if evaluated by cache; the behavior may change in the future
        assert len(disp.graphlets[2].graph["nodes"]) == 2
        query = disp.graphlets[2].query.statement.replace('"', '')
        domain = session.irgraph.get_variable("domain")
        c3 = next(session.irgraph.predecessors(domain))
        assert query == f"SELECT * \nFROM (SELECT * \nFROM {c3.id.hex}) AS domain"

        assert len(disp.graphlets[3].graph["nodes"]) == 12
        print(disp.graphlets[3].graph["nodes"])
        query = disp.graphlets[3].query.statement.replace('"', '')
        p2 = session.irgraph.get_variable("p2")
        p2pa = next(session.irgraph.successors(p2))
        assert query == f"SELECT * \nFROM (SELECT * \nFROM (SELECT * \nFROM {c3.id.hex}) AS domain \nWHERE ip IN (SELECT destination \nFROM (SELECT * \nFROM {nt.id.hex}v \nWHERE pid IN (SELECT * \nFROM {p2pa.id.hex}v)) AS ntx)) AS d2"

        df_ref = DataFrame([{"ip": "1.1.1.2", "domain": "xyz.cloudflare.com"}])
        assert df_ref.equals(df_res)

    for db_file in extra_db:
        os.remove(db_file)
