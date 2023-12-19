from importlib import resources
from kestrel.exceptions import MappingParseError
from kestrel.utils import load_data_file
import os
from typeguard import typechecked
from typing import (
    Iterable,
    Union,
)
import yaml


# _entityname_mapping and _entityattr_mapping are dictionaries that contain
# the info needed to translate:
#   a. queries between:
#      1. STIX and OCSF
#      2. ECS and OCSF
#      3. OCSF and ECS
#   b. results between:
#      1. ECS and OCSF
_entityname_mapping = {}
_entityattr_mapping = {}


@typechecked
def load_standard_config(mapping_pkg: str):
    global _entityname_mapping
    global entityattr_mapping
    if (len(_entityname_mapping) > 0 and len(_entityattr_mapping) > 0):
        return
    entityname_maps = resources.files(mapping_pkg).joinpath("entityname")
    entityname_mapping_files = (f for f in entityname_maps.iterdir()
                                if f.is_file() and f.name.endswith(".yaml"))
    for f in entityname_mapping_files:
        parse_entityname_mapping_file(mapping_pkg, f.name)
    entityattr_maps = resources.files(mapping_pkg).joinpath("entityattribute")
    entityattr_mapping_files = (f for f in entityattr_maps.iterdir()
                                if f.is_file() and f.name.endswith(".yaml"))
    for f in entityattr_mapping_files:
        parse_entityattr_mapping_file(mapping_pkg, f.name)


@typechecked
def parse_entityname_mapping_file(mapping_pkg: str, filename: str):
    global _entityname_mapping
    mapping_fpath = os.path.join("entityname", filename)
    filename_no_ext, _ = filename.split(".")
    if filename_no_ext.startswith("to_"):
        src_lang = 'ocsf'
        dst_lang = filename_no_ext[3: ]
    else:
        src_lang = "stix" if filename_no_ext == "alias" else filename_no_ext
        dst_lang = "ocsf"
    src_dict = _entityname_mapping.get(src_lang, {})
    dst_dict = src_dict.get(dst_lang, {})
    try:
        mapping_str = load_data_file(mapping_pkg, mapping_fpath)
        mapping = yaml.safe_load(mapping_str)
        dst_dict.update(mapping)
    except Exception as ex:
        raise MappingParseError()
    src_dict[dst_lang] = dst_dict
    _entityname_mapping[src_lang] = src_dict


@typechecked
def expand_referenced_field(mapping: dict, key: str, value: dict) -> dict:
    res = {}
    ref = value.get("ref")
    prefix = value.get("prefix")
    for k, v in mapping.items():
        if k.startswith(f"{ref}."):
            k_no_ref = k[len(ref) + 1: ]
            ref_key = ".".join([key, k_no_ref])
            if prefix is None:
                ref_value = v
            else:
                prefix_tokens = prefix.split(".")
                v_tokens = v.split(".")
                i = 0
                len_prefix_tokens = len(prefix_tokens)
                len_v_tokens = len(v_tokens)
                max_len = (len_prefix_tokens if len_prefix_tokens < len_v_tokens
                           else len_v_tokens)
                while i < max_len:
                    if (prefix_tokens[-1 - i].startswith("-") and
                        prefix_tokens[-1 - i][1: ] == v_tokens[i]):
                        i += 1
                    else:
                        break
                ref_value = ".".join(prefix_tokens[: len_prefix_tokens - i] +
                                     v_tokens[i: ])
            res[ref_key] = ref_value
    return res


@typechecked
def parse_entityattr_mapping_file(mapping_pkg: str, filename: str):
    global _entityattr_mapping
    mapping_fpath = os.path.join("entityattribute", filename)
    filename_no_ext, _ = filename.split(".")
    if filename_no_ext.startswith("to_"):
        src_lang = 'ocsf'
        dst_lang = filename_no_ext[3: ]
    else:
        src_lang = "stix" if filename_no_ext == "alias" else filename_no_ext
        dst_lang = "ocsf"
    src_dict = _entityattr_mapping.get(src_lang, {})
    dst_dict = src_dict.get(dst_lang, {})
    try:
        mapping_str = load_data_file(mapping_pkg, mapping_fpath)
        mapping = yaml.safe_load(mapping_str)
        mapping_referenced_fields = mapping.pop("referenced_fields", {})
        expanded_refs = {}
        for key, value in mapping_referenced_fields.items():
            expanded_ref = expand_referenced_field(mapping, key, value)
            expanded_refs.update(expanded_ref)
        mapping.update(expanded_refs)
        dst_dict.update(mapping)
    except Exception as ex:
        raise MappingParseError()
    src_dict[dst_lang] = dst_dict
    _entityattr_mapping[src_lang] = src_dict


def load_custom_config():
    # ~/.config/kestrel/mapping/entity/*.yaml
    # ~/.config/kestrel/mapping/property/*.yaml
    return


def normalize_entity():
    return


def normalize_property():
    return


@typechecked
def translate_entityname(entityname: str, src_lang: str, dst_lang: str) -> Union[str, Iterable[str]]:
    return _entityname_mapping.get(src_lang, {}).get(dst_lang, {}).get(entityname, entityname)


@typechecked
def translate_entityattr(entityattr: str, src_lang: str, dst_lang: str) -> Union[str, Iterable[str]]:
    return _entityattr_mapping.get(src_lang, {}).get(dst_lang, {}).get(entityattr, entityattr)