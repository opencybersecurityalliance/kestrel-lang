import os
import yaml
import pathlib
import pkgutil
import logging

from kestrel.utils import update_nested_dict

CONFIG_DIR_DEFAULT = pathlib.Path.home() / ".config" / "kestrel"
CONFIG_PATH_DEFAULT = CONFIG_DIR_DEFAULT / "kestrel.yaml"
CONFIG_PATH_ENV_VAR = "KESTREL_CONFIG"  # override CONFIG_PATH_DEFAULT if provided

_logger = logging.getLogger(__name__)


def load_default_config():
    _logger.debug(f"Loading default config file...")
    return yaml.safe_load(pkgutil.get_data(__name__, "config.yaml"))


def load_user_config(config_path_env_var, config_path_default):
    config_path = os.getenv(config_path_env_var, config_path_default)
    config_path = os.path.expanduser(config_path)
    config = {}
    if config_path:
        try:
            with open(config_path, "r") as fp:
                _logger.debug(f"User configuration file found: {config_path}")
                config = yaml.safe_load(fp)
        except FileNotFoundError:
            _logger.debug(f"User configuration file not exist.")
    return config


def load_config():
    config_default = load_default_config()
    config_user = load_user_config(CONFIG_PATH_ENV_VAR, CONFIG_PATH_DEFAULT)
    _logger.debug(f"User configuration loaded: {config_user}")
    _logger.debug(f"Updating default config with user config...")
    return update_nested_dict(config_default, config_user)
