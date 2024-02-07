import logging
from dataclasses import dataclass
from typing import Dict

from mashumaro.mixins.json import DataClassJSONMixin

from kestrel.config.utils import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)

PROFILE_PATH_DEFAULT = CONFIG_DIR_DEFAULT / "opensearch.yaml"
PROFILE_PATH_ENV_VAR = "KESTREL_OPENSEARCH_CONFIG"

_logger = logging.getLogger(__name__)


@dataclass
class Auth:
    username: str
    password: str


@dataclass
class Connection(DataClassJSONMixin):
    url: str
    auth: Auth
    verify_certs: bool = True

    def __post_init__(self):
        self.auth = Auth(**self.auth)


@dataclass
class Index(DataClassJSONMixin):
    connection: str
    timestamp: str


@dataclass
class Config(DataClassJSONMixin):
    connections: Dict[str, Connection]
    indexes: Dict[str, Index]

    def __post_init__(self):
        self.connections = {k: Connection(**v) for k, v in self.connections.items()}
        self.indexes = {k: Index(**v) for k, v in self.indexes.items()}


def load_config():
    return Config(**load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT))
