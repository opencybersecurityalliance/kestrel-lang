import collections.abc
from importlib import resources
from kestrel.__future__ import is_python_older_than_minor_version
import os
from pathlib import Path
from pkgutil import get_data
from typeguard import typechecked
from typing import Union, Mapping


def load_data_file(package_name, file_name):
    try:
        # resources.files() is introduced in Python 3.9
        content = resources.files(package_name).joinpath(file_name).read_text()
    except AttributeError:
        # Python 3.8; deprecation warning forward
        if is_python_older_than_minor_version(9):
            content = get_data(package_name, file_name).decode("utf-8")

    return content


def list_folder_files(package_name, folder_name, prefix=None, suffix=None):
    try:
        file_paths = resources.files(package_name).joinpath(folder_name).iterdir()
    except AttributeError:
        if is_python_older_than_minor_version(9):
            import pkg_resources

            file_names = pkg_resources.resource_listdir(package_name, folder_name)
            file_paths = [
                Path(
                    pkg_resources.resource_filename(
                        package_name, os.path.join(folder_name, filename)
                    )
                )
                for filename in file_names
            ]
    file_list = (
        f
        for f in file_paths
        if (
            f.is_file()
            and (f.name.endswith(suffix) if suffix else True)
            and (f.name.startswith(prefix) if prefix else True)
        )
    )
    return file_list


@typechecked
def unescape_quoted_string(s: str) -> str:
    if s.startswith("r"):
        return s[2:-1]
    else:
        return s[1:-1].encode("utf-8").decode("unicode_escape")


@typechecked
def update_nested_dict(dict_old: Mapping, dict_new: Union[Mapping, None]):
    if dict_new:
        for k, v in dict_new.items():
            if isinstance(v, collections.abc.Mapping) and k in dict_old:
                dict_old[k] = update_nested_dict(dict_old[k], v)
            else:
                dict_old[k] = v
    return dict_old
