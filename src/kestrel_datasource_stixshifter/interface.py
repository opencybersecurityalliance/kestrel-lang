"""STIX Shifter data source package provides access to data sources via
stix-shifter.

Before use, need to install the target stix-shifter connector packages such as
``stix-shifter-modules-carbonblack``.

The STIX Shifter interface can reach multiple data sources. The user needs to
setup one *profile* per data source. The profile name will be used in the
``FROM`` clause of the Kestrel ``GET`` command, e.g., ``newvar = GET entity-type
FROM stixshifter://profilename WHERE ...``. Kestrel runtime will load profiles
from (the later will override the former):

#. stix-shifter interface config file (only at first run):

    - First check environment variable ``KESTREL_STIXSHIFTER_CONFIG`` to find a file path.
    - Then load either the file from the first step or the default place ``~/.config/kestrel/stixshifter.yaml``.

    The YAML file shoud has a root level key ``profiles``.

#. environment variables (only at first run):

    - ``STIXSHIFTER_PROFILENAME_CONNECTOR``: the STIX Shifter connector name, e.g., ``elastic_ecs``.
    - ``STIXSHIFTER_PROFILENAME_CONNECTION``: the STIX Shifter `connection <https://github.com/opencybersecurityalliance/stix-shifter/blob/master/OVERVIEW.md#connection>`_ object in JSON string.
    - ``STIXSHIFTER_PROFILENAME_CONFIG``: the STIX Shifter `configuration <https://github.com/opencybersecurityalliance/stix-shifter/blob/master/OVERVIEW.md#configuration>`_ object in JSON string.

    Properties of profile name:

    - Not case sensitive, e.g., ``profileX`` in the Kestrel command will match
  ``STIXSHIFTER_PROFILEX_...`` in environment variables.
    - Cannot contain ``_``.

#. any in-session edit through the ``CONFIG`` command.

"""

import json
import time

from stix_shifter.stix_translation import stix_translation
from stix_shifter.stix_transmission import stix_transmission

from kestrel.utils import mkdtemp
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromFile
from kestrel.exceptions import DataSourceError, DataSourceManagerInternalError
from kestrel_datasource_stixshifter.config import RETRIEVAL_BATCH_SIZE, get_datasource_from_profiles, load_profiles

class StixShifterInterface(AbstractDataSourceInterface):

    @staticmethod
    def schemes():
        """STIX Shifter data source interface only supports ``stixshifter://`` scheme."""
        return ["stixshifter"]

    @staticmethod
    def list_data_sources(config):
        """Get configured data sources from environment variable profiles."""
        if not config:
            config["profiles"] = load_profiles()
        data_sources = list(config["profiles"].keys())
        data_sources.sort()
        return data_sources

    @staticmethod
    def query(uri, pattern, session_id, config):
        """Query a stixshifter data source."""
        scheme, _, profile = uri.rpartition("://")
        profiles = profile.split(",")

        if not config:
            config["profiles"] = load_profiles()

        if scheme != "stixshifter":
            raise DataSourceManagerInternalError(f"interface {__package__} should not process scheme {scheme}")

        ingestdir = mkdtemp()
        query_id = ingestdir.name
        bundles = []
        for i, profile in enumerate(profiles):
            (
                connector_name,
                connection_dict,
                configuration_dict,
            ) = get_datasource_from_profiles(profile, config["profiles"])

            data_path_striped = "".join(filter(str.isalnum, profile))
            ingestfile = ingestdir / f"{i}_{data_path_striped}.json"

            query_metadata = json.dumps(
                {"id": "identity--" + query_id, "name": connector_name}
            )

            translation = stix_translation.StixTranslation()
            transmission = stix_transmission.StixTransmission(
                connector_name, connection_dict, configuration_dict
            )

            dsl = translation.translate(
                connector_name, "query", query_metadata, pattern, {}
            )

            if "error" in dsl:
                raise DataSourceError(
                    f"STIX-shifter translation failed with message: {dsl['error']}"
                )

            # query results should be put together; when translated to STIX, the relation between them will remain
            connector_results = []
            for query in dsl["queries"]:
                search_meta_result = transmission.query(query)
                if search_meta_result["success"]:
                    search_id = search_meta_result["search_id"]
                    if transmission.is_async():
                        time.sleep(1)
                        status = transmission.status(search_id)
                        if status["success"]:
                            while (
                                status["progress"] < 100
                                and status["status"] == "RUNNING"
                            ):
                                status = transmission.status(search_id)
                        else:
                            stix_shifter_error_msg = (
                                status["error"]
                                if "error" in status
                                else "details not avaliable"
                            )
                            raise DataSourceError(
                                f"STIX-shifter transmission.status() failed with message: {stix_shifter_error_msg}"
                            )

                    result_retrieval_offset = 0
                    has_remaining_results = True
                    while has_remaining_results:
                        result_batch = transmission.results(
                            search_id, result_retrieval_offset, RETRIEVAL_BATCH_SIZE
                        )
                        if result_batch["success"]:
                            new_entries = result_batch["data"]
                            if new_entries:
                                connector_results += new_entries
                                result_retrieval_offset += RETRIEVAL_BATCH_SIZE
                                if len(new_entries) < RETRIEVAL_BATCH_SIZE:
                                    has_remaining_results = False
                            else:
                                has_remaining_results = False
                        else:
                            stix_shifter_error_msg = (
                                result_batch["error"]
                                if "error" in result_batch
                                else "details not avaliable"
                            )
                            raise DataSourceError(
                                f"STIX-shifter transmission.results() failed with message: {stix_shifter_error_msg}"
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

            stixbundle = translation.translate(
                connector_name,
                "results",
                query_metadata,
                json.dumps(connector_results),
                {},
            )

            with ingestfile.open("w") as ingest:
                json.dump(stixbundle, ingest, indent=4)
            bundles.append(str(ingestfile.resolve()))

        return ReturnFromFile(query_id, bundles)
