import json
from copy import deepcopy
from multiprocessing import Queue
from kestrel.utils import mask_value_in_nested_dict
from kestrel_datasource_stixshifter.config import (
    set_stixshifter_logging_level,
    get_datasource_from_profiles,
    load_options,
    load_profiles,
)
from kestrel_datasource_stixshifter.worker import STOP_SIGN
from kestrel_datasource_stixshifter.query import translate_query
from kestrel_datasource_stixshifter.worker.transmitter import Transmitter
from stix_shifter.stix_transmission import stix_transmission


class Diagnosis:
    def __init__(self, datasource_name):
        self.datasource_name = datasource_name
        self.profiles = load_profiles()
        self.kestrel_options = load_options()
        (
            self.connector_name,
            self.connection_dict,
            self.configuration_dict,
            self.retrieval_batch_size,
            self.cool_down_after_transmission,
        ) = get_datasource_from_profiles(datasource_name, self.profiles)
        self.if_fast_translation = (
            self.connector_name in self.kestrel_options["fast_translate"]
        )
        set_stixshifter_logging_level()

    def diagnose_config(self):
        print()
        print()
        print()
        print("## Diagnose: config verification")

        configuration_dict_masked = mask_value_in_nested_dict(
            deepcopy(self.configuration_dict)
        )

        print()
        print("#### Kestrel specific config")
        print(f"retrieval batch size: {self.retrieval_batch_size}")
        print(f"cool down after transmission: {self.cool_down_after_transmission}")
        print(f"enable fast translation: {self.if_fast_translation}")

        print()
        print("#### Config to be passed to stix-shifter")
        print(f"connector name: {self.connector_name}")
        print(
            "connection object [ref: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#connection]:"
        )
        print(json.dumps(self.connection_dict, indent=4))
        print(
            "configuration object [ref: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/OVERVIEW.md#configuration]:"
        )
        print(json.dumps(configuration_dict_masked, indent=4))

    def diagnose_ping(self):
        print()
        print()
        print()
        print("## Diagnose: stix-shifter to data source connection (network, auth)")

        transmission = stix_transmission.StixTransmission(
            self.connector_name,
            self.connection_dict,
            self.configuration_dict,
        )

        result = transmission.ping()

        print()
        print("#### Results from stixshifter transmission.ping()")
        print(json.dumps(result, indent=4))

    def diagnose_translate_query(self, stix_pattern, quiet=False):
        if not quiet:
            print()
            print()
            print()
            print("## Diagnose: stix-shifter query translation")

        dsl = translate_query(
            self.connector_name,
            {},
            stix_pattern,
            self.connection_dict,
        )

        if not quiet:
            print()
            print("#### Input pattern")
            print(stix_pattern)
            print()
            print("#### Output data source native query")
            print(json.dumps(dsl, indent=4))

        return dsl

    def diagnose_run_query_and_retrieval_result(self, stix_patterns, max_batch_cnt):
        print()
        print()
        print()
        print(f"## Diagnose: stix-shifter query execution: <={max_batch_cnt} batch(s)")

        result_queue = Queue()
        result_counts = []

        for pattern in stix_patterns:
            for query in self.diagnose_translate_query(pattern, True)["queries"]:
                transmitter = Transmitter(
                    self.connector_name,
                    self.connection_dict,
                    self.configuration_dict,
                    self.retrieval_batch_size,
                    self.cool_down_after_transmission,
                    query,
                    result_queue,
                    max_batch_cnt * self.retrieval_batch_size,
                )

                transmitter.run()
                result_queue.put(STOP_SIGN)

                print()
                print("#### data retrieval results:")
                for packet in iter(result_queue.get, STOP_SIGN):
                    if packet.success:
                        cnt = len(packet.data)
                        result_counts.append(cnt)
                        print(f"one batch retrieved: {cnt} entries")
                    else:
                        print(packet.log)

                if result_counts:
                    break
                else:
                    print(f"no result matched for query: {query}, go next query")

            if result_counts:
                break
            else:
                print(f"no result matched for pattern: {pattern}, go next pattern")

        return result_counts
