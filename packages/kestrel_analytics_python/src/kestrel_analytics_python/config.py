import logging

from kestrel.config import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)
from kestrel.exceptions import InvalidAnalytics

PROFILE_PATH_DEFAULT = CONFIG_DIR_DEFAULT / "pythonanalytics.yaml"
PROFILE_PATH_ENV_VAR = "KESTREL_PYTHON_ANALYTICS_CONFIG"

_logger = logging.getLogger(__name__)


def load_profiles():
    config = load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT)
    if config and "profiles" in config:
        _logger.debug(f"python analytics profiles found in config file")
        profiles = config["profiles"]
    else:
        _logger.info("no python analytics config with profiles found")
        profiles = {}
    _logger.debug(f"profiles loaded: {profiles}")
    return profiles


def get_profile(profile_name, profiles):
    if profile_name not in profiles:
        raise InvalidAnalytics(
            profile_name,
            "python",
            f"no {profile_name} configuration found",
        )
    else:
        profile = profiles[profile_name]
        _logger.debug(f"profile to use: {profile}")
        if "module" not in profile:
            raise InvalidAnalytics(
                profile_name,
                "python",
                f"no {profile_name} module defined",
            )
        else:
            module_name = profile["module"]
        if "func" not in profile:
            raise InvalidAnalytics(
                profile_name,
                "python",
                f"no {profile_name} func defined",
            )
        else:
            func_name = profile["func"]

    return module_name, func_name
