import pytest

from kestrel.session import Session


def test_describe():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": 123}
             , {"type": "process", "name": "explorer.exe", "pid": 99}
             , {"type": "process", "name": "explorer.exe", "pid": 200}
             ]
"""
        s.execute(stmt)
        out = s.execute("DESCRIBE newvar.name")
        stats = out[0].to_dict()['data']
        assert stats['count'] == 3
        assert stats['unique'] == 2
        assert stats['top'] == "explorer.exe"
        assert stats['freq'] == 2

        out = s.execute("DESCRIBE newvar.pid")
        stats = out[0].to_dict()['data']
        assert stats['count'] == 3
        assert stats['mean'] == (123 + 99 + 200)/3
        assert stats['min'] == 99
        assert stats['max'] == 200
