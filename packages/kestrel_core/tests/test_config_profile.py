import os
import pytest

import kestrel
from kestrel.session import Session
from kestrel.codegen import prefetch

from .utils import set_empty_kestrel_config, set_no_prefetch_kestrel_config


def test_default_prefetch_config(set_empty_kestrel_config):
    with Session() as s:
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "get", "ipv4-addr"
            )
            == True
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "network-traffic"
            )
            == True
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "process"
            )
            == True
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "file"
            )
            == False
        )


def test_prefetch_disabled_config(set_no_prefetch_kestrel_config):
    with Session() as s:
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "get", "ipv4-addr"
            )
            == False
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "network-traffic"
            )
            == False
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "process"
            )
            == False
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "file"
            )
            == False
        )


def test_env_var_resolve(tmp_path):
    os.chdir(tmp_path)
    config_name = "abc.yaml"
    with open(config_name, "w") as config:
        config.write(r"""
language:
  default_variable: "_"
""")
    os.environ[kestrel.config.CONFIG_PATH_ENV_VAR] = config_name
    s = Session()
    full_path = os.path.join(os.getcwd(), config_name)
    assert os.environ[kestrel.config.CONFIG_PATH_ENV_VAR] == full_path 
