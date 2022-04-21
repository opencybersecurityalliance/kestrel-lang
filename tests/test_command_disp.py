import os
import pandas as pd
import pytest

from kestrel.exceptions import VariableNotExist
from kestrel.session import Session


@pytest.fixture
def proc_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "doctored-1k.json")


def test_disp():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""
        d = s.execute(stmt)
        out = s.execute("DISP newvar")
        data = out[0].to_dict()


def test_disp_no_vars():
    with Session() as s:
        with pytest.raises(VariableNotExist):
            s.execute("DISP newvar")


def test_disp_grouped_procs():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             , {"type": "process", "name": "explorer.exe", "pid": "98"}
             ]
"""
        s.execute(stmt)
        s.execute("grpvar = group newvar by name")
        out = s.execute("DISP grpvar")
        data = out[0].to_dict()["data"]
        assert len(data) == 2


def test_disp_grouped_conns():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "network-traffic", "src_ref.value": "1.2.3.4", "dst_ref.value": "4.3.2.1"}
             , {"type": "network-traffic", "src_ref.value": "2.2.3.4", "dst_ref.value": "4.3.2.1"}
             , {"type": "network-traffic", "src_ref.value": "1.2.3.4", "dst_ref.value": "5.3.2.1"}
             ]
"""
        s.execute(stmt)
        s.execute("grpvar = group newvar by dst_ref.value")
        out = s.execute("DISP grpvar")
        data = out[0].to_dict()["data"]
        assert len(data) == 2


def test_disp_mixed_v4_v6(proc_bundle_file):
    with Session() as s:
        stmt = f"""
conns = GET network-traffic
        FROM file://{proc_bundle_file}
        WHERE [network-traffic:dst_port > 0]
"""
        s.execute(stmt)

        out = s.execute("DISP conns ATTR src_ref.value, src_port")
        data = out[0].to_dict()["data"]
        df = pd.DataFrame.from_records(data)
        assert df.columns.tolist() == ["src_ref.value", "src_port"]

        out = s.execute("DISP TIMESTAMPED(conns) ATTR src_ref.value, src_port")
        data = out[0].to_dict()["data"]
        df = pd.DataFrame.from_records(data)
        assert df.columns.tolist() == ["first_observed", "src_ref.value", "src_port"]
