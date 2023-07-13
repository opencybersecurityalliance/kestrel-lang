import logging
import json
import pandas
import pytest
from multiprocessing import Queue

from kestrel_datasource_stixshifter.connector import check_module_availability
from kestrel_datasource_stixshifter import multiproc
from kestrel_datasource_stixshifter.worker.utils import TransmissionResult
from kestrel_datasource_stixshifter.worker import STOP_SIGN


CONNECTOR_NAME = "elastic_ecs"

SAMPLE_RESULT = TransmissionResult(
    "fake transmission worker",
    True,
    [
        {
            "process": {
                "name": "svchost.exe",
                "pid": 1744,
                "entity_id": "{8dfc401c-f5a9-6068-2300-000000001300}",
                "executable": "C:\\Windows\\System32\\svchost.exe",
            },
            "@timestamp": "2021-04-10T05:35:45.333Z",
            "destination": {
                "port": 49343,
                "ip": "127.0.0.1",
                "domain": "thl-win.example.com",
            },
            "host": {
                "hostname": "thl-win",
                "os": {
                    "build": "17763.1817",
                    "kernel": "10.0.17763.1817 (WinBuild.160101.0800)",
                    "name": "Windows Server 2019 Standard",
                    "family": "windows",
                    "version": "10.0",
                    "platform": "windows",
                },
                "ip": ["2001:db8:a::123", "198.51.100.101", "10.0.0.141"],
                "name": "thl-win.example.com",
                "id": "d3f820f9-f601-4dd8-bd48-5c13549a6027",
                "mac": ["00:25:96:12:34:56"],
                "architecture": "x86_64",
            },
            "source": {
                "port": 49343,
                "ip": "127.0.0.1",
                "domain": "thl-win.example.com",
            },
            "event": {
                "code": 3,
                "provider": "Microsoft-Windows-Sysmon",
                "kind": "event",
                "created": "2021-04-10T05:35:43.069Z",
                "module": "sysmon",
                "action": "Network connection detected (rule: NetworkConnect)",
                "category": ["network"],
                "type": ["connection", "start", "protocol"],
            },
            "user": {"domain": "NT AUTHORITY", "name": "SYSTEM"},
            "network": {
                "community_id": "1:ZXhhbXBsZQ==",
                "protocol": "-",
                "transport": "udp",
                "type": "ipv4",
                "direction": "egress",
            },
            "tags": ["beats_input_codec_plain_applied"],
        }
    ],
    100,
    None,
)


def test_stixshifter_translate():
    query_id = "8df266aa-2901-4a94-ace9-a4403e310fa1"
    check_module_availability(CONNECTOR_NAME)

    input_queue = Queue()
    output_queue = Queue()

    with multiproc.translate(
        CONNECTOR_NAME,
        {"id": "identity--" + query_id, "name": CONNECTOR_NAME},
        {},
        None,
        False,
        input_queue,
        output_queue,
        1,
    ) as translators:

        input_queue.put(SAMPLE_RESULT)
        input_queue.put(STOP_SIGN)

        for result in multiproc.read_translated_results(output_queue, 1):
            id_object = result["objects"][0]
            assert id_object["id"] == "identity--" + query_id
            assert id_object["name"] == CONNECTOR_NAME

    for translator in translators:
        assert translator.is_alive() == False


def test_stixshifter_translate_with_bundle_writing_to_disk(tmpdir):
    query_id = "8df266aa-2901-4a94-ace9-a4403e310fa1"
    check_module_availability(CONNECTOR_NAME)
    cache_bundle_path_prefix = str(tmpdir.join("test"))
    offset_str = str(SAMPLE_RESULT.offset).zfill(32)
    cache_bundle_path = cache_bundle_path_prefix + f"_{offset_str}.json"

    input_queue = Queue()
    output_queue = Queue()

    with multiproc.translate(
        CONNECTOR_NAME,
        {"id": "identity--" + query_id, "name": CONNECTOR_NAME},
        {},
        cache_bundle_path_prefix,
        False,
        input_queue,
        output_queue,
        1,
    ) as translators:

        input_queue.put(SAMPLE_RESULT)
        input_queue.put(STOP_SIGN)

        for result in multiproc.read_translated_results(output_queue, 1):
            pass

        with open(cache_bundle_path, "r") as bundle_fp:
            bundle = json.load(bundle_fp)
            id_object = bundle["objects"][0]
            assert id_object["id"] == "identity--" + query_id
            assert id_object["name"] == CONNECTOR_NAME

    for translator in translators:
        assert translator.is_alive() == False


def test_fast_translate():
    query_id = "8df266aa-2901-4a94-ace9-a4403e310fa1"
    check_module_availability(CONNECTOR_NAME)

    input_queue = Queue()
    output_queue = Queue()

    with multiproc.translate(
        CONNECTOR_NAME,
        {"id": "identity--" + query_id, "name": CONNECTOR_NAME},
        {},
        None,
        True,
        input_queue,
        output_queue,
        1,
    ) as translators:

        input_queue.put(SAMPLE_RESULT)
        input_queue.put(STOP_SIGN)

        for result in multiproc.read_translated_results(output_queue, 1):
            assert isinstance(result, pandas.DataFrame)
            assert result.empty == False

    for translator in translators:
        assert translator.is_alive() == False


@pytest.mark.skip(reason="kestrel v1.7.1 released with issue #370 unfixed")
def test_stixshifter_fast_translate_with_parquet_writing_to_disk(tmpdir):
    query_id = "8df266aa-2901-4a94-ace9-a4403e310fa1"
    check_module_availability(CONNECTOR_NAME)
    cache_parquet_path_prefix = str(tmpdir.join("test"))
    offset_str = str(SAMPLE_RESULT.offset).zfill(32)
    cache_parquet_path = cache_parquet_path_prefix + f"_{offset_str}.parquet"

    input_queue = Queue()
    output_queue = Queue()

    with multiproc.translate(
        CONNECTOR_NAME,
        {"id": "identity--" + query_id, "name": CONNECTOR_NAME},
        {},
        cache_parquet_path_prefix,
        True,
        input_queue,
        output_queue,
        1,
    ) as translators:

        input_queue.put(SAMPLE_RESULT)
        input_queue.put(STOP_SIGN)

        for result in multiproc.read_translated_results(output_queue, 1):
            pass

        df = pandas.read_parquet(cache_parquet_path)

    for translator in translators:
        assert translator.is_alive() == False
