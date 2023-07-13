import json
import os
import shutil

import pytest

from kestrel.codegen.display import DisplayWarning
from kestrel.session import Session

from .utils import set_empty_kestrel_config, set_no_prefetch_kestrel_config


@pytest.fixture
def proc_bundle_file():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cwd, "doctored-1k.json")


@pytest.fixture()
def file_stix_bundles():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(cwd, "test_bundle_4.json"),
        os.path.join(cwd, "test_bundle_5.json"),
    ]


@pytest.fixture()
def nt_stix_bundles():
    cwd = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(cwd, "test_bundle_nt_1.json"),
        os.path.join(cwd, "test_bundle_nt_2.json"),
    ]


@pytest.fixture()
def set_stixshifter_stix_bundles():
    cfg = '{"auth": {"username": "","password": ""}}'
    connector = "stix_bundle"
    stixshifter_data_url = "https://raw.githubusercontent.com/opencybersecurityalliance/stix-shifter/develop/data/cybox"
    host1 = f"{stixshifter_data_url}/carbon_black/cb_observed_156.json"
    host2 = f"{stixshifter_data_url}/qradar/qradar_custom_process_observable.json"

    os.environ["STIXSHIFTER_HOST1_CONNECTION"] = json.dumps({"host": host1})
    os.environ["STIXSHIFTER_HOST1_CONNECTOR"] = connector
    os.environ["STIXSHIFTER_HOST1_CONFIG"] = cfg
    os.environ["STIXSHIFTER_HOST2_CONNECTION"] = json.dumps({"host": host2})
    os.environ["STIXSHIFTER_HOST2_CONNECTOR"] = connector
    os.environ["STIXSHIFTER_HOST2_CONFIG"] = cfg

    # use `yield` to pause here before a test finished
    # https://docs.pytest.org/en/latest/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization
    yield None

    # this clean up will be executed when the test (that uses the fixture) exits
    ss_envs = [k for k in list(os.environ.keys()) if k.startswith("STIXSHIFTER_")]
    for ss_env in ss_envs:
        del os.environ[ss_env]


def test_get_single_file(file_stix_bundles):
    with Session() as s:
        stmt = f"""
                var = GET process
                      FROM file://{file_stix_bundles[0]}
                      WHERE [process:name='compattelrunner.exe']
                """

        s.execute(stmt)
        v = s.get_variable("var")
        print(json.dumps(v, indent=4))
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_single_file_limit(file_stix_bundles):
    with Session() as s:
        stmt = f"""
                var = GET process
                      FROM file://{file_stix_bundles[0]}
                      WHERE [process:name='compattelrunner.exe']
                      LIMIT 1
                """

        s.execute(stmt)
        v = s.get_variable("var")
        print(json.dumps(v, indent=4))
        assert len(v) == 1
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_single_file_limit_1(file_stix_bundles):
    with Session() as s:
        stmt = f"""
                var = GET process
                      FROM file://{file_stix_bundles[0]}
                      WHERE [process:name='compattelrunner.exe']
                      LIMIT 10
                """

        s.execute(stmt)
        v = s.get_variable("var")
        print(json.dumps(v, indent=4))
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_multiple_file_stix_bundles(file_stix_bundles):
    with Session() as s:
        file_bundles = ",".join(file_stix_bundles)
        stmt = f"""
                var = GET process
                      FROM file://{file_bundles}
                      WHERE name = 'compattelrunner.exe'
                """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_multiple_file_stix_bundles_limit(file_stix_bundles):
    with Session() as s:
        file_bundles = ",".join(file_stix_bundles)
        stmt = f"""
                var = GET process
                      FROM file://{file_bundles}
                      WHERE name = 'compattelrunner.exe'
                      LIMIT 3
                """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 3
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_multiple_file_stix_bundles_limit_1(file_stix_bundles):
    with Session() as s:
        file_bundles = ",".join(file_stix_bundles)
        stmt = f"""
                var = GET process
                      FROM file://{file_bundles}
                      WHERE name = 'compattelrunner.exe'
                      LIMIT 4
                """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 4
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_multiple_file_stix_bundles_limit_2(file_stix_bundles):
    with Session() as s:
        file_bundles = ",".join(file_stix_bundles)
        stmt = f"""
                var = GET process
                      FROM file://{file_bundles}
                      WHERE name = 'compattelrunner.exe'
                      LIMIT 8
                """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_single_stixshifter_stix_bundle(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST2
                     WHERE [ipv4-addr:value = '127.0.0.1']
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
               """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 6
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] == "powershell.exe"


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_single_stixshifter_stix_bundle_limit(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST2
                     WHERE [ipv4-addr:value = '127.0.0.1']
                     LIMIT 4
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
               """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 4
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] == "powershell.exe"


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_multiple_stixshifter_stix_bundles(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
               """

        s.execute(stmt)
        v = s.get_variable("var")

        # The extended graph [ipv4-addr:value = '127.0.0.1'] is recognized and
        # merged to prefetch query, resultsing in limited (32) processes. If
        # not used by prefetch, the total number of process records prefetched
        # is 240.
        assert len(v) == 32
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] in [
                "powershell.exe",
                "(unknown)",
                "explorer.exe",
                "firefox.exe",
                "ntoskrnl.exe",
                "teamviewer_service.exe",
                "teamviewer.exe",
                "vmware.exe",
                "dashost.exe",
                "applemobiledeviceservice.exe",
                "svctest.exe",
                "vmware-hostd.exe",
            ]


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_multiple_stixshifter_stix_bundles_limit(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     LIMIT 10
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
               """

        s.execute(stmt)
        v = s.get_variable("var")

        # The extended graph [ipv4-addr:value = '127.0.0.1'] is recognized and
        # merged to prefetch query, resultsing in limited (32) processes. If
        # not used by prefetch, the total number of process records prefetched
        # is 240.
        assert len(v) == 20
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] in [
                "powershell.exe",
                "(unknown)",
                "explorer.exe",
                "firefox.exe",
                "ntoskrnl.exe",
                "teamviewer_service.exe",
                "teamviewer.exe",
                "vmware.exe",
                "dashost.exe",
                "applemobiledeviceservice.exe",
                "svctest.exe",
                "vmware-hostd.exe",
            ]


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_multiple_stixshifter_stix_bundles_limit_1(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     LIMIT 15
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
               """

        s.execute(stmt)
        v = s.get_variable("var")

        # The extended graph [ipv4-addr:value = '127.0.0.1'] is recognized and
        # merged to prefetch query, resultsing in limited (32) processes. If
        # not used by prefetch, the total number of process records prefetched
        # is 240.
        assert len(v) == 28
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] in [
                "powershell.exe",
                "(unknown)",
                "explorer.exe",
                "firefox.exe",
                "ntoskrnl.exe",
                "teamviewer_service.exe",
                "teamviewer.exe",
                "vmware.exe",
                "dashost.exe",
                "applemobiledeviceservice.exe",
                "svctest.exe",
                "vmware-hostd.exe",
            ]


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_multiple_stixshifter_stix_bundles_limit_2(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     LIMIT 50
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
               """

        s.execute(stmt)
        v = s.get_variable("var")

        # The extended graph [ipv4-addr:value = '127.0.0.1'] is recognized and
        # merged to prefetch query, resultsing in limited (32) processes. If
        # not used by prefetch, the total number of process records prefetched
        # is 240.
        assert len(v) == 32
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] in [
                "powershell.exe",
                "(unknown)",
                "explorer.exe",
                "firefox.exe",
                "ntoskrnl.exe",
                "teamviewer_service.exe",
                "teamviewer.exe",
                "vmware.exe",
                "dashost.exe",
                "applemobiledeviceservice.exe",
                "svctest.exe",
                "vmware-hostd.exe",
            ]


def test_last_datasource(proc_bundle_file):
    with Session() as s:
        stmt = f"""
                a = GET process
                    FROM file://{proc_bundle_file}
                    WHERE name = "cmd.exe"
                b = GET process
                    WHERE name = 'svchost.exe'
                """

        output = s.execute(stmt)
        a = s.get_variable("a")
        b = s.get_variable("b")
        assert len(a) == 14
        assert len(b) == 704


def test_relative_file_path(tmp_path):
    data_file_path = "doctored-1k.json"
    ori_path = os.path.join(
        os.path.dirname(__file__), data_file_path
    )
    shutil.copy2(ori_path, tmp_path)
    os.chdir(tmp_path)

    with Session() as s:
        stmt = f"""
                a = GET process
                    FROM file://{data_file_path}
                    WHERE name = "cmd.exe"
                b = GET process
                    FROM file://./{data_file_path}
                    WHERE name = 'svchost.exe'
                """
        output = s.execute(stmt)
        a = s.get_variable("a")
        b = s.get_variable("b")
        assert len(a) == 14
        assert len(b) == 704


def test_get_wrong_type(file_stix_bundles):
    with Session() as s:
        stmt = f"""
                var = GET foo
                      FROM file://{file_stix_bundles[0]}
                      WHERE name = "compattelrunner.exe"
                """

        output = s.execute(stmt)
        warnings = []
        for o in output:
            print(json.dumps(o.to_dict(), indent=4))
            if isinstance(o, DisplayWarning):
                warnings.append(o)
        assert len(warnings) == 1
        assert "foo" in warnings[0].to_string()
        v = s.get_variable("var")
        print(json.dumps(v, indent=4))
        assert len(v) == 0


def test_get_repeated(proc_bundle_file):
    """process objects may not have deterministic IDs, so we need to prevent duplicate entries somehow"""
    with Session() as s:
        stmt = f"""
                var = GET process
                      FROM file://{proc_bundle_file}
                      WHERE name = "cmd.exe"
                """
        output = s.execute(stmt)
        data = output[0].to_dict()["data"]["variables updated"][0]
        print(json.dumps(data, indent=4))
        n_ent = data["#(ENTITIES)"]
        n_rec = data["#(RECORDS)"]

        # Re-run; counts should not change
        output = s.execute(stmt)
        data = output[0].to_dict()["data"]["variables updated"][0]
        assert n_ent == data["#(ENTITIES)"]
        assert n_rec == data["#(RECORDS)"]

        stmt = f"""
                var = GET file
                      FROM file://{proc_bundle_file}
                      WHERE [file:name = 'cmd.exe']
                """
        output = s.execute(stmt)
        data = output[0].to_dict()["data"]["variables updated"][0]
        print(json.dumps(data, indent=4))
        assert data["#(ENTITIES)"] > 0
        assert data["#(RECORDS)"] > 0


@pytest.mark.parametrize(
    "num, unit, count",
    [
        # They're mostly out of the time range
        (1, "d", 0),
        (10, "days", 0),
        (9, "h", 0),
        (99, "hours", 0),
        (5, "m", 0),
        (50, "minutes", 0),
        (3600, "s", 0),
        (30, "SECONDS", 0),
        (3650, "DAYS", 2),  # This will fail sometime in 2031
    ],
)
def test_get_relative_timespan(file_stix_bundles, num, unit, count):
    with Session() as s:
        stmt = f"""
                var = GET process
                      FROM file://{file_stix_bundles[0]}
                      WHERE name='compattelrunner.exe' LAST {num} {unit}
                """

        s.execute(stmt)
        v = s.get_variable("var")
        print(json.dumps(v, indent=4))
        assert len(v) == count


def test_get_referred_variable(nt_stix_bundles):
    with Session() as s:
        stmt1 = f"""
                 nt111 = GET network-traffic
                         FROM file://{nt_stix_bundles[0]}
                         WHERE dst_ref.value = '192.168.56.112'
                 """
        s.execute(stmt1)

        stmt2 = f"""
                 nt112 = GET network-traffic
                         FROM file://{nt_stix_bundles[1]}
                         WHERE src_port = nt111.src_port
                 """
        s.execute(stmt2)

        stmt3 = f"""
                 nt112y = GET network-traffic
                          FROM file://{nt_stix_bundles[1]}
                          WHERE src_ref.value = nt111.src_ref.value
                 """
        s.execute(stmt3)

        s.config["stixquery"]["timerange_start_offset"] = -10
        s.config["stixquery"]["timerange_stop_offset"] = 10
        stmt4 = f"""
                 nt112z = GET network-traffic
                          FROM file://{nt_stix_bundles[1]}
                          WHERE src_ref.value = nt111.src_ref.value
                 """
        s.execute(stmt4)

        nt112 = s.get_variable("nt112")
        nt112y = s.get_variable("nt112y")
        nt112z = s.get_variable("nt112z")

        # src_port should uniquely identify the 4 network-traffic
        # between the two hosts: 111 and 112
        assert len(nt112) == 4

        # there are many nt from 111 to 112 in a larger time range
        # by default, offset are -300, 300 seconds, which will give more results
        assert len(nt112y) == 7

        # reset the offsets to nearly 0 (need to tolerate clock sync diff)
        # now it should go back to 4
        assert len(nt112z) == 4


def test_regex_escaping_in_stix_bundle(nt_stix_bundles):
    with Session() as s:
        stmt1 = f"""
                 d = GET directory
                     FROM file://{nt_stix_bundles[0]}
                     WHERE path MATCHES 
                 """ + r"'C:\\\\Windows.*'" # FIXME: r"'C:\\Windows.*' is expected
        s.execute(stmt1)
        d = s.get_variable("d")
        assert len(d) == 1
