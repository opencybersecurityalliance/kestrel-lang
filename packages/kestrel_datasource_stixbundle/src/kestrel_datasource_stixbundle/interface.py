"""The STIX bundle data source package provides access to canned data in STIX
bundles locally or remotely.

"""

import json
import logging
import os
import re
import uuid
import pathlib
import shutil
from datetime import datetime, timedelta, timezone
import requests

from stix2matcher.matcher import Pattern

from firepit.woodchipper import convert_to_stix

from firepit.timestamp import to_datetime
from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromFile
from kestrel.exceptions import DataSourceManagerInternalError, DataSourceConnectionError

_logger = logging.getLogger(__name__)


def _make_query_id(uri, pattern):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, str(uri) + pattern))


def _make_query_dir(query_id):
    path = pathlib.Path(query_id)
    path.mkdir(parents=True, exist_ok=False)
    return path


def _make_download_dir():
    path = pathlib.Path("downloads")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _clean_ingestdir_and_raise_error(ingestdir, uri):
    # it is important to clean the directory before raise error
    # otherwise, the next execution will find the dir and assume good data there
    shutil.rmtree(ingestdir)
    raise DataSourceConnectionError(uri)


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
    def query(uri, pattern, session_id=None, config=None, store=None, limit=None):
        """Query a STIX bundle locally or remotely."""

        _logger.debug(f"query URI received at interface_stixbundle: {uri}")

        scheme, _, data_paths = uri.rpartition("://")
        data_paths = data_paths.split(",")
        pattern = fixup_pattern(pattern)
        compiled_pattern = Pattern(pattern)
        query_id = _make_query_id(uri, pattern)
        downloaddir = _make_download_dir()

        try:
            ingestdir = _make_query_dir(query_id)
        except FileExistsError:
            # We already cached this bundle
            data_paths = []

        bundles = []
        num_records = 0
        for i, data_path in enumerate(data_paths):
            _logger.debug(f"requesting data from path: {data_path}")

            if scheme == "file":
                rawfile = data_path
                try:
                    with open(data_path, "r") as f:
                        bundle_in = json.load(f)
                except Exception:
                    _clean_ingestdir_and_raise_error(ingestdir, uri)

            elif scheme == "http" or scheme == "https":
                data_uri = f"{scheme}://{data_path}"
                data_path, extension = os.path.splitext(data_path)
                data_path_stripped = "".join(filter(str.isalnum, data_path))
                rawfile = downloaddir / f"{data_path_stripped}"
                if extension:
                    rawfile = rawfile.with_suffix(f"{extension}")
                last_modified = None
                file_time = None
                if rawfile.exists():
                    _logger.debug("File exists: %s", rawfile)
                    try:
                        resp = requests.head(data_uri)
                    except requests.exceptions.ConnectionError:
                        _clean_ingestdir_and_raise_error(ingestdir, uri)

                    file_time = datetime.fromtimestamp(
                        rawfile.stat().st_mtime, tz=timezone.utc
                    )
                    last_modified = resp.headers.get("Last-Modified")
                    if last_modified:
                        last_modified = to_datetime(last_modified)
                    else:
                        _logger.debug(
                            "HTTP/HTTPS response header does not have 'Last-Modified' field"
                        )
                        last_modified = datetime.now(timezone.utc) - timedelta(
                            minutes=5
                        )
                else:
                    _logger.debug("File not on disk: %s", rawfile)

                if not last_modified or last_modified > file_time:
                    _logger.info("Downloading %s to %s", data_uri, rawfile)
                    try:
                        resp = requests.get(data_uri, stream=True)
                    except requests.exceptions.ConnectionError:
                        _clean_ingestdir_and_raise_error(ingestdir, uri)

                    with rawfile.open("wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    # We already have this file
                    _logger.debug("Using cached file: %s", rawfile)

                try:
                    bundle_in = _get_bundle(rawfile)
                except Exception:
                    _clean_ingestdir_and_raise_error(ingestdir, uri)
            else:
                raise DataSourceManagerInternalError(
                    f"interface {__package__} should not process scheme {scheme}"
                )

            bundle_out = {}
            _logger.debug("Filtering: %s", rawfile)
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
                            matched += 1
                            if obj["type"] == "observed-data":
                                num_records += 1
                                if not limit or num_records <= limit:
                                    bundle_out[prop].append(obj)
                            else:
                                bundle_out[prop].append(obj)
                else:
                    bundle_out[prop] = val
            _logger.debug("Matched %d of %d observations: %s", matched, count, rawfile)

            ingestfile = ingestdir / f"{i}.json"
            with ingestfile.open("w") as f:
                json.dump(bundle_out, f)
            bundles.append(str(ingestfile.expanduser().resolve()))

        return ReturnFromFile(query_id, bundles)


def _get_bundle(rawfile):
    try:
        with open(rawfile, "r") as fp:
            bundle = json.load(fp)
    except (json.decoder.JSONDecodeError, UnicodeDecodeError):
        # It's not JSON.  Maybe firepit can convert it to STIX?
        bundle = convert_to_stix(str(rawfile))
    return bundle
