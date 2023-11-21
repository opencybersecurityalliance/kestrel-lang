from pkgutil import get_data
from importlib import resources


def load_data_file(package_name, file_name):
    try:
        # resources.files() is introduced in Python 3.9
        content = resources.files(package_name).joinpath(file_name).read_text()
    except AttributeError:
        # Python 3.8; deprecation warning forward
        content = get_data(package_name, file_name).decode("utf-8")

    return content
