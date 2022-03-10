"""The STIX-shifter data source package provides access to data sources via
`stix-shifter`_.

The STIX-shifter interface can reach multiple data sources. The user needs to
provide one *profile* per data source. The profile name (case insensitive) will
be used in the ``FROM`` clause of the Kestrel ``GET`` command, e.g., ``newvar =
GET entity-type FROM stixshifter://profilename WHERE ...``. Kestrel runtime
will load profiles from 3 places (the later will override the former):

#. STIX-shifter interface config file (only when a Kestrel session starts):

    Put your profiles in the STIX-shifter interface config file (YAML):

    - Default path: ``~/.config/kestrel/stixshifter.yaml``.
    - A customized path specified in the environment variable ``KESTREL_STIXSHIFTER_CONFIG``.

    Example of STIX-shifter interface config file containing profiles:

    .. code-block:: yaml

        profiles:
            host101:
                connector: elastic_ecs
                connection:
                    host: elastic.securitylog.company.com
                    port: 9200
                    selfSignedCert: false # this means do NOT check cert
                    indices: host101
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

"""

import sys
import json
import time
import copy
import logging
import importlib
import subprocess
import requests
from lxml import html

from stix_shifter.stix_translation import stix_translation
from stix_shifter.stix_transmission import stix_transmission

from kestrel.utils import mkdtemp
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromFile
from kestrel.exceptions import DataSourceError, DataSourceManagerInternalError
from kestrel_datasource_stixshifter.config import (
    RETRIEVAL_BATCH_SIZE,
    get_datasource_from_profiles,
    load_profiles,
    set_stixshifter_logging_level,
)

_logger = logging.getLogger(__name__)


XPATH_PYPI_PKG_HOME = "/html/body/main/div[4]/div/div/div[1]/div[2]/ul/li[1]/a/@href"
XPATH_PYPI_PKG_SOURCE = "/html/body/main/div[4]/div/div/div[1]/div[2]/ul/li[2]/a/@href"
STIX_SHIFTER_HOMEPAGE = "https://github.com/opencybersecurityalliance/stix-shifter"


def get_package_name(connector_name):
    return "stix-shifter-modules-" + connector_name.replace("_", "-")


def verify_package_origin(connector_name):
    _logger.debug("go to PyPI to verify package genuineness from STIX-shifter project")
    package_name = get_package_name(connector_name)

    try:
        pypi_response = requests.get(f"https://pypi.org/project/{package_name}")
        pypi_etree = html.fromstring(pypi_response.content)
    except:
        raise DataSourceError(
            f'STIX-shifter connector for "{connector_name}" is not installed '
            f'and Kestrel guessed Python package name "{package_name}" but failed to locate it at PyPI',
            "please manually install the correct STIX-shifter connector Python package.",
        )

    try:
        p_homepage = pypi_etree.xpath(XPATH_PYPI_PKG_HOME)[0]
        p_source = pypi_etree.xpath(XPATH_PYPI_PKG_SOURCE)[0]
    except:
        raise DataSourceError(
            f'STIX-shifter connector for "{connector_name}" is not installed '
            f'and Kestrel guessed Python package name "{package_name}" but could not verify its genuineness due to PyPI design change',
            "please find the correct STIX-shifter connector Python package to install. "
            "And report to Kestrel developers about this package verification failure",
        )

    if p_homepage != STIX_SHIFTER_HOMEPAGE or p_source != STIX_SHIFTER_HOMEPAGE:
        raise DataSourceError(
            f'STIX-shifter connector for "{connector_name}" is not installed '
            f'and Kestrel found Python package "{package_name}" is not a genuine STIX-shifter package',
            "please find the correct STIX-shifter connector Python package to install. "
            f"And report to Kestrel developers about this malicious package",
        )

    _logger.info(f'"{package_name}" verified as a STIX-shifter package.')


def check_module_availability(connector_name):
    try:
        importlib.import_module(
            "stix_shifter_modules." + connector_name + ".entry_point"
        )
    except:
        _logger.info(f'miss STIX-shifter connector "{connector_name}"')

        package_name = get_package_name(connector_name)
        _logger.debug(f"guess the connector package name: {package_name}")

        verify_package_origin(connector_name)

        _logger.info(f'install Python package "{package_name}".')
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name]
            )
        except:
            _logger.info("package installation with 'pip' failed.")

        try:
            importlib.import_module(
                "stix_shifter_modules." + connector_name + ".entry_point"
            )
        except:
            raise DataSourceError(
                f'STIX-shifter connector for "{connector_name}" is not installed '
                f'and Kestrel failed to install the possible Python package "{package_name}"',
                "please manually install the corresponding STIX-shifter connector Python package.",
            )


class StixShifterInterface(AbstractDataSourceInterface):
    @staticmethod
    def schemes():
        """STIX-shifter data source interface only supports ``stixshifter://`` scheme."""
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
            raise DataSourceManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        set_stixshifter_logging_level()

        ingestdir = mkdtemp()
        query_id = ingestdir.name
        bundles = []
        _logger.debug(f"prepare query with ID: {query_id}")
        for i, profile in enumerate(profiles):
            # STIX-shifter will alter the config objects, thus making them not reusable.
            # So only give STIX-shifter a copy of the configs.
            # Check `modernize` functions in the `stix_shifter_utils` for details.
            (connector_name, connection_dict, configuration_dict,) = map(
                copy.deepcopy, get_datasource_from_profiles(profile, config["profiles"])
            )

            check_module_availability(connector_name)

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

            _logger.debug(f"STIX pattern to query: {pattern}")
            _logger.debug(f"translate results: {dsl}")

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

            _logger.debug("transmission succeeded, start translate back to STIX")

            stixbundle = translation.translate(
                connector_name,
                "results",
                query_metadata,
                json.dumps(connector_results),
                {},
            )

            _logger.debug(f"dumping STIX bundles into file: {ingestfile}")
            with ingestfile.open("w") as ingest:
                json.dump(stixbundle, ingest, indent=4)
            bundles.append(str(ingestfile.expanduser().resolve()))

        return ReturnFromFile(query_id, bundles)
