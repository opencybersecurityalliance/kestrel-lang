import os

from kestrel.config import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)
from kestrel.utils import update_nested_dict
from kestrel.exceptions import InvalidConfiguration, InvalidDataSource

PROFILE_PATH_DEFAULT = CONFIG_DIR_DEFAULT / "stixshifter.yaml"
PROFILE_PATH_ENV_VAR = "KESTREL_STIXSHIFTER_CONFIG"
ENV_VAR_PREFIX = "STIXSHIFTER_"
RETRIEVAL_BATCH_SIZE = 512


def load_profiles_from_env_var():
    env_vars = os.environ.keys()
    stixshifter_vars = filter(lambda x: x.startswith(ENV_VAR_PREFIX), env_vars)
    profiles = {}
    for evar in stixshifter_vars:
        items = evar.lower().split("_")
        suffix = items[-1]
        profile = "_".join(items[1:-1])
        if profile not in profiles:
            profiles[profile] = {}

        # decoding JSON or string values from environment variables
        if suffix == "connection" or suffix == "config":
            try:
                value = json.loads(os.environ[evar])
            except json.decoder.JSONDecodeError:
                raise InvalidDataSource(
                    profile,
                    "stixshifter",
                    f"invalid JSON in {evar} environment variable",
                )
        else:
            value = os.environ[evar]

        profiles[profile][suffix] = value

    return profiles


def get_datasource_from_profiles(profile_name, profiles):
    """Validate profile data

    Validate profile data. The data should be a dict with "connector",
    "connection", "config" keys, and appropriate values.

    Args:
        profile_name (str): The name of the profile.
        profiles (dict): name to profile (dict) mapping.

    Returns:
        Bool
    """
    if profile_name not in profiles:
        raise InvalidDataSource(
            profile_name,
            "stixshifter",
            f"no {profile_name} configuration found",
        )
    else:
        profile = profiles[profile_name]
        if "connector" not in profile:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {profile_name} connector defined",
            )
        else:
            connector_name = profile["connector"]
        if "conneciton" not in profile:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {profile_name} connection defined",
            )
        else:
            connection = profile["connection"]
        if "config" not in profile:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f"no {profile_name} configuration defined",
            )
        else:
            configuration = profile["config"]
        if "host" not in connection:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {profile_name} connection section: no "host" field',
            )

        if "port" not in connection and connector_name != "stix_bundle":
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {profile_name} connection section: no "port" field',
            )

        if "auth" not in configuration:
            raise InvalidDataSource(
                profile_name,
                "stixshifter",
                f'invalid {profile_name} configuration section: no "auth" field',
            )
    return connector_name, connection, configuration


def load_profiles():
    config = load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT)
    if "profiles" not in config:
        raise InvalidConfiguration(
            'stix-shifter config file error that "profiles" is not found as a root-level key',
            "check stix-shifter config file",
        )
    profiles_from_file = config["profiles"]
    profiles_from_env_var = load_profiles_from_env_var()
    profiles = update_nested_dict(profiles_from_file, profiles_from_env_var)
    return profiles
