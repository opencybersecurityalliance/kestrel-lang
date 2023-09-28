import pytest
import os
import sys
import subprocess
import importlib
from importlib.metadata import version

from kestrel.session import Session

from kestrel_datasource_stixshifter.connector import (
    verify_package_origin,
    setup_connector_module,
    get_package_name,
)

from kestrel_datasource_stixshifter.config import get_datasource_from_profiles


def test_verify_package_origin():
    connectors = ["stix_bundle", "qradar", "elastic_ecs", "splunk"]
    for connector_name in connectors:
        verify_package_origin(connector_name, "test_version")


def test_setup_connector_module():
    connectors = ["stix_bundle"]
    for connector_name in connectors:
        setup_connector_module(connector_name)
        importlib.import_module("stix_shifter_modules." + connector_name + ".entry_point")


def test_setup_connector_module_w_wrong_version():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "stix-shifter-modules-paloalto==5.0.0"])
    connector_name = "paloalto"
    setup_connector_module(connector_name)
    importlib.import_module("stix_shifter_modules." + connector_name + ".entry_point")
    stixshifter_version = version("stix_shifter")
    package_name = get_package_name(connector_name)
    package_version = version(package_name)
    assert stixshifter_version == package_version


def test_setup_connector_module_dev_connector():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "stix-shifter-modules-datadog==5.0.0"])
    connector_name = "datadog"
    setup_connector_module(connector_name, True)
    importlib.import_module("stix_shifter_modules." + connector_name + ".entry_point")
    package_version = version(get_package_name(connector_name))
    assert package_version == "5.0.0"


def test_yaml_profiles_refresh(tmp_path):

    profileA = f"""
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

    profileB = f"""
profiles:
    host101:
        connector: elastic_ecs
        connection:
            host: elastic.securitylog.company.com
            port: 9200
            indices: host101
            options:
                retrieval_batch_size: 10000
                single_batch_timeout: 120
                cool_down_after_transmission: 5
                allow_dev_connector: True
                dialects:
                    - beats
        config:
            auth:
                id: profileB
                api_key: xxxxxx
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
        connector_name, connection, configuration, retrieval_batch_size, cool_down_after_transmission, allow_dev_connector = get_datasource_from_profiles("host101", ss_profiles)
        assert connector_name == "elastic_ecs"
        assert configuration["auth"]["id"] == "profileA"
        assert configuration["auth"]["api_key"] == "qwer"
        assert connection["options"]["timeout"] == 60
        assert connection["options"]["result_limit"] == 2000 * 2
        assert retrieval_batch_size == 2000
        assert cool_down_after_transmission == 0

        with open(profile_file, "w") as pf:
            pf.write(profileB)

        s.data_source_manager.list_data_sources_from_scheme("stixshifter")

        # need to refresh the pointers since the dict is updated
        ss_profiles = ss_config["profiles"]
        connector_name, connection, configuration, retrieval_batch_size, cool_down_after_transmission, allow_dev_connector = get_datasource_from_profiles("host101", ss_profiles)
        assert connector_name == "elastic_ecs"
        assert configuration["auth"]["id"] == "profileB"
        assert configuration["auth"]["api_key"] == "xxxxxx"
        assert connection["options"]["timeout"] == 120
        assert connection["options"]["result_limit"] == 10000 * 2
        assert retrieval_batch_size == 10000
        assert cool_down_after_transmission == 5
        assert allow_dev_connector == True

    del os.environ["KESTREL_STIXSHIFTER_CONFIG"]
