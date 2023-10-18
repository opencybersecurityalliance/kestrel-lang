import json
import os
import pytest

from kestrel.session import Session

from .utils import set_no_prefetch_kestrel_config


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


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_single_stixshifter_stix(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
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
def test_get_single_stixshifter_stix_limit(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST2
                     WHERE [ipv4-addr:value = '127.0.0.1']
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
                     LIMIT 4
               """

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 4
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] == "powershell.exe"


# stix_bundle connector does not support extended graph
# disable prefetch to test
def test_get_multiple_stixshifter_stix(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
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
def test_get_multiple_stixshifter_stix_limit(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
                     LIMIT 10
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
def test_get_multiple_stixshifter_stix_limit_1(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
                     LIMIT 15
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
def test_get_multiple_stixshifter_stix_limit_2(set_no_prefetch_kestrel_config, set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = """
               var = GET process
                     FROM HOST1,HOST2
                     WHERE ipv4-addr:value = '127.0.0.1'
                     START 2019-01-01T00:00:00Z STOP 2023-01-01T00:00:00Z
                     LIMIT 50
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
