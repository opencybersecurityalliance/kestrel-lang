import os
import pytest
from kestrel.codegen.relations import all_relations
from kestrel.session import Session
from kestrel.syntax.utils import (
    LITERALS,
    AGG_FUNCS,
    TRANSFORMS,
)


KNOWN_ETYPES = {
    "artifact",
    "autonomous-system",
    "directory",
    "domain-name",
    "email-addr",
    "email-message",
    "file",
    "ipv4-addr",
    "ipv6-addr",
    "mac-addr",
    "mutex",
    "network-traffic",
    "process",
    "software",
    "url",
    "user-account",
    "windows-registry-key",
    "x-ibm-finding",
    "x-oca-asset",
    "x-oca-event",
}


@pytest.fixture
def a_session():
    cwd = os.path.dirname(os.path.abspath(__file__))
    bundle = os.path.join(cwd, "test_bundle.json")
    session = Session(debug_mode=True)
    stmt = (
        "conns = get network-traffic"
        f" from file://{bundle}"
        " where [network-traffic:dst_port < 10000]"
    )
    session.execute(stmt)
    return session


@pytest.mark.parametrize(
    "code, expected",
    [
        ("x", []), # No suggestion
        ("c", []), # No suggestion on existing variable name if first token in statement
        ("x ", {"="}),
        (
            "procs = ",
            {"GET", "FIND", "JOIN", "SORT", "GROUP", "LOAD", "NEW", "conns", "_"}
            | TRANSFORMS,
        ),
    ],
)
def test_do_complete_variable_as_first_token(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("disp ", {"conns", "_"} | TRANSFORMS),
        ("disp c", {"onns"}),
        ("disp conns", []),
        ("disp conns ", {"LIMIT", "ATTR", "SORT", "WHERE", "OFFSET"}),
        ("disp conns LIMIT 5 ", {"ATTR", "SORT", "WHERE", "OFFSET"}),
        ("disp conns ATTR name ", {"LIMIT", "SORT", "WHERE", "OFFSET"}),
        ("disp conns WHERE name = 'abc' ", {"LIMIT", "SORT", "ATTR", "OFFSET"}),
    ],
)
def test_do_complete_disp(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("procs = G", {"ET", "ROUP"}),
        ("urls = g", ["et", "roup"]),
        ("urls = ge", ["t"]),
        ("urls = get ", KNOWN_ETYPES),
        ("urls = get url ", ["FROM", "WHERE"]),
        (
            "urls = get url from ",
            ["_", "conns", "file://", "http://", "https://", "stixshifter://"],
        ),
        ("urls = get url where ", {"% TODO: ATTRIBUTE COMPLETION %"}),
        ("urls = get url where name = 'a' ", {"START"}),
        ("urls = get url where name = 'a' START 2022-01-01T00:00:00Z ", {"STOP"}),
    ],
)
def test_do_complete_cmd_get(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("procs = F", {"IND"}),
        ("procs = FI", {"ND"}),
        ("procs = FIN", {"D"}),
        ("procs = FIND", []),
        ("procs = FIND ", KNOWN_ETYPES),
        ("procs = FIND p", ["rocess"]),
        ("procs = FIND process", []),
        ("procs = FIND process ", all_relations),
        ("procs = FIND process l", {"oaded", "inked"}),
        ("procs = FIND process c", {"reated", "ontained"}),
        ("procs = FIND process created ", {"conns", "_", "BY"}),
        ("procs = FIND process created BY ", {"conns", "_"}),
        ("procs = FIND process created BY conns ", {"WHERE", "START"}),
    ],
)
def test_do_complete_cmd_find(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("procs2 = SORT procs ", {"BY"}),
        ("procs2 = SORT procs BY ", {"% TODO: ATTRIBUTE COMPLETION %"}),
    ],
)
def test_do_complete_cmd_sort(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("APPLY abc ON ", {"_", "conns"}),
        ("APPLY abc ON c ", {"WITH"}),
    ],
)
def test_do_complete_cmd_apply(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)

@pytest.mark.parametrize(
    "code, expected",
    [
        ("grps = GR", {"OUP"}),
        ("grps = GROUP ", {"conns", "_"}),
        ("grps = GROUP conns ", {"BY"}),
        ("grps = GROUP conns by ", {"% TODO: ATTRIBUTE COMPLETION %", "BIN"}),
    ],
)
def test_do_complete_cmd_group(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("procs2 = JOIN x, ", {"_", "conns"}),
        ("procs2 = JOIN x, y ", {"BY"}),
        ("procs2 = JOIN x, y BY ", {"% TODO: ATTRIBUTE COMPLETION %"}),
        ("procs2 = JOIN x, y BY a", []),
        ("procs2 = JOIN x, y BY a ", {","}),
        ("procs2 = JOIN x, y BY a,", {"% TODO: ATTRIBUTE COMPLETION %"}),
        ("procs2 = JOIN x, y BY a, ", {"% TODO: ATTRIBUTE COMPLETION %"}),
    ],
)
def test_do_complete_cmd_join(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "time_string, suffix_ts",
    [
        ("START t'2021", ["-01-01T00:00:00.000Z'"]),
        ("START t'2021-05", ["-01T00:00:00.000Z'"]),
        ("START t'2021-05-04", ["T00:00:00.000Z'"]),
        ("START t'2021-05-04T07:", ["00:00.000Z'"]),
        ("START t'2021-05-04T07:30", [":00.000Z'"]),
        ("START t'2021-05-04T07:30:", ["00.000Z'"]),
        ("START t'2021-05-04T07:30:00Z' STOP t'2021", ["-01-01T00:00:00.000Z'"]),
        ("START t'2021-05-04T07:30:00Z' STOP t'2021-05", ["-01T00:00:00.000Z'"]),
        ("START t'2021-05-04T07:30:00Z' STOP t'2021-05-04", ["T00:00:00.000Z'"]),
        ("START t'2021-05-04T07:30:00Z' STOP t'2021-05-04T07:", ["00:00.000Z'"]),
        ("START t'2021-05-04T07:30:00Z' STOP t'2021-05-04T07:30", [":00.000Z'"]),
        ("START t'2021-05-04T07:30:00Z' STOP t'2021-05-04T07:30:", ["00.000Z'"]),
        ("START 2021", ["-01-01T00:00:00.000Z"]),
        ("START 2021-05", ["-01T00:00:00.000Z"]),
        ("START 2021-05-04", ["T00:00:00.000Z"]),
        ("START 2021-05-04T07:", ["00:00.000Z"]),
        ("START 2021-05-04T07:30", [":00.000Z"]),
        ("START 2021-05-04T07:30:", ["00.000Z"]),
        ("START 2021-05-04T07:30:00Z STOP 2021", ["-01-01T00:00:00.000Z"]),
        ("START 2021-05-04T07:30:00Z STOP 2021-05", ["-01T00:00:00.000Z"]),
        ("START 2021-05-04T07:30:00Z STOP 2021-05-04", ["T00:00:00.000Z"]),
        ("START 2021-05-04T07:30:00Z STOP 2021-05-04T07:", ["00:00.000Z"]),
        ("START 2021-05-04T07:30:00Z STOP 2021-05-04T07:30", [":00.000Z"]),
        ("START 2021-05-04T07:30:00Z STOP 2021-05-04T07:30:", ["00.000Z"]),
    ],
)
def test_session_do_complete_timestamp(time_string, suffix_ts):
    with Session(debug_mode=True) as session:
        script = f"x = GET p WHERE n = 'x' {time_string}"
        result = session.do_complete(script, len(script))
        assert result == suffix_ts
