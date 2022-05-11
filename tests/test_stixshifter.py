import pytest
import os

from kestrel.session import Session

from kestrel_datasource_stixshifter.connector import (
    verify_package_origin,
    check_module_availability,
)


def test_verify_package_origin():
    connectors = ["stix_bundle", "qradar", "elastic_ecs", "splunk"]
    for connector_name in connectors:
        verify_package_origin(connector_name)


def test_check_module_availability():
    connectors = ["stix_bundle"]
    for connector_name in connectors:
        check_module_availability(connector_name)


def test_yaml_profiles_refresh(tmp_path):

    profileA = f"""profiles:
profiles:
    host101:
        connector: elastic_ecs
        connection:
            host: elastic.securitylog.company.com
            port: 9200
            indices: host101
        config:
            auth:
                id: profileA
                api_key: qwer
"""

    profileB = f"""profiles:
profiles:
    host101:
        connector: elastic_ecs
        connection:
            host: elastic.securitylog.company.com
            port: 9200
            indices: host101
        config:
            auth:
                id: profileB
                api_key: asdf
"""

    profile_file = tmp_path / "stixshifter.yaml"

    os.environ["KESTREL_STIXSHIFTER_CONFIG"] = str(profile_file.expanduser().resolve())

    with Session() as s:

        with open(profile_file, "w") as pf:
            pf.write(profileA)

        stmt = """
newvar = NEW [ {"type": "process", "name": "cmd.exe", "pid": "123"}
             , {"type": "process", "name": "explorer.exe", "pid": "99"}
             ]
"""
        s.execute(stmt)

        s.data_source_manager.list_data_sources_from_scheme("stixshifter")

        ss_config = s.config["datasources"]["kestrel_datasource_stixshifter"]
        ss_profiles = ss_config["profiles"]
        ss_host101_auth = ss_profiles["host101"]["config"]["auth"]
        assert ss_host101_auth["id"] == "profileA"
        assert ss_host101_auth["api_key"] == "qwer"

        with open(profile_file, "w") as pf:
            pf.write(profileB)

        s.data_source_manager.list_data_sources_from_scheme("stixshifter")

        # need to refresh the pointers since the dict is updated
        ss_profiles = ss_config["profiles"]
        ss_host101_auth = ss_profiles["host101"]["config"]["auth"]
        assert ss_host101_auth["id"] == "profileB"
        assert ss_host101_auth["api_key"] == "asdf"
