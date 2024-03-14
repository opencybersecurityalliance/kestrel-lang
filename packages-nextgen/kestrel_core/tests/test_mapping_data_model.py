import pytest

from kestrel.mapping.data_model import (
    load_mapping,
    reverse_mapping,
    translate_comparison_to_native,
    translate_comparison_to_ocsf,
)


# A "custom" mapping for an opensearch/elasticsearch datasource.
# This mapping works with data from Blue Team Village's 2023 DefCon CTF, for example.
WINLOGBEAT_MAPPING = {
    "file": {
        "path": "file.path",
        "name": "file.name"
    },
    "process": {
        "cmd_line": "winlog.event_data.CommandLine",
        "pid": {
            "native_field": "process.pid",
            "native_value": "to_str",
            "ocsf_value": "to_int"
        },
        "uid": "winlog.event_data.ProcessGuid",
        "file": {
            "path": "winlog.event_data.Image",
            "name": [
                {
                    "native_field": "winlog.event_data.Image",
                    "native_op": "LIKE",
                    "native_value": "endswith",
                    "ocsf_value": "basename"
                }
            ],
            "parent_folder": [
                {
                    "native_field": "winlog.event_data.Image",
                    "native_op": "LIKE",
                    "native_value": "startswith",
                    "ocsf_value": "dirname"
                }
            ]
        },
        "parent_process": {
            "cmd_line": "winlog.event_data.ParentCommandLine",
            "pid": "winlog.event_data.ParentProcessId",
            "uid": "winlog.event_data.ParentProcessGuid",
            "file": {
                "path": "winlog.event_data.ParentImage",
                "name": [
                    {
                        "native_field": "winlog.event_data.ParentImage",
                        "native_op": "LIKE",
                        "native_value": "endswith",
                        "ocsf_value": "basename"
                    }
                ],
                "parent_folder": [
                    {
                        "native_field": "winlog.event_data.ParentImage",
                        "native_op": "LIKE",
                        "native_value": "startswith",
                        "ocsf_value": "dirname"
                    }
                ]
            }
        }
    },
    "dst_endpoint": {
        "ip": "winlog.event_data.DestinationIp",
        "port": "winlog.event_data.DestinationPort"
    },
    "src_endpoint": {
        "ip": "winlog.event_data.SourceIp",
        "port": "winlog.event_data.SourcePort"
    }
}


# Simplified subset of the standard mapping
STIX_MAPPING = {
    "device": {
        "ip": "ipv4-addr:value"
    },
    "endpoint": {
        "ip": "ipv4-addr:value"
    },
}


# This mapping is used in 2 places:
# - frontend comparison from ECS to OCSF
# - backend comparison from OCSF to ECS (datasource)
ECS_MAPPING = load_mapping("ecs")


def test_reverse_mapping_ipv4():
    reverse_map = reverse_mapping(STIX_MAPPING)
    ipv4 = reverse_map["ipv4-addr:value"]
    assert isinstance(ipv4, list)
    assert set(ipv4) == {"device.ip", "endpoint.ip"}


def test_reverse_mapping_executable():
    reverse_map = reverse_mapping(ECS_MAPPING)
    exe = reverse_map["process.executable"]
    assert isinstance(exe, list)
    assert "process.file.path" in exe
    for item in exe:
        if isinstance(item, dict):
            assert "ocsf_field" in item
            if item["ocsf_field"] == "process.file.name":
                # Make sure all metadata from the mapping got reversed
                assert item["native_value"] == "endswith"
                assert item["native_op"] == "LIKE"
                assert item["ocsf_value"] == "basename"



@pytest.mark.parametrize(
    "dmm, field, op, value, expected_result",
    [
        (WINLOGBEAT_MAPPING, "process.file.path", "=", "C:\\TMP\\foo.exe",
         [("winlog.event_data.Image", "=", "C:\\TMP\\foo.exe")]),
        (WINLOGBEAT_MAPPING, "process.file.name", "=", "foo.exe",
         [("winlog.event_data.Image", "LIKE", "%\\foo.exe")]),
        (ECS_MAPPING, "process.file.path", "=", "C:\\TMP\\foo.exe",
         [("process.executable", "=", "C:\\TMP\\foo.exe")]),
        (ECS_MAPPING, "process.file.name", "=", "foo.exe",
         [("process.executable", "LIKE", "%\\foo.exe")]),
    ],
)
def test_translate_comparison_to_native(dmm, field, op, value, expected_result):
    assert translate_comparison_to_native(dmm, field, op, value) == expected_result


@pytest.mark.parametrize(
    "dmm, field, op, value, expected_result",
    [
        # (WINLOGBEAT_MAPPING, "winlog.event_data.Image", "=", "C:\\TMP\\foo.exe",  #TODO: don't need this test case
        #  [
        #     ("process.file.path", "=", "C:\\TMP\\foo.exe"),
        #     ("process.file.name", "=", "foo.exe"),
        #     ("process.file.parent_folder", "=", "C:\\TMP"),
        #  ]),
        # (WINLOGBEAT_MAPPING, "winlog.event_data.Image", "LIKE", "%\\foo.exe",  #TODO: don't need this test case
        #  [
        #     ("process.file.path", "LIKE", "%\\foo.exe"),
        #     ("process.file.name", "LIKE", "foo.exe"),
        #     ("process.file.parent_folder", "LIKE", "%"),
        #  ]),
        (ECS_MAPPING, "process.executable", "=", "C:\\TMP\\foo.exe",
         [
            ("process.file.path", "=", "C:\\TMP\\foo.exe"),
            ("process.file.name", "=", "foo.exe"),
            ("process.file.parent_folder", "=", "C:\\TMP"),
         ]),
        (ECS_MAPPING, "process.executable", "LIKE", "%\\foo.exe",
         [
            ("process.file.path", "LIKE", "%\\foo.exe"),
            ("process.file.name", "LIKE", "foo.exe"),     #TODO: could optimize this to "="
            ("process.file.parent_folder", "LIKE", "%"),  #TODO: could eliminate this?
         ]),
        (STIX_MAPPING, "ipv4-addr:value", "=", "198.51.100.13",
         [
             ("device.ip", "=", "198.51.100.13"),
             ("endpoint.ip", "=", "198.51.100.13"),
         ]),
    ],
)
def test_translate_comparison_to_ocsf(dmm, field, op, value, expected_result):
    """Test the translate function."""
    reverse_dmm = reverse_mapping(dmm)  # Make the dmms fixtures?
    assert set(translate_comparison_to_ocsf(reverse_dmm, field, op, value)) == set(expected_result)
