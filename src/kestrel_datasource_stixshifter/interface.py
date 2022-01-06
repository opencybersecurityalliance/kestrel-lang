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
from functools import lru_cache

import yaml

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

# Create a global dict of cached configurations
# On first invocation, search for YAML file of configurations
# Note the parsing time and cache. On subsequent calls, check stat.ST_MTIME and re-parse if necessary
# ENV variables _override_ the YAML file``


def merge(c1, c2):
    for k in set(c1.keys()).union(set(c2.keys())):
        if k in c1 and k in c2:
            if isinstance(c1[k], dict) and isinstance(c2[k], dict):
                yield (k, dict(merge(c1[k], c2[k])))
            else:
                yield (k, c2[k])
        elif k in c1:
            yield (k, c1[k])
        else:
            yield (k, c2[k])


class StixShifterInterface(AbstractDataSourceInterface):
    __config = None

    @staticmethod
    def init():
        if StixShifterInterface.__config is not None:
            return
        config = dict()
        k_path = os.path.expanduser("~/.kestrel/config.yml")
        if os.path.exists(k_path):
            with open(k_path, "r") as fd:
                cfg = yaml.load(fd, yaml.SafeLoader)
                try:
                    if "stixshifter" in cfg:
                        config = {c["name"].lower(): c for c in cfg["stixshifter"]}
                    for kv in cfg.get("env", []):
                        os.environ[kv["key"]] = kv["value"]
                except:
                    pass
        # Check for environment variable to override the config
        if "KESTREL_CONFIG" in os.environ and os.path.exists(
            os.environ.get("KESTREL_CONFIG")
        ):
            k_path = os.environ.get("KESTREL_CONFIG")
            with open(k_path, "r") as fd:
                cfg = yaml.load(fd, yaml.SafeLoader)
                try:
                    for c in cfg.get("stixshifter", []):
                        pname = c["name"].lower()
                        if pname not in config:
                            config[pname] = c
                        else:
                            # we need to merge
                            config[pname] = dict(merge(config[pname], c))
                    for kv in cfg.get("env", []):
                        os.environ[kv["key"]] = kv["value"]
                except:
                    pass
        # Now look for any ENV variables the override or add new configs
        StixShifterInterface.__config = dict(
            merge(config, StixShifterInterface.__env_parse())
        )

    @staticmethod
    def __env_parse():
        env_vars = os.environ.keys()
        stixshifter_vars = filter(lambda x: x.startswith(ENV_VAR_PREFIX), env_vars)
        config = dict()
        for evar in stixshifter_vars:
            profile = evar.split("_")[1].lower()
            if profile not in config:
                config[profile] = dict()
            # is it a _CONNECTOR, _CONNECTION, or _CONFIG?
            try:
                if evar.lower().endswith("_connector"):
                    config[profile]["connector"] = os.environ[evar]
                elif evar.lower().endswith("_connection"):
                    try:
                        config[profile]["connector"] = json.loads(os.environ[evar])
                    except json.decoder.JSONDecodeError:
                        raise InvalidDataSource(
                            profile,
                            "stixshifter",
                            f"invalid JSON in {evar} environment variable",
                        )
                elif evar.lower().endswith("_config"):
                    try:
                        config[profile]["config"] = json.loads(os.environ[evar])
                    except json.decoder.JSONDecodeError:
                        raise InvalidDataSource(
                            profile,
                            "stixshifter",
                            f"invalid JSON in {evar} environment variable",
                        )
            except:
                pass
        return config

    @staticmethod
    def config():
        return StixShifterInterface.__config

    @staticmethod
    def schemes():
        """STIX Shifter data source interface only supports ``stixshifter://`` scheme."""
        return ["stixshifter"]

    @staticmethod
    @lru_cache(maxsize=1)
    def list_data_sources():
        """Get configured data sources from environment variable profiles."""
        if StixShifterInterface.__config is None:
            StixShifterInterface.init()
        data_sources = list(StixShifterInterface.__config.keys())
        data_sources.sort()
        return data_sources

    @staticmethod
    def query(uri, pattern, session_id=None):
        """Query a stixshifter data source."""
        scheme, _, profile = uri.rpartition("://")
        profiles = profile.split(",")

        if scheme != "stixshifter":
            raise DataSourceManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        ingestdir = mkdtemp()
        query_id = ingestdir.name
        bundles = []
        for i, profile in enumerate(profiles):
            (
                connector_name,
                connection_dict,
                configuration_dict,
            ) = StixShifterInterface._get_stixshifter_config(profile)

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

    @staticmethod
    @lru_cache(maxsize=100)
    def _get_stixshifter_config(profile_name):
        if StixShifterInterface.__config is None:
            StixShifterInterface.init()

        profile_name = profile_name.lower()
        connector_name = StixShifterInterface.__config.get(profile_name, {}).get(
            "connector"
        )
        if not connector_name:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {profile_name} configuration found",
            )
        connector_name = connector_name.lower()

        connection = StixShifterInterface.__config[profile_name].get("connection", None)
        if not connection:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {profile_name} connection configured",
            )

        configuration = StixShifterInterface.__config[profile_name].get("config", None)
        if not configuration:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {profile_name} configuration defined",
            )

        if "host" not in connection:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {profile_name} environment variable: no "host" field',
            )

        if "port" not in connection and connector_name != "stix_bundle":
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {profile_name} environment variable: no "port" field',
            )

        if "auth" not in configuration:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {profile_name} environment variable: no "auth" field',
            )
        return connector_name, connection, configuration
