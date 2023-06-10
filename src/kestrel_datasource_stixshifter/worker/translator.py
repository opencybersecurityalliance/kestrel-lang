import json
import logging
from multiprocessing import Process, Queue
from typeguard import typechecked

from kestrel.exceptions import DataSourceError
from stix_shifter.stix_translation import stix_translation
from stix_shifter_utils.stix_translation.src.utils.transformer_utils import (
    get_module_transformers,
)
from firepit.aio.ingest import translate

from kestrel_datasource_stixshifter.worker import STOP_SIGN


_logger = logging.getLogger(__name__)


@typechecked
class Translator(Process):
    def __init__(
        self,
        connector_name: str,
        observation_metadata: dict,
        translation_options: dict,
        cache_bundle_path_prefix: str,
        is_fast_translation: bool,
        input_queue: Queue,
        output_queue: Queue,
    ):
        super().__init__()

        self.connector_name = connector_name
        self.observation_metadata = observation_metadata
        self.translation_options = translation_options
        self.cache_bundle_path_prefix = cache_bundle_path_prefix
        self.is_fast_translation = is_fast_translation
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        _logger.debug("translator worker starts")
        translation = stix_translation.StixTranslation()

        for input_batch in iter(self.input_queue.get, STOP_SIGN):
            if self.is_fast_translation:
                _logger.debug("fast translation task assigned to translator worker")
                transformers = get_module_transformers(self.connector_name)

                mapping = translation.translate(
                    self.connector_name,
                    stix_translation.MAPPING,
                    None,
                    None,
                    self.translation_options,
                )

                if "error" in mapping:
                    raise DataSourceError(
                        f"STIX-shifter mapping failed with message: {mapping['error']}"
                    )

                dataframe = translate(
                    mapping["to_stix_map"],
                    transformers,
                    input_batch["data"],
                    self.observation_metadata,
                )

                self.output_queue.put((dataframe,))
                _logger.debug("fast translation done and results in queue")

            else:
                _logger.debug("JSON translation task assigned to translator worker")
                stixbundle = translation.translate(
                    self.connector_name,
                    "results",
                    self.observation_metadata,
                    input_batch["data"],
                    self.translation_options,
                )

                if "error" in stixbundle:
                    raise DataSourceError(
                        "STIX-shifter translation results to STIX failed"
                        f" with message: {stixbundle['error']}"
                    )

                if _logger.isEnabledFor(logging.DEBUG):
                    debug_stixbundle_filepath = self.get_cache_bundle_path(
                        input_batch["offset"]
                    )
                    _logger.debug(
                        f"dumping STIX bundles into file: {debug_stixbundle_filepath}"
                    )
                    with debug_stixbundle_filepath.open("w") as ingest_fp:
                        json.dump(stixbundle, ingest_fp, indent=4)

                self.output_queue.put((stixbundle,))
                _logger.debug("JSON translation done and results in queue")

        self.output_queue.put(STOP_SIGN)

        def get_cache_bundle_path(self, offset):
            offset = str(offset).zfill(32)
            return f"{self.cache_bundle_path_prefix}_{offset}.json"
