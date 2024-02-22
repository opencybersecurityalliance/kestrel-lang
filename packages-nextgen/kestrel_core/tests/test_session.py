import pytest
from kestrel import Session
from pandas import DataFrame


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
