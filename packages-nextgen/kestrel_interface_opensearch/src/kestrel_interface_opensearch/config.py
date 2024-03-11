import logging
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import yaml
from mashumaro.mixins.json import DataClassJSONMixin

from kestrel.config.utils import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)
from kestrel.mapping.utils import (
    generate_from_ocsf_dictionaries,
    load_standard_config,
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
    timestamp_format: str
    data_model_mapping: Optional[str] = None
    data_model_map: Mapping = field(default_factory=dict)

    def __post_init__(self):
        if self.data_model_mapping:
            with open(self.data_model_mapping, "r") as fp:
                data_model_map = yaml.safe_load(fp)
            # Reverse it so it's ocsf -> native
            self.data_model_map = {
                v: k for k, v in data_model_map.items() if isinstance(v, str)
            }
        else:
            # Default to the built-in ECS mapping
            load_standard_config("kestrel.mapping")
            _, data_model_map = generate_from_ocsf_dictionaries("ecs")
            self.data_model_map = {k: v[0] for k, v in data_model_map.items()}


@dataclass
class Config(DataClassJSONMixin):
    connections: Dict[str, Connection]
    indexes: Dict[str, Index]

    def __post_init__(self):
        self.connections = {k: Connection(**v) for k, v in self.connections.items()}
        self.indexes = {k: Index(**v) for k, v in self.indexes.items()}


def load_config():
    return Config(**load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT))
