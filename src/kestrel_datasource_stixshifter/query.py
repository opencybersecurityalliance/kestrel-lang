import logging
import copy
from pandas import DataFrame
from multiprocessing import Queue

from kestrel.datasource import ReturnFromStore
from kestrel.utils import mkdtemp
from kestrel.exceptions import DataSourceError, DataSourceManagerInternalError
from kestrel_datasource_stixshifter.connector import check_module_availability
from kestrel_datasource_stixshifter.worker import STOP_SIGN
from kestrel_datasource_stixshifter.worker.transmitter import TransmitterPool
from kestrel_datasource_stixshifter.worker.translator import Translator
from kestrel_datasource_stixshifter.config import (
    get_datasource_from_profiles,
    load_options,
    load_profiles,
    set_stixshifter_logging_level,
)

from firepit.aio import asyncwrapper
from firepit.aio.ingest import ingest

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

        data_path_striped = "".join(filter(str.isalnum, profile))

        gen_debug_stixbundle_filepath = make_debug_stixbundle_filepath(
            cache_dir, data_path_striped
        )

        observation_metadata = {
            "id": "identity--" + query_id,
            "name": connector_name,
            "type": "identity",
        }

        translation_options = copy.deepcopy(connection_dict.get("options", {}))

        translation = stix_translation.StixTranslation()

        _logger.debug(f"STIX pattern to query: {pattern}")

        dsl = translation.translate(
            connector_name, "query", observation_metadata, pattern, translation_options
        )

        if "error" in dsl:
            raise DataSourceError(
                "STIX-shifter translation from STIX"
                " to native query failed"
                f" with message: {dsl['error']}"
            )

        _logger.debug(f"translate results: {dsl}")

        raw_records_queue = Queue()
        translated_data_queue = Queue()

        translators_count = config["options"]["translation_workers_count"]
        _logger.debug(f"{translators_count} translation workers to be started")

        is_fast_translation = connector_name in config["options"]["fast_translate"]
        _logger.debug(f"fast translation enabled: {is_fast_translation}")

        translators = [
            Translator(
                connector_name,
                observation_metadata,
                translation_options,
                gen_debug_stixbundle_filepath,
                is_fast_translation,
                raw_records_queue,
                translated_data_queue,
            )
            for _ in range(translators_count)
        ]

        for translator in translators:
            translator.start()

        transmitter_pool = TransmitterPool(
            connector_name,
            connection_dict,
            configuration_dict,
            retrieval_batch_size,
            translators_count,
            dsl["queries"],
            raw_records_queue,
        )

        transmitter_pool.start()

        for _ in range(translators_count):
            for translated_data in iter(translated_data_queue.get, STOP_SIGN):
                if isinstance(translated_data, DataFrame):
                    # fast translation result
                    asyncio.run(
                        ingest(
                            asyncwrapper.SyncWrapper(store=store),
                            observation_metadata,
                            translated_data,
                            query_id,
                        )
                    )
                else:
                    # STIX bundle (normal stix-shifter translation result)
                    store.cache(query_id, translated_data)

        # all transmitters should already finished
        if transmitter_pool.is_alive():
            raise DataSourceManagerInternalError(
                f"one or more transmitters do not terminate in interface {__package__}"
            )

        # all translators should already finished
        for translator in translators:
            if translator.is_alive():
                raise DataSourceManagerInternalError(
                    f"one or more translators do not terminate in interface {__package__}"
                )

    return ReturnFromStore(query_id)


def make_debug_stixbundle_filepath(cache_dir, data_path_striped):
    def debug_stixbundle_filepath(offset):
        offset = str(offset).zfill(32)
        bundle = cache_dir / f"{data_path_striped}_{offset}.json"
        return bundle

    return debug_stixbundle_filepath
