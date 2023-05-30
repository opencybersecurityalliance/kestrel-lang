"""The STIX-shifter data source package provides access to data sources via
`stix-shifter`_.

The STIX-shifter interface connects to multiple data sources. Users need to
provide one *profile* per data source. The profile name (case insensitive) will
be used in the ``FROM`` clause of the Kestrel ``GET`` command, e.g., ``newvar =
GET entity-type FROM stixshifter://profilename WHERE ...``. Kestrel runtime
will load profiles from 3 places (the later will override the former):

#. STIX-shifter interface config file (only when a Kestrel session starts):

    Create the STIX-shifter interface config file (YAML):

    - Default path: ``~/.config/kestrel/stixshifter.yaml``.

    - A customized path specified in the environment variable ``KESTREL_STIXSHIFTER_CONFIG``.

    Example of STIX-shifter interface config file containing profiles
    (note that the ``options`` section is not required):

    .. code-block:: yaml

        profiles:
            host101:
                connector: elastic_ecs
                connection:
                    host: elastic.securitylog.company.com
                    port: 9200
                    selfSignedCert: false # this means do NOT check cert
                    indices: host101
                    options:  # use any of this section when needed
                        retrieval_batch_size: 10000  # set to 10000 to match default Elasticsearch page size; Kestrel default across connectors: 2000
                        single_batch_timeout: 120  # increase it if hit 60 seconds (Kestrel default) timeout error for each batch of retrieval
                        dialects:  # more info: https://github.com/opencybersecurityalliance/stix-shifter/tree/develop/stix_shifter_modules/elastic_ecs#dialects
                          - beats  # need it if the index is created by Filebeat/Winlogbeat/*beat
                config:
                    auth:
                        id: VuaCfGcBCdbkQm-e5aOx
                        api_key: ui2lp2axTNmsyakw9tvNnw
            host102:
                connector: qradar
                connection:
                    host: qradar.securitylog.company.com
                    port: 443
                config:
                    auth:
                        SEC: 123e4567-e89b-12d3-a456-426614174000
            host103:
                connector: cbcloud
                connection:
                    host: cbcloud.securitylog.company.com
                    port: 443
                config:
                    auth:
                        org-key: D5DQRHQP
                        token: HT8EMI32DSIMAQ7DJM
        options:  # this section is not required
            fast_translate:  # use firepit-native translation (Dataframe as vessel) instead of stix-shifter result translation (JSON as vessel) for the following connectors
                - qradar
                - elastic_ecs

    Full specifications for data source profile sections/fields:

    - Connector-specific fields: in `stix-shifter`_, go to ``stix_shifter_modules/connector_name/configuration`` like `elastic_ecs config`_.

    - General fields shared across connectors: in `stix-shifter`_, go to `stix_shifter_modules/lang_en.json`_.

#. environment variables (only when a Kestrel session starts):

    Three environment variables are required for each profile:

    - ``STIXSHIFTER_PROFILENAME_CONNECTOR``: the STIX-shifter connector name,
      e.g., ``elastic_ecs``.

    - ``STIXSHIFTER_PROFILENAME_CONNECTION``: the STIX-shifter `connection
      <https://github.com/opencybersecurityalliance/stix-shifter/blob/master/OVERVIEW.md#connection>`_
      object in JSON string.

    - ``STIXSHIFTER_PROFILENAME_CONFIG``: the STIX-shifter `configuration
      <https://github.com/opencybersecurityalliance/stix-shifter/blob/master/OVERVIEW.md#configuration>`_
      object in JSON string.

    Example of environment variables for a profile:

    .. code-block:: console

        $ export STIXSHIFTER_HOST101_CONNECTOR=elastic_ecs
        $ export STIXSHIFTER_HOST101_CONNECTION='{"host":"elastic.securitylog.company.com", "port":9200, "indices":"host101"}'
        $ export STIXSHIFTER_HOST101_CONFIG='{"auth":{"id":"VuaCfGcBCdbkQm-e5aOx", "api_key":"ui2lp2axTNmsyakw9tvNnw"}}'

#. any in-session edit through the ``CONFIG`` command.

If you launch Kestrel in debug mode, STIX-shifter debug mode is still not
enabled by default. To record debug level logs of STIX-shifter, create
environment variable ``KESTREL_STIXSHIFTER_DEBUG`` with any value.

.. _STIX-shifter: https://github.com/opencybersecurityalliance/stix-shifter
.. _elastic_ecs config: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/stix_shifter_modules/elastic_ecs/configuration/lang_en.json
.. _stix_shifter_modules/lang_en.json: https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/stix_shifter_modules/lang_en.json

"""

import asyncio
import json
import copy
import logging


from stix_shifter.stix_translation import stix_translation
from stix_shifter.stix_transmission import stix_transmission
from stix_shifter_utils.stix_translation.src.utils.transformer_utils import (
    get_module_transformers,
)

from firepit.aio import asyncwrapper
from firepit.aio.ingest import ingest, translate
from kestrel.utils import mkdtemp
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromStore
from kestrel.exceptions import DataSourceError, DataSourceManagerInternalError
from kestrel_datasource_stixshifter.connector import check_module_availability
from kestrel_datasource_stixshifter.config import (
    get_datasource_from_profiles,
    load_options,
    load_profiles,
    set_stixshifter_logging_level,
)

_logger = logging.getLogger(__name__)


class StixShifterInterface(AbstractDataSourceInterface):
    @staticmethod
    def schemes():
        """STIX-shifter data source interface only supports ``stixshifter://`` scheme."""
        return ["stixshifter"]

    @staticmethod
    def list_data_sources(config):
        """Get configured data sources from environment variable profiles."""

        # CONFIG command is not supported
        # profiles will be updated according to YAML file and env var
        config["profiles"] = load_profiles()

        data_sources = list(config["profiles"].keys())
        data_sources.sort()
        return data_sources

    @staticmethod
    async def query(uri, pattern, session_id, config, store=None):
        """Query a stixshifter data source."""

        # CONFIG command is not supported
        # profiles will be updated according to YAML file and env var
        config["profiles"] = load_profiles()

        config["options"] = load_options()
        _logger.debug(
            "fast_translate enabled for: %s", config["options"]["fast_translate"]
        )

        scheme, _, profile = uri.rpartition("://")
        profiles = profile.split(",")
        if scheme != "stixshifter":
            raise DataSourceManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        set_stixshifter_logging_level()

        ingestdir = mkdtemp()
        query_id = ingestdir.name
        # bundles = []
        dict_bundles = []
        _logger.debug(f"prepare query with ID: {query_id}")
        for i, profile in enumerate(profiles):
            # STIX-shifter will alter the config objects, thus making them not reusable.
            # So only give STIX-shifter a copy of the configs.
            # Check `modernize` functions in the `stix_shifter_utils` for details.
            (
                connector_name,
                connection_dict,
                configuration_dict,
                retrieval_batch_size,
            ) = map(
                copy.deepcopy, get_datasource_from_profiles(profile, config["profiles"])
            )

            check_module_availability(connector_name)

            data_path_striped = "".join(filter(str.isalnum, profile))

            ingest_stixbundle_filepath = make_ingest_stixbundle_filepath(
                ingestdir, data_path_striped, i
            )

            query_metadata = {
                "id": "identity--" + query_id,
                "name": connector_name,
                "type": "identity",
            }

            translation = stix_translation.StixTranslation()
            transmission = stix_transmission.StixTransmission(
                connector_name, connection_dict, configuration_dict
            )

            translation_options = copy.deepcopy(connection_dict.get("options", {}))
            dsl = await translation.translate_async(
                connector_name, "query", query_metadata, pattern, translation_options
            )

            if "error" in dsl:
                raise DataSourceError(
                    f"STIX-shifter translation from STIX to native query failed with message: {dsl['error']}"
                )

            _logger.debug(f"STIX pattern to query: {pattern}")
            _logger.debug(f"translate results: {dsl}")

            # query results should be put together; when translated to STIX, the relation between them will remain
            transmission_queue = asyncio.Queue()

            # schedule consumers
            consumers = []
            consumer_count = config["options"]["async_translation_workers_count"]
            if connector_name in config["options"]["fast_translate"]:
                for _ in range(consumer_count):
                    consumer = asyncio.create_task(
                        fast_translate_ingest_consume(
                            transmission_queue,
                            connector_name,
                            translation,
                            translation_options,
                            query_metadata,
                            query_id,
                            store,
                        )
                    )
                    consumers.append(consumer)
            else:
                for _ in range(consumer_count):
                    consumer = asyncio.create_task(
                        translation_ingest_consume(
                            transmission_queue,
                            translation,
                            connector_name,
                            query_metadata,
                            translation_options,
                            ingest_stixbundle_filepath,
                            query_id,
                            store,
                        )
                    )
                    consumers.append(consumer)

            batch_index = 0
            for query in dsl["queries"]:
                search_meta_result = await transmission.query_async(query)
                if search_meta_result["success"]:
                    search_id = search_meta_result["search_id"]

                    await transmission_complete(transmission, search_id)

                    # run the producer and wait for completion
                    batch_index = await transmission_produce(
                        connector_name,
                        transmission_queue,
                        transmission,
                        search_id,
                        retrieval_batch_size,
                        batch_index,
                    )

                else:
                    stix_shifter_error_msg = (
                        search_meta_result["error"]
                        if "error" in search_meta_result
                        else "details not avaliable"
                    )
                    raise DataSourceError(
                        f"STIX-shifter transmission.query() failed with message: {stix_shifter_error_msg}"
                    )

            # _logger.debug("transmission succeeded, start translate back to STIX")

            # wait until the consumer has processed all items
            await transmission_queue.join()

            # the consumers are still waiting for an item, cancel them
            for consumer in consumers:
                consumer.cancel()

            # wait until all worker tasks are cancelled
            responses = await asyncio.gather(*consumers, return_exceptions=True)
            for response in responses:
                if not isinstance(response, asyncio.CancelledError):
                    raise response

        return ReturnFromStore(query_id)
        # return ReturnFromFile(query_id, bundles)


def make_ingest_stixbundle_filepath(ingestdir, data_path_striped, profile_index):
    def ingest_stixbundle_filepath(batch_index):
        ingestbatchfile = (
            ingestdir / f"{profile_index}_{batch_index}_{data_path_striped}.json"
        )
        return ingestbatchfile

    return ingest_stixbundle_filepath


async def transmission_complete(transmission, search_id):
    status = None
    while True:
        status = await transmission.status_async(search_id)
        if not status["success"]:
            stix_shifter_error_msg = (
                status["error"] if "error" in status else "details not avaliable"
            )
            raise DataSourceError(
                f"STIX-shifter transmission.status() failed with message: {stix_shifter_error_msg}"
            )
        elif status["progress"] < 100 and status["status"] == "RUNNING":
            await asyncio.sleep(1)
        else:
            break


async def transmission_produce(
    connector_name,
    transmission_queue,
    transmission,
    search_id,
    retrieval_batch_size,
    batch_index,
):
    result_retrieval_offset = 0
    has_remaining_results = True
    metadata = None
    is_retry_cycle = False
    while has_remaining_results:
        result_batch = await transmission.results_async(
            search_id, result_retrieval_offset, retrieval_batch_size, metadata
        )
        if result_batch["success"]:
            new_entries = result_batch["data"]
            if new_entries:
                result_batch["batch_index"] = batch_index
                await transmission_queue.put(result_batch)
                result_retrieval_offset += len(new_entries)
                batch_index += 1
            else:
                has_remaining_results = False
            if "metadata" in result_batch:
                metadata = result_batch["metadata"]
            is_retry_cycle = False
        else:
            stix_shifter_error_msg = (
                result_batch["error"]
                if "error" in result_batch
                else "details not avaliable"
            )
            if (
                stix_shifter_error_msg.startswith(
                    f"{connector_name} connector error => server timeout_error"
                )
                and not is_retry_cycle
            ):
                # mitigate https://github.com/opencybersecurityalliance/stix-shifter/issues/1493
                # only give it one retry to mitigate high CPU occupation
                # otherwise, it could be a real server connection issue
                # /stix_shifter_utils/stix_transmission/utils/RestApiClientAsync.py
                _logger.info(
                    f"busy CPU; hit stix-shifter transmission aiohttp connection timeout; retry"
                )
                is_retry_cycle = True
            else:
                raise DataSourceError(
                    f"STIX-shifter transmission.results() failed with message: {stix_shifter_error_msg}"
                )
    return batch_index


async def translation_ingest_consume(
    transmission_queue,
    translation,
    connector_name,
    query_metadata,
    translation_options,
    ingest_stixbundle_filepath,
    query_id,
    store,
):
    while True:
        # wait for an item from the producer
        result_batch = await transmission_queue.get()

        stixbundle = await translation.translate_async(
            connector_name,
            "results",
            query_metadata,
            result_batch["data"],
            translation_options,
        )

        if "error" in stixbundle:
            transmission_queue.task_done()
            raise DataSourceError(
                f"STIX-shifter translation results to STIX failed with message: {stixbundle['error']}"
            )

        await asyncwrapper.SyncWrapper(store=store).cache(query_id, stixbundle)

        if _logger.isEnabledFor(logging.DEBUG):
            ingestbatchfile = ingest_stixbundle_filepath(
                str(result_batch["batch_index"])
            )
            _logger.debug(f"dumping STIX bundles into file: {ingestbatchfile}")
            with ingestbatchfile.open("w") as ingest_fp:
                json.dump(stixbundle, ingest_fp, indent=4)

        # Notify the queue that the item has been processed
        transmission_queue.task_done()


async def fast_translate_ingest_consume(
    transmission_queue,
    connector_name,
    translation,
    translation_options,
    identity,
    query_id,
    store,
):
    while True:
        # wait for an item from the producer
        result_batch = await transmission_queue.get()
        await fast_translate(
            connector_name,
            result_batch["data"],
            translation,
            translation_options,
            identity,
            query_id,
            store,
        )
        # Notify the queue that the item has been processed
        transmission_queue.task_done()


async def fast_translate(
    connector_name,
    connector_results,
    translation,
    translation_options,
    identity,
    query_id,
    store,
):
    # Use the alternate, faster DataFrame-based translation (in firepit)
    _logger.debug("Using fast translation for connector %s", connector_name)
    transformers = get_module_transformers(connector_name)
    mapping = await translation.translate_async(
        connector_name,
        stix_translation.MAPPING,
        None,
        None,
        translation_options,
    )

    if "error" in mapping:
        raise DataSourceError(
            f"STIX-shifter mapping failed with message: {mapping['error']}"
        )

    df = translate(mapping["to_stix_map"], transformers, connector_results, identity)

    identity_obj = {
        "identity_class": "system",
        "created": None,
        "modified": None,
    }  # These are required by STIX but not needed here
    identity_obj.update(identity)

    await ingest(
        asyncwrapper.SyncWrapper(store=store),
        identity_obj,
        df,
        query_id,
    )
