import time
from multiprocessing import Process

from kestrel.exceptions import DataSourceError
from stix_shifter.stix_transmission import stix_transmission
from kestrel_datasource_stixshifter.worker import STOP_SIGN


class TransmitterPool(Process):
    def __init__(
        self,
        connector_name,
        connection_dict,
        configuration_dict,
        retrieval_batch_size,
        number_of_translators,
        queries,
        output_queue,
    ):
        super().__init__()

        self.connector_name = connector_name
        self.connection_dict = connection_dict
        self.configuration_dict = configuration_dict
        self.retrieval_batch_size = retrieval_batch_size
        self.number_of_translators = number_of_translators
        self.queries = queries
        self.queue = output_queue

    def run(self):
        transmitters = [
            Transmitter(
                self.connector_name,
                self.connection_dict,
                self.configuration_dict,
                self.retrieval_batch_size,
                query,
                self.queue,
            )
            for query in self.queries
        ]
        for transmitter in transmitters:
            transmitter.start()
        for transmitter in transmitters:
            transmitter.join()
        for _ in range(self.number_of_translators):
            self.queue.put(STOP_SIGN)


class Transmitter(Process):
    def __init__(
        self,
        connector_name,
        connection_dict,
        configuration_dict,
        retrieval_batch_size,
        query,
        output_queue,
    ):
        super().__init__()

        self.connector_name = connector_name
        self.connection_dict = connection_dict
        self.configuration_dict = configuration_dict
        self.retrieval_batch_size = retrieval_batch_size
        self.query = query
        self.queue = output_queue

    def run(self):
        self.transmission = stix_transmission.StixTransmission(
            self.connector_name,
            self.connection_dict,
            self.configuration_dict,
        )
        search_meta_result = self.transmission.query(self.query)
        if search_meta_result["success"]:
            self.search_id = search_meta_result["search_id"]
            self.wait_datasource_search()
            self.retrieve_data()
        else:
            stix_shifter_error_msg = (
                search_meta_result["error"]
                if "error" in search_meta_result
                else "details not avaliable"
            )
            raise DataSourceError(
                f"STIX-shifter transmission.query() failed with message: {stix_shifter_error_msg}"
            )

    def wait_datasource_search(self):
        # stix-shifter will not give "KINIT" status, but just "RUNNING"
        status = {"progress": 0, "status": "KINIT"}

        while status["progress"] < 100 and status["status"] in ("KINIT", "RUNNING"):
            if status["status"] == "RUNNING":
                time.sleep(1)
            status = self.transmission.status(self.search_id)
            if not status["success"]:
                stix_shifter_error_msg = (
                    status["error"] if "error" in status else "details not avaliable"
                )
                raise DataSourceError(
                    "STIX-shifter transmission.status()"
                    f" failed with message: {stix_shifter_error_msg}"
                )

    def retrieve_data(self):
        result_retrieval_offset = 0
        has_remaining_results = True
        metadata = None

        while has_remaining_results:
            result_batch = self.transmission.results(
                self.search_id,
                result_retrieval_offset,
                self.retrieval_batch_size,
                metadata,
            )

            if result_batch["success"]:
                new_entries = result_batch["data"]

                if new_entries:
                    # decorate result
                    result_batch["offset"] = result_retrieval_offset

                    # put results to output queue
                    self.queue.put(result_batch)

                    # prepare for next round retrieval
                    result_retrieval_offset += len(new_entries)
                    if "metadata" in result_batch:
                        metadata = result_batch["metadata"]

                else:
                    has_remaining_results = False

            else:
                stix_shifter_error_msg = (
                    result_batch["error"]
                    if "error" in result_batch
                    else "details not avaliable"
                )
                raise DataSourceError(
                    "STIX-shifter transmission.results() failed"
                    f" with message: {stix_shifter_error_msg}"
                )
