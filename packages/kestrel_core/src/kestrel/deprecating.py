from pkgutil import get_data
from importlib import resources

def load_data_file(package_name, file_name):
    try:
        # resources.files() is introduced in Python 3.9
        default_config = resources.files(package_name).joinpath(file_name).read_text()
    except AttributeError:
        # Python 3.8; deprecation warning forward
        default_config = get_data(package_name, file_name)

    return default_config
