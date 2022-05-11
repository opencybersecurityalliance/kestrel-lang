import pytest

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
