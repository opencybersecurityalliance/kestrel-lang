from stix_shifter.stix_translation import stix_translation

from kestrel.session import Session
from kestrel_datasource_stixshifter.connector import check_module_availability
from kestrel_datasource_stixshifter.interface import fast_translate


SAMPLE_RESULT = {
    "success": True,
    "data": [
        {
            "process": {
                "name": "svchost.exe",
                "pid": 1744,
                "entity_id": "{8dfc401c-f5a9-6068-2300-000000001300}",
                "executable": "C:\\Windows\\System32\\svchost.exe"
            },
            "@timestamp": "2021-04-10T05:35:45.333Z",
            "destination": {
                "port": 49343,
                "ip": "127.0.0.1",
                "domain": "thl-win.example.com"
            },
            "host": {
                "hostname": "thl-win",
                "os": {
                    "build": "17763.1817",
                    "kernel": "10.0.17763.1817 (WinBuild.160101.0800)",
                    "name": "Windows Server 2019 Standard",
                    "family": "windows",
                    "version": "10.0",
                    "platform": "windows"
                },
                "ip": [
                    "2001:db8:a::123",
                    "198.51.100.101",
                    "10.0.0.141"
                ],
                "name": "thl-win.example.com",
                "id": "d3f820f9-f601-4dd8-bd48-5c13549a6027",
                "mac": [
                    "00:25:96:12:34:56"
                ],
                "architecture": "x86_64"
            },
            "source": {
                "port": 49343,
                "ip": "127.0.0.1",
                "domain": "thl-win.example.com"
            },
            "event": {
                "code": 3,
                "provider": "Microsoft-Windows-Sysmon",
                "kind": "event",
                "created": "2021-04-10T05:35:43.069Z",
                "module": "sysmon",
                "action": "Network connection detected (rule: NetworkConnect)",
                "category": [
                    "network"
                ],
                "type": [
                    "connection",
                    "start",
                    "protocol"
                ]
            },
            "user": {
                "domain": "NT AUTHORITY",
                "name": "SYSTEM"
            },
            "network": {
                "community_id": "1:ZXhhbXBsZQ==",
                "protocol": "-",
                "transport": "udp",
                "type": "ipv4",
                "direction": "egress"
            },
            "tags": [
                "beats_input_codec_plain_applied"
            ]
        }
    ]
}


def test_fast_translate():
    connector_name = "elastic_ecs"
    check_module_availability(connector_name)
    connector_results = SAMPLE_RESULT["data"]
    translation = stix_translation.StixTranslation()
    translation_options = {}
    query_id = "8df266aa-2901-4a94-ace9-a4403e310fa1"
    identity = {"id": "identity--" + query_id, "name": connector_name}
    with Session() as s:
        fast_translate(connector_name, connector_results,
                       translation, translation_options,
                       identity, query_id, s.store)
