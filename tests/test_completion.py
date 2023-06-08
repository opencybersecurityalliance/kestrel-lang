import os
import pytest
import pathlib
from kestrel.codegen.relations import all_relations
from kestrel.session import Session
from kestrel.syntax.utils import (
    LITERALS,
    AGG_FUNCS,
    TRANSFORMS,
    EXPRESSION_OPTIONS,
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
def datasource_env_setup(tmp_path):

    profiles = f"""profiles:
    thost101:
        connector: elastic_ecs
        connection:
            host: elastic.securitylog.company.com
            port: 9200
            selfSignedCert: false # this means do NOT check cert
            indices: asdfqwer
        config:
            auth:
                id: VuaCfGcBCdbkQm-e5aOx
                api_key: ui2lp2axTNmsyakw9tvNnw
    thost102:
        connector: qradar
        connection:
            host: qradar.securitylog.company.com
            port: 443
        config:
            auth:
                SEC: 123e4567-e89b-12d3-a456-426614174000
    thost103:
        connector: cbcloud
        connection:
            host: cbcloud.securitylog.company.com
            port: 443
        config:
            auth:
                org-key: D5DQRHQP
                token: HT8EMI32DSIMAQ7DJM
    """

    profile_file = tmp_path / "stixshifter.yaml"
    with open(profile_file, "w") as pf:
        pf.write(profiles)

    os.environ["KESTREL_STIXSHIFTER_CONFIG"] = str(
        profile_file.expanduser().resolve()
    )

    # https://docs.pytest.org/en/latest/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization
    yield None
    del os.environ["KESTREL_STIXSHIFTER_CONFIG"]


@pytest.fixture
def analytics_env_setup(tmp_path):

    analytics_module_path = str(
        pathlib.Path(__file__).resolve().parent / "python_analytics_mockup.py"
    )

    profiles = f"""profiles:
    enrich_one_variable:
        module: {analytics_module_path}
        func: enrich_one_variable
    html_visualization:
        module: {analytics_module_path}
        func: html_visualization
    enrich_multiple_variables:
        module: {analytics_module_path}
        func: enrich_multiple_variables
    enrich_variable_with_arguments:
        module: {analytics_module_path}
        func: enrich_variable_with_arguments
    """

    profile_file = tmp_path / "pythonanalytics.yaml"
    with open(profile_file, "w") as pf:
        pf.write(profiles)

    os.environ["KESTREL_PYTHON_ANALYTICS_CONFIG"] = str(
        profile_file.expanduser().resolve()
    )


@pytest.fixture
def a_session(datasource_env_setup, analytics_env_setup):
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
        ("disp conns ", EXPRESSION_OPTIONS),
        ("disp conns LIMIT 5 ", EXPRESSION_OPTIONS - {"LIMIT"}),
        ("disp conns ATTR name ", EXPRESSION_OPTIONS - {"ATTR"}),
        ("disp conns WHERE name = 'abc' ", EXPRESSION_OPTIONS - {"WHERE"}),
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
            "urls = GET url FROM ",
            ["_", "conns", "file://", "http://", "https://", "stixshifter://"],
        ),
        ( "urls = GET url FROM stixshi", {"fter://"}),
        ( "urls = GET url FROM stixshifter://", {"thost101", "thost102", "thost103"}),
        ( "urls = GET url FROM stixshifter://thost", {"101", "102", "103"}),
        ("urls = get url where ", []), # TODO: attribute completion
        ("urls = get url where name = 'a' ", {"START"}),
        ("urls = get url where name = 'a' START 2022-01-01T00:00:00Z ", {"STOP"}),
    ],
)
def test_do_complete_cmd_get(datasource_env_setup, a_session, code, expected):
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
        ("procs2 = SORT procs BY ", []), # TODO: attribute completion
    ],
)
def test_do_complete_cmd_sort(a_session, code, expected):
    result = a_session.do_complete(code, len(code))
    assert set(result) == set(expected)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("APPLY ", {"python://", "docker://"}),
        ("APPLY pyth", {"on://"}),
        ("APPLY python://", {"enrich_one_variable", "html_visualization", "enrich_multiple_variables", "enrich_variable_with_arguments"}),
        ("APPLY python://enrich", {"_one_variable", "_multiple_variables", "_variable_with_arguments"}),
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
        ("grps = GROUP conns by ", {"BIN"}), # TODO: attribute completion
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
        ("procs2 = JOIN x, y BY ", []), # TODO: attribute completion
        ("procs2 = JOIN x, y BY a", []),
        ("procs2 = JOIN x, y BY a ", {","}),
        ("procs2 = JOIN x, y BY a,", []), # TODO: attribute completion
        ("procs2 = JOIN x, y BY a, ", []), # TODO: attribute completion
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
