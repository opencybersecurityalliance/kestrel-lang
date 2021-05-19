"""STIX Shifter data source package provides access to data sources via
stix-shifter.

Before use, need to install the target stix-shifter connector packages such as
``stix-shifter-modules-carbonblack``.

The STIX Shifter interface can reach multiple data sources. The user needs to
setup one *profile* per data source. The profile name will be used in the
``FROM`` clause of the Kestrel ``GET`` command, e.g., ``newvar = GET entity-type
FROM stixshifter://profilename WHERE ...``. Kestrel runtime will load the profile
for the used profile from environment variables:

- ``STIXSHIFTER_PROFILENAME_CONNECTOR``: the STIX Shifter connector name, e.g., ``elastic_ecs``.
- ``STIXSHIFTER_PROFILENAME_CONNECTION``: the STIX Shifter `connection <https://github.com/opencybersecurityalliance/stix-shifter/blob/master/OVERVIEW.md#connection>`_ object in JSON string.
- ``STIXSHIFTER_PROFILENAME_CONFIG``: the STIX Shifter `configuration <https://github.com/opencybersecurityalliance/stix-shifter/blob/master/OVERVIEW.md#configuration>`_ object in JSON string.

Properties of profile name:

- Not case sensitive, e.g., ``profileX`` in the Kestrel command will match
  ``STIXSHIFTER_PROFILEX_...`` in environment variables.
- Cannot contain ``_``.

"""

import os
import json
import time

from stix_shifter.stix_translation import stix_translation
from stix_shifter.stix_transmission import stix_transmission

from kestrel.utils import mkdtemp
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromFile
from kestrel.exceptions import (
    InvalidDataSource,
    DataSourceError,
    DataSourceManagerInternalError,
)

from kestrel_datasource_stixshifter.config import ENV_VAR_PREFIX, RETRIEVAL_BATCH_SIZE


class StixShifterInterface(AbstractDataSourceInterface):
    @staticmethod
    def schemes():
        """STIX Shifter data source interface only supports ``stixshifter://`` scheme."""
        return ["stixshifter"]

    @staticmethod
    def list_data_sources():
        """Get configured data sources from environment variable profiles."""
        data_sources = []

        env_vars = os.environ.keys()
        stixshifter_vars = filter(lambda x: x.startswith(ENV_VAR_PREFIX), env_vars)
        for evar in stixshifter_vars:
            profile = evar.split("_")[1].lower()
            if profile not in data_sources:
                data_sources.append(profile)

        data_sources.sort()

        return data_sources

    @staticmethod
    def query(uri, pattern, session_id=None):
        """Query a stixshifter data source."""
        scheme, profile = uri.split("://")

        if scheme != "stixshifter":
            raise DataSourceManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        (
            connector_name,
            connection_dict,
            configuration_dict,
        ) = StixShifterInterface._get_stixshifter_config(profile)

        ingestdir = mkdtemp()
        ingestfile = ingestdir / "data.json"

        query_id = ingestdir.name
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
            raise DataSourceError("STIX-shifter translation failed")

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
                            status["progress"] < 100 and status["status"] == "RUNNING"
                        ):
                            status = transmission.status(search_id)
                    else:
                        raise DataSourceError(
                            "STIX-shifter transmission.status() failed"
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
                        raise DataSourceError(
                            "STIX-shifter transmission.results() failed"
                        )

            else:
                raise DataSourceError("STIX-shifter transmission.query() failed")

        stixbundle = translation.translate(
            connector_name, "results", query_metadata, json.dumps(connector_results), {}
        )

        with ingestfile.open("w") as ingest:
            json.dump(stixbundle, ingest, indent=4)

        return ReturnFromFile(query_id, [str(ingestfile.resolve())])

    @staticmethod
    def _get_stixshifter_config(profile_name):
        profile_name = profile_name.upper()

        env_conr_name = f"{ENV_VAR_PREFIX}{profile_name}_CONNECTOR"
        connector_name = os.getenv(env_conr_name)
        if not connector_name:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {env_conr_name} environment variable found",
            )
        connector_name = connector_name.lower()

        env_conn_name = f"{ENV_VAR_PREFIX}{profile_name}_CONNECTION"
        connection = os.getenv(env_conn_name)
        if not connection:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {env_conn_name} environment variable found",
            )

        env_conf_name = f"{ENV_VAR_PREFIX}{profile_name}_CONFIG"
        configuration = os.getenv(env_conf_name)
        if not configuration:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {env_conf_name} environment variable found",
            )

        try:
            connection = json.loads(connection)
        except json.decoder.JSONDecodeError:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"invalid JSON in {env_conn_name} environment variable",
            )

        if "host" not in connection:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {env_conn_name} environment variable: no "host" field',
            )

        if "port" not in connection:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {env_conn_name} environment variable: no "port" field',
            )

        try:
            configuration = json.loads(configuration)
        except json.decoder.JSONDecodeError:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"invalid JSON in {env_conf_name} environment variable",
            )

        if "auth" not in configuration:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {env_conf_name} environment variable: no "auth" field',
            )

        return connector_name, connection, configuration
