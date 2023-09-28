import pytest

from kestrel.session import Session
from kestrel.exceptions import MissingEntityType


def test_new_with_full_json():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] in ["cmd.exe", "explorer.exe"]
        if v[0]["name"] == "cmd.exe":
            assert v[0]["pid"] == "123"
        else:
            assert v[0]["pid"] == "99"


def test_new_with_json_no_type():
    with Session() as s:
        stmt = """
newvar = NEW process [ {"name": "cmd.exe", "pid": "123"}
                     , {"name": "explorer.exe", "pid": "99"}
                     ]
"""
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] in ["cmd.exe", "explorer.exe"]
        if v[0]["name"] == "cmd.exe":
            assert v[0]["pid"] == "123"
        else:
            assert v[0]["pid"] == "99"


def test_new_with_json_no_type_to_fail():
    with Session() as s:
        stmt = """
newvar = NEW [ {"name": "cmd.exe", "pid": "123"}
             , {"name": "explorer.exe", "pid": "99"}
             ]
"""
        with pytest.raises(MissingEntityType) as e:
            s.execute(stmt)


def test_new_with_list_of_strings():
    with Session() as s:
        stmt = (
            """newvar = NEW process ["cmd.exe", "explorer.exe", "google-chrome.exe"]"""
        )
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 3
        assert v[0]["type"] == "process"
        assert sorted([i["name"] for i in v]) == [
            "cmd.exe",
            "explorer.exe",
            "google-chrome.exe",
        ]


def test_new_list_of_strings_without_type_to_fail():
    with Session() as s:
        stmt = """newvar = NEW ["cmd.exe", "explorer.exe", "google-chrome.exe"]"""
        with pytest.raises(MissingEntityType) as e:
            s.execute(stmt)


def test_new_with_int_pid():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": 123}
             , {"type": "process", "name": "explorer.exe", "pid": 99}
             ]
"""
        s.execute(stmt)
        v = s.get_variable("newvar")
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] in ["cmd.exe", "explorer.exe"]
        if v[0]["name"] == "cmd.exe":
            assert v[0]["pid"] == 123
        else:
            assert v[0]["pid"] == 99


def test_new_with_missing_field():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe"}
             ]
"""
        s.execute(stmt)
        v = sorted(s.get_variable("newvar"), key=lambda d: d["name"])
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] in ["cmd.exe", "explorer.exe"]
        assert v[0]["pid"] == "123"
        assert v[1]["pid"] == None


def test_new_with_missing_field_first():
    with Session() as s:
        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""
        s.execute(stmt)
        v = sorted(s.get_variable("newvar"), key=lambda d: d["name"])
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] in ["cmd.exe", "explorer.exe"]
        assert v[0]["pid"] == None
        assert v[1]["pid"] == "99"
