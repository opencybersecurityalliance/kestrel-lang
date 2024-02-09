import os

import yaml

from kestrel_datasource_opensearch.config import (
    PROFILE_PATH_ENV_VAR,
    Connection,
    load_config,
)


def test_load_config(tmp_path):
    config = {
        "connections": {
            "localhost": {
                "url": "https://localhost:9200",
                "verify_certs": False,
                "auth": {
                    "username": "admin",
                    "password": "admin",
                }
            },
            "some-cloud-thing": {
                "url": "https://www.example.com:9200",
                "verify_certs": True,
                "auth": {
                    "username": "hunter",
                    "password": "super_secret",
                }
            }
        },
        "indexes": {
            "some_index": {
                "connection": "some-cloud-thing",
                "timestamp": "@timestamp",
                "timestamp_format": "%Y-%m-%d %H:%M:%S.%f"
            }
        }
    }
    config_file = tmp_path / "opensearch.yaml"
    with open(config_file, 'w') as fp:
        yaml.dump(config, fp)
    os.environ[PROFILE_PATH_ENV_VAR] = str(config_file)
    read_config = load_config()
    conn: Connection = read_config.connections["localhost"]
    assert conn.url == config["connections"]["localhost"]["url"]
    assert read_config.connections["localhost"].url == config["connections"]["localhost"]["url"]
    assert read_config.indexes["some_index"].timestamp == config["indexes"]["some_index"]["timestamp"]
