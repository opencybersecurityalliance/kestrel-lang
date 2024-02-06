import logging

from kestrel.config.utils import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)

PROFILE_PATH_DEFAULT = CONFIG_DIR_DEFAULT / "opensearch.yaml"
PROFILE_PATH_ENV_VAR = "KESTREL_OPENSEARCH_CONFIG"

_logger = logging.getLogger(__name__)


def load_config():
    return load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT)
