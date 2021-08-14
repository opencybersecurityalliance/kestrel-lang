import pytest
import json

from kestrel.exceptions import VariableNotExist
from kestrel.session import Session


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
