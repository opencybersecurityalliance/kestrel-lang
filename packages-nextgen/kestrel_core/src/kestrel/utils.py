import os
from pathlib import Path
import pkg_resources
from pkgutil import get_data
from importlib import resources
from typeguard import typechecked
import pkgutil

def load_data_file(package_name, file_name):
    try:
        # resources.files() is introduced in Python 3.9
        content = resources.files(package_name).joinpath(file_name).read_text()
    except AttributeError:
        # Python 3.8; deprecation warning forward
        content = get_data(package_name, file_name).decode("utf-8")

    return content


def list_folder_files(package_name, folder_name, prefix=None, suffix=None):
    try:
        file_paths = resources.files(package_name).joinpath(folder_name).iterdir()
    except AttributeError:
        file_names = pkg_resources.resource_listdir(package_name, folder_name)
        file_paths = [
            Path(pkg_resources.resource_filename(
                package_name, os.path.join(folder_name, filename)))
                for filename in file_names
        ]
    file_list = (f for f in file_paths if (
        f.is_file() and
        (f.name.endswith(suffix) if suffix else True) and
        (f.name.startswith(prefix) if prefix else True)))
    return file_list


@typechecked
def unescape_quoted_string(s: str) -> str:
    if s.startswith("r"):
        return s[2:-1]
    else:
        return s[1:-1].encode("utf-8").decode("unicode_escape")
