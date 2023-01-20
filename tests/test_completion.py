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
        # ("procs = FIND process ", {"created", "loaded", "linked"}),
        ("procs = FIND process ", all_relations),
        ("procs = FIND process l", {"oaded", "inked"}),
        ("procs = FIND process c", {"reated", "ontained"}),
        ("procs = FIND process created ", {"conns", "_", "BY"}),
        ("procs = FIND process created BY ", {"conns", "_"}),
    ],
)
def test_do_complete_cmd_find(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("procs2 = SORT procs ", {"BY"}),
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
        ("procs2 = SORT procs ", {"BY"}),
    ],
)
def test_do_complete_cmd_sort(a_session, code, expected):
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
