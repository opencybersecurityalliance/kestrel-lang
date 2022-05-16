import json
import os

import pytest

from kestrel.codegen.display import DisplayWarning
from kestrel.session import Session


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


def test_get_single_file(file_stix_bundles):
    with Session() as s:
        stmt = f"var = GET process FROM file://{file_stix_bundles[0]} WHERE [process:name='compattelrunner.exe']"

        s.execute(stmt)
        v = s.get_variable("var")
        print(json.dumps(v, indent=4))
        assert len(v) == 2
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_multiple_file_stix_bundles(file_stix_bundles):
    with Session() as s:
        file_bundles = ",".join(file_stix_bundles)
        stmt = f"var = GET process FROM file://{file_bundles} WHERE [process:name='compattelrunner.exe']"

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 5
        assert v[0]["type"] == "process"
        assert v[0]["name"] == "compattelrunner.exe"


def test_get_single_stixshifter_stix_bundle(set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = "var = GET process FROM HOST2 WHERE [ipv4-addr:value = '127.0.0.1']"

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 6 or len(v) == 8  # FIXME: prefetch causing duplicates
        for i in range(len(v)):
            assert v[i]["type"] == "process"
            assert v[i]["name"] == "powershell.exe"


def test_get_multiple_stixshifter_stix_bundles(set_stixshifter_stix_bundles):
    with Session() as s:
        # default data source schema is stixshifter
        stmt = (
            "var = GET process FROM HOST1,HOST2 WHERE [ipv4-addr:value = '127.0.0.1']"
        )

        s.execute(stmt)
        v = s.get_variable("var")
        assert len(v) == 240 or len(v) == 267  # FIXME: prefetch causing duplicates
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


def test_get_wrong_type(file_stix_bundles):
    with Session() as s:
        stmt = f"var = GET foo FROM file://{file_stix_bundles[0]} WHERE [process:name='compattelrunner.exe']"

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
        stmt = f"var = GET process FROM file://{proc_bundle_file} WHERE [process:name = 'cmd.exe']"
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

        stmt = f"var = GET file FROM file://{proc_bundle_file} WHERE [file:name = 'cmd.exe']"
        output = s.execute(stmt)
        data = output[0].to_dict()["data"]["variables updated"][0]
        print(json.dumps(data, indent=4))
        assert data["#(ENTITIES)"] > 0
        assert data["#(RECORDS)"] > 0
