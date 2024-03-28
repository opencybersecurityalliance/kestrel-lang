import logging
import os
from typing import (
    Iterable,
    Union,
)

from typeguard import typechecked
import yaml

from kestrel.exceptions import MappingParseError
from kestrel.utils import load_data_file, list_folder_files


_logger = logging.getLogger(__name__)


# _entityname_mapping is dictionaries that contain
# the info needed to translate:
#   a. queries between:
#      1. STIX and OCSF
#      2. ECS and OCSF
#      3. OCSF and ECS
#   b. results between:
#      1. ECS and OCSF
_entityname_mapping = {}


@typechecked
def load_standard_config(mapping_pkg: str):
    global _entityname_mapping
    if len(_entityname_mapping) > 0:
        return
    entityname_mapping_files = list_folder_files(
        mapping_pkg, "entityname", suffix=".yaml"
    )
    for f in entityname_mapping_files:
        parse_entityname_mapping_file(mapping_pkg, f.name)


@typechecked
def parse_entityname_mapping_file(mapping_pkg: str, filename: str):
    global _entityname_mapping
    mapping_fpath = os.path.join("entityname", filename)
    filename_no_ext, _ = filename.split(".")
    src_lang = "stix" if filename_no_ext == "alias" else filename_no_ext
    dst_lang = "ocsf"
    src_dict = _entityname_mapping.get(src_lang, {})
    dst_dict = src_dict.get(dst_lang, {})
    try:
        mapping_str = load_data_file(mapping_pkg, mapping_fpath)
        mapping = yaml.safe_load(mapping_str)
        dst_dict.update(mapping)
    except Exception as ex:
        raise MappingParseError() from ex
    src_dict[dst_lang] = dst_dict
    _entityname_mapping[src_lang] = src_dict


def load_custom_config():
    # ~/.config/kestrel/mapping/entity/*.yaml
    # ~/.config/kestrel/mapping/property/*.yaml
    return


@typechecked
def normalize_entity(
    entityname: str, src_lang: str, dst_lang: str
) -> Union[str, Iterable[str]]:
    return (
        _entityname_mapping.get(src_lang, {})
        .get(dst_lang, {})
        .get(entityname, entityname)
    )
