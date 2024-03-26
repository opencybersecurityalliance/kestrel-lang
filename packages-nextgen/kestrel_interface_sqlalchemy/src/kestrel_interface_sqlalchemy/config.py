import logging
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import yaml
from mashumaro.mixins.json import DataClassJSONMixin

from kestrel.config.utils import (
    CONFIG_DIR_DEFAULT,
    load_user_config,
)
from kestrel.exceptions import InterfaceNotConfigured
from kestrel.mapping.data_model import load_mapping


PROFILE_PATH_DEFAULT = CONFIG_DIR_DEFAULT / "sqlalchemy.yaml"
PROFILE_PATH_ENV_VAR = "KESTREL_SQLALCHEMY_CONFIG"

_logger = logging.getLogger(__name__)


@dataclass
class Connection(DataClassJSONMixin):
    url: str  # SQLAlchemy "connection URL" or "connection string"


@dataclass
class Table(DataClassJSONMixin):
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
            self.data_model_map = load_mapping("ecs")  # FIXME: need a default?


@dataclass
class Config(DataClassJSONMixin):
    connections: Dict[str, Connection]
    tables: Dict[str, Table]

    def __post_init__(self):
        self.connections = {k: Connection(**v) for k, v in self.connections.items()}
        self.tables = {k: Table(**v) for k, v in self.tables.items()}


def load_config():
    try:
        return Config(**load_user_config(PROFILE_PATH_ENV_VAR, PROFILE_PATH_DEFAULT))
    except TypeError:
        raise InterfaceNotConfigured()
