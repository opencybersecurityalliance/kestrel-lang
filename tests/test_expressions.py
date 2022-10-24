import json

import pytest

from kestrel.session import Session


NEW_PROCS = """
procs = NEW [ {"type": "process", "name": "cmd.exe", "pid": 123, "x_foo": "bar"}
            , {"type": "process", "name": "explorer.exe", "pid": 99}]
"""


@pytest.mark.parametrize(
    "attrs, unexpected",
    [
        ("pid", {"name"}),
        ("name", {"pid"}),
        ("pid,name", set()),
    ],
)
def test_expr_attr(attrs, unexpected):
    with Session() as s:
        s.execute(NEW_PROCS)
        out = s.execute(f"DISP procs ATTR {attrs}")
        data = out[0].to_dict()["data"]
        print(json.dumps(data, indent=4))
        actual = set(data[0].keys())
        expected = set(attrs.split(","))
        assert expected == actual
        assert len(unexpected & actual) == 0


@pytest.mark.parametrize(
    "prop, direction, expected",
    [
        ("pid", "asc", [99, 123]),
        ("pid", "desc", [123, 99]),
        ("name", "asc", ["cmd.exe", "explorer.exe"]),
        ("name", "desc", ["explorer.exe", "cmd.exe"]),
    ],
)
def test_expr_sort(prop, direction, expected):
    with Session() as s:
        s.execute(NEW_PROCS)
        out = s.execute(f"DISP procs sort by {prop} {direction}")
        data = out[0].to_dict()["data"]
        print(json.dumps(data, indent=4))
        actual = [p[prop] for p in data]
        assert actual == expected


@pytest.mark.parametrize(
    "limit, offset, expected",
    [
        (5, 0, [99, 123]),
        (1, 0, [99]),
        (2, 1, [123]),
        (1, 1, [123]),
    ],
)
def test_expr_limit_offset(limit, offset, expected):
    with Session() as s:
        s.execute(NEW_PROCS)
        out = s.execute(f"DISP procs SORT BY pid ASC LIMIT {limit} OFFSET {offset}")
        data = out[0].to_dict()["data"]
        print(json.dumps(data, indent=4))
        actual = [p["pid"] for p in data]
        assert actual == expected


@pytest.mark.parametrize(
    "col, op, val, expected",
    [
        ("pid", "=", 99, [99]),
        ("pid", "<", 100, [99]),
        ("pid", ">=", 100, [123]),
        ("x_foo", "IS NULL", "", [99]),
        ("x_foo", "IS NOT NULL", "", [123]),
        ("x_foo", "=", "'bar'", [123]),
    ],
)
def test_expr_where(col, op, val, expected):
    with Session() as s:
        s.execute(NEW_PROCS)
        for stmt in (
            f"DISP procs WHERE {col} {op} {val}",
            f"DISP procs WHERE [{col} {op} {val}]",
        ):
            out = s.execute(stmt)
            data = out[0].to_dict()["data"]
            print(json.dumps(data, indent=4))
            actual = [p["pid"] for p in data]
            assert actual == expected


def test_expr_assign_where():
    with Session() as s:
        s.execute(NEW_PROCS)
        out = s.execute("x = procs WHERE pid > 100")
        data = out[0].to_dict()["data"]
        print(json.dumps(data, indent=4))
        vars_updated = data["variables updated"]
        assert vars_updated[0]["#(ENTITIES)"] == 1
