"""The STIX bundle data source package provides access to canned data in STIX
bundles locally or remotely.

"""

import json
import logging
import re
import uuid
import pathlib
from datetime import datetime, timezone
from dateutil import parser
import requests

from stix2matcher.matcher import Pattern

from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromFile
from kestrel.exceptions import DataSourceManagerInternalError, DataSourceConnectionError

_logger = logging.getLogger(__name__)


def _make_query_dir(uri):
    path = pathlib.Path(str(uuid.uuid5(uuid.NAMESPACE_URL, str(uri))))
    path.mkdir(parents=True, exist_ok=True)
    return path


def fixup_pattern(pattern):
    # The matcher doesn't accept TimestampLiterals in START/STOP
    # See https://github.com/oasis-open/cti-pattern-validator/issues/52
    return re.sub(r"(START|STOP)\s+t'", r"\1 '", pattern)


class StixBundleInterface(AbstractDataSourceInterface):
    @staticmethod
    def schemes():
        """STIX bundle data source interface supporting ``file:///``, ``http://``, ``https://`` scheme."""
        return ["file", "http", "https"]

    @staticmethod
    def list_data_sources(config=None):
        """This interface does not list data sources."""
        return []

    @staticmethod
    def query(uri, pattern, session_id=None, config=None):
        """Query a STIX bundle locally or remotely."""
        scheme, _, data_paths = uri.rpartition("://")
        data_paths = data_paths.split(",")
        pattern = fixup_pattern(pattern)
        compiled_pattern = Pattern(pattern)

        ingestdir = _make_query_dir(uri)
        bundles = []
        for i, data_path in enumerate(data_paths):
            data_path_striped = "".join(filter(str.isalnum, data_path))
            bundlefile = ingestdir / f"{data_path_striped}.json"
            ingestfile = ingestdir / f"{i}.json"

            if scheme == "file":
                try:
                    with open(data_path, "r") as f:
                        bundle_in = json.load(f)
                except Exception:
                    raise DataSourceConnectionError(uri)
            elif scheme == "http" or scheme == "https":
                data_uri = f"{scheme}://{data_path}"
                last_modified = None
                file_time = None
                if bundlefile.exists():
                    _logger.debug("File exists: %s", bundlefile)
                    try:
                        resp = requests.head(data_uri)
                    except requests.exceptions.ConnectionError:
                        raise DataSourceConnectionError(uri)
                    last_modified = resp.headers.get("Last-Modified")
                    if last_modified:
                        last_modified = parser.parse(last_modified)
                        file_time = datetime.fromtimestamp(
                            bundlefile.stat().st_mtime, tz=timezone.utc
                        )
                    else:
                        _logger.debug(
                            "HTTP/HTTPS response header does not have 'Last-Modified' field"
                        )
                else:
                    _logger.debug("Bundle not on disk: %s", bundlefile)

                if not last_modified or last_modified > file_time:
                    _logger.info("Downloading %s to %s", data_uri, bundlefile)
                    try:
                        bundle_in = requests.get(data_uri).json()
                    except requests.exceptions.ConnectionError:
                        raise DataSourceConnectionError(uri)
                    with bundlefile.open("w") as f:
                        json.dump(bundle_in, f)
                else:
                    # We already have this file
                    _logger.debug("Using cached bundle: %s", bundlefile)
                    try:
                        with open(bundlefile, "r") as f:
                            bundle_in = json.load(f)
                    except Exception:
                        raise DataSourceConnectionError(uri)
            else:
                raise DataSourceManagerInternalError(
                    f"interface {__package__} should not process scheme {scheme}"
                )

            bundle_out = {}
            _logger.debug("Filtering: %s", bundlefile)
            count = 0
            matched = 0
            for prop, val in bundle_in.items():
                if prop == "objects":
                    bundle_out[prop] = []
                    for obj in val:
                        count += 1
                        if obj["type"] != "observed-data" or compiled_pattern.match(
                            [obj], False
                        ):
                            bundle_out[prop].append(obj)
                            matched += 1
                else:
                    bundle_out[prop] = val
            _logger.debug(
                "Matched %d of %d observations: %s", matched, count, bundlefile
            )

            with ingestfile.open("w") as f:
                json.dump(bundle_out, f)
            bundles.append(str(ingestfile.expanduser().resolve()))

        return ReturnFromFile(ingestdir.name, bundles)
