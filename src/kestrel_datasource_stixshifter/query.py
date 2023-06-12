import logging
import asyncio
import copy
from typing import Union
from typeguard import typechecked
from pandas import DataFrame
from multiprocessing import Queue

from kestrel.datasource import ReturnFromStore
from kestrel.utils import mkdtemp
from kestrel.exceptions import DataSourceError, DataSourceManagerInternalError
from kestrel_datasource_stixshifter.connector import check_module_availability
from kestrel_datasource_stixshifter.worker import STOP_SIGN
from kestrel_datasource_stixshifter import multiproc
from kestrel_datasource_stixshifter.config import (
    get_datasource_from_profiles,
    load_options,
    load_profiles,
    set_stixshifter_logging_level,
)

from firepit.sqlstorage import SqlStorage
import firepit.aio.ingest
import firepit.aio.asyncwrapper

from stix_shifter.stix_translation import stix_translation

# TODO: better solution to avoid using nest_asyncio for run_until_complete()
#       maybe putting entire Kestrel in async mode
import nest_asyncio

nest_asyncio.apply()


_logger = logging.getLogger(__name__)


def query_datasource(uri, pattern, session_id, config, store):
    # CONFIG command is not supported
    # profiles will be updated according to YAML file and env var
    config["profiles"] = load_profiles()

    config["options"] = load_options()

    _logger.debug(
        "fast_translate enabled for: " f"{config['options']['fast_translate']}"
    )

    scheme, _, profile = uri.rpartition("://")
    profiles = profile.split(",")
    if scheme != "stixshifter":
        raise DataSourceManagerInternalError(
            f"interface {__package__} should not process scheme {scheme}"
        )

    set_stixshifter_logging_level()

    # cache_dir will be empty if not in debug mode
    # however, the directory guarantees unique and non-exist query ID
    # so it always needs to be created
    cache_dir = mkdtemp()
    query_id = cache_dir.name

    _logger.debug(f"prepare query with ID: {query_id}")

    for profile in profiles:
        _logger.debug(f"entering stix-shifter data source: {profile}")

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

        if _logger.isEnabledFor(logging.DEBUG):
            data_path_striped = "".join(filter(str.isalnum, profile))
            cache_data_path_prefix = str(cache_dir / data_path_striped)
        else:
            cache_data_path_prefix = None

        observation_metadata = gen_observation_metadata(connector_name, query_id)

        dsl = translate_query(
            connector_name, observation_metadata, pattern, connection_dict
        )

        raw_records_queue = Queue()
        translated_data_queue = Queue()

        with multiproc.translate(
            connector_name,
            observation_metadata,
            connection_dict.get("options", {}),
            cache_data_path_prefix,
            connector_name in config["options"]["fast_translate"],
            raw_records_queue,
            translated_data_queue,
            config["options"]["translation_workers_count"],
        ):
            with multiproc.transmit(
                connector_name,
                connection_dict,
                configuration_dict,
                retrieval_batch_size,
                config["options"]["translation_workers_count"],
                dsl["queries"],
                raw_records_queue,
            ):
                for _ in range(config["options"]["translation_workers_count"]):
                    for packet in iter(translated_data_queue.get, STOP_SIGN):
                        if packet.success:
                            ingest(packet.data, observation_metadata, query_id, store)
                        else:
                            process_log_msg(packet)

    return ReturnFromStore(query_id)


@typechecked
def gen_observation_metadata(connector_name: str, query_id: str):
    return {
        "id": "identity--" + query_id,
        "name": connector_name,
        "type": "identity",
    }


@typechecked
def translate_query(
    connector_name: str,
    observation_metadata: dict,
    pattern: str,
    connection_dict: dict,
):
    translation = stix_translation.StixTranslation()
    translation_options = copy.deepcopy(connection_dict.get("options", {}))

    _logger.debug(f"STIX pattern to query: {pattern}")

    dsl = translation.translate(
        connector_name, "query", observation_metadata, pattern, translation_options
    )

    _logger.debug(f"translate results: {dsl}")

    if "error" in dsl:
        raise DataSourceError(
            "STIX-shifter translation from STIX"
            " to native query failed"
            f" with message: {dsl['error']}"
        )

    return dsl


@typechecked
def ingest(
    result: Union[dict, DataFrame],
    observation_metadata: dict,
    query_id: str,
    store: SqlStorage,
):
    _logger.debug("ingestion of a batch/page starts")
    if isinstance(result, DataFrame):
        # fast translation result in DataFrame
        asyncio.run(
            firepit.aio.ingest.ingest(
                firepit.aio.asyncwrapper.SyncWrapper(store=store),
                observation_metadata,
                result,
                query_id,
            )
        )
    else:
        # STIX bundle (normal stix-shifter translation result)
        store.cache(query_id, result)
    _logger.debug("ingestion of a batch/page ends")


def process_log_msg(packet):
    log_msg = f"[worker: {packet.worker}] {packet.log.log}"
    if packet.log.level == logging.ERROR:
        _logger.debug(log_msg)
        raise DataSourceError(log_msg)
    else:
        if packet.log.level == logging.WARN:
            _logger.warn(log_msg)
        elif packet.log.level == logging.INFO:
            _logger.info(log_msg)
        else:  #  all others as debug logs
            _logger.debug(log_msg)
