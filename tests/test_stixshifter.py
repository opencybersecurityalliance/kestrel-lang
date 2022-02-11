import pytest

from kestrel_datasource_stixshifter.interface import (
    verify_package_origin,
    check_module_availability,
)


@pytest.fixture()
def connectors():
    return [
        ("stix_bundle", "stix-shifter-modules-stix-bundle"),
    ]


def test_verify_package_origin(connectors):
    for (connector_name, package_name) in connectors:
        verify_package_origin(connector_name, package_name)


def test_check_module_availability(connectors):
    for (connector_name, package_name) in connectors:
        check_module_availability(connector_name)
