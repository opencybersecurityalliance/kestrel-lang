import pytest

from kestrel.session import Session
from kestrel.codegen import prefetch

from .utils import set_empty_kestrel_config, set_no_prefetch_kestrel_config


def test_default_prefetch_config(set_empty_kestrel_config):
    with Session() as s:
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "get", "process"
            )
            == True
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "file"
            )
            == True
        )


def test_prefetch_disabled_config(set_no_prefetch_kestrel_config):
    with Session() as s:
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "get", "process"
            )
            == False
        )
        assert (
            prefetch._is_prefetch_allowed_in_config(
                s.config["prefetch"], "find", "file"
            )
            == False
        )
