import logging
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import yaml
from mashumaro.mixins.json import DataClassJSONMixin

from kestrel.config.utils import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)
from kestrel.mapping.data_model import load_mapping


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
    timestamp_format: str
    data_model_mapping: Optional[str] = None  # Filename for mapping
    data_model_map: Mapping = field(default_factory=dict)

    def __post_init__(self):
        if self.data_model_mapping:
            with open(self.data_model_mapping, "r") as fp:
                self.data_model_map = yaml.safe_load(fp)
        else:
            # Default to the built-in ECS mapping
            self.data_model_map = load_mapping("ecs")


@dataclass
class Config(DataClassJSONMixin):
    connections: Dict[str, Connection]
    indexes: Dict[str, Index]

    def __post_init__(self):
        self.connections = {k: Connection(**v) for k, v in self.connections.items()}
        self.indexes = {k: Index(**v) for k, v in self.indexes.items()}


def load_config():
    return Config(**load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT))
