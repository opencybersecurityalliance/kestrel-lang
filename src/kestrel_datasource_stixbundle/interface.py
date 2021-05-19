import json
import re
import uuid
import pathlib
import requests

from stix2matcher.matcher import match

from kestrel.datasource import AbstractDataSourceInterface
from kestrel.datasource import ReturnFromFile
from kestrel.exceptions import DataSourceManagerInternalError, DataSourceConnectionError


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
        return ["file", "http", "https"]

    @staticmethod
    def list_data_sources():
        """Empty return for now.

        May not be meaningful to implement this for this interface. This method
        should enumerate hosts but the set is unbounded.

        """
        return []

    @staticmethod
    def query(uri, pattern, session_id=None):
        scheme, data_path = uri.split("://")
        pattern = fixup_pattern(pattern)

        ingestdir = _make_query_dir(uri)
        ingestfile = ingestdir / "data.json"

        # TODO: keep files in LRU cache?

        if scheme == "file":
            try:
                with open(data_path, "r") as f:
                    data = f.read()
            except Exception:
                raise DataSourceConnectionError(uri)
        elif scheme == "http" or scheme == "https":
            try:
                data = requests.get(uri)
            except requests.exceptions.ConnectionError:
                raise DataSourceConnectionError(uri)
        else:
            raise DataSourceManagerInternalError(
                f"interface {__package__} should not process scheme {scheme}"
            )

        bundle_in = json.loads(data)
        bundle_out = {}
        for prop, val in bundle_in.items():
            if prop == "objects":
                bundle_out[prop] = []
                for obj in val:
                    if obj["type"] != "observed-data" or match(pattern, [obj], False):
                        bundle_out[prop].append(obj)
            else:
                bundle_out[prop] = val

        with ingestfile.open("w") as f:
            json.dump(bundle_out, f)

        return ReturnFromFile(ingestdir.name, [str(ingestfile.resolve())])
