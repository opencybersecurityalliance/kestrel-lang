import os
import pytest

from kestrel.session import Session


NEW_PROCS = """
p = NEW [
          {"type": "process", "name": "cmd.exe", "command_line": "cmd -c dir"},
          {"type": "process", "name": "explorer.exe", "pid": "99"}
        ]
"""

@pytest.fixture
def proc_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "doctored-1k.json")


@pytest.mark.parametrize(
    "stmt, expected",
    [
        ("x = p", 2),
        ("x = p WHERE pid = 99", 1),
        ("x = p WHERE command_line IS NULL", 1),
        ("x = p WHERE command_line IS NOT NULL", 1),
        ("x = p WHERE command_line LIKE '%cmd%'", 1),
    ],
)
def test_assign_after_new(stmt, expected):
    with Session() as s:
        s.execute(NEW_PROCS)
        s.execute(stmt)
        x = s.get_variable("x")
        assert len(x) == expected, f"ASSIGN error: f{stmt}"


# The * 2 on these counts is due to our inability to dedup process objects
# Need unique IDs on process objects
@pytest.mark.parametrize(
    "stmt, expected",
    [
        ("x = p", 1000 * 2),
        ("x = p WHERE pid = 1380", 106 * 2),
        ("x = p WHERE command_line IS NULL", 948 * 2),
        ("x = p WHERE command_line IS NOT NULL", 52 * 2),
        ("x = p WHERE command_line LIKE '%/node%'", 1 * 2),
        ("x = p WHERE pid = 5960 OR name = 'taskeng.exe'", 2 * 2),
        ("x = p WHERE (pid = 5960 OR name = 'taskeng.exe') AND command_line IS NULL", 0),
    ],
)
def test_assign_after_get(proc_bundle_file, stmt, expected):
    with Session() as s:
        s.execute(("p = GET process"
                   f" FROM file://{proc_bundle_file}"
                   "  WHERE [process:pid > 0]"))
        s.execute(stmt)
        x = s.get_variable("x")
        assert len(x) == expected, f"ASSIGN error: {stmt}"
